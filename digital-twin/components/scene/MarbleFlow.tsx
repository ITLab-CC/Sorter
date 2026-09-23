"use client";

/**
 * Visual marble flow. This is deliberately not a physics simulation: marbles
 * follow scripted waypoints (tube exit -> funnel -> camera -> gate -> cup),
 * driven by the `release` / `detection` events of the twin.
 */
import { useFrame } from "@react-three/fiber";
import { useEffect, useMemo, useRef } from "react";
import * as THREE from "three";
import { CUP_X, DROP, MARBLE_RADIUS, TRANSPORT_PATH, type Vec3 } from "@/lib/layout";
import { twin, useTwin } from "@/lib/twin/store";
import { TIMING } from "@/lib/twin/timing";
import { LABEL_COLORS, LABELS, type MarbleLabel, type Side } from "@/lib/twin/types";
import { useUi } from "@/lib/ui";

const MAX_FLYING = 8;
const SPACING = 15.5;

interface Flying {
  id: number;
  label: MarbleLabel;
  /** "a": exit -> camera, "hold": in front of the camera, "b": camera -> cup */
  phase: "a" | "hold" | "b";
  t: number;
  side: Side | null;
  path: { p: THREE.Vector3; d: number }[];
}

const v = (p: Vec3) => new THREE.Vector3(...p);

function pathA() {
  return [
    { p: v(DROP.exit), d: 0 },
    { p: v(DROP.funnel), d: TIMING.toCamera * 0.45 },
    { p: v(DROP.camera), d: TIMING.toCamera * 0.55 },
  ];
}

const pileSlot = (i: number): Vec3 => {
  const layer = Math.floor(i / 7);
  const k = i % 7;
  const r = k === 0 ? 0 : 14.5;
  const a = (k / 6) * Math.PI * 2 + layer * 0.5;
  return [Math.cos(a) * r, Math.sin(a) * r, MARBLE_RADIUS + 2 + layer * 11];
};

function pathB(side: Side, pileIndex: number) {
  const s = side === "left" ? -1 : 1;
  const slot = pileSlot(Math.min(pileIndex, 20));
  return [
    { p: v(DROP.camera), d: 0 },
    { p: v(DROP.unterteil), d: TIMING.toCup * 0.3 },
    { p: v(DROP.gateTop), d: TIMING.toCup * 0.18 },
    { p: v(DROP.chuteBottom(s)), d: TIMING.toCup * 0.16 },
    { p: v(DROP.legTop(s)), d: TIMING.toCup * 0.06 },
    { p: v(DROP.legBottom(s)), d: TIMING.toCup * 0.14 },
    { p: v([s * CUP_X + slot[0], slot[1], slot[2]]), d: TIMING.toCup * 0.16 },
  ];
}

function sample(path: Flying["path"], t: number, out: THREE.Vector3) {
  let acc = 0;
  for (let i = 1; i < path.length; i++) {
    const d = path[i].d;
    if (t <= acc + d) {
      const k = d > 0 ? (t - acc) / d : 1;
      return out.lerpVectors(path[i - 1].p, path[i].p, k * (0.6 + 0.4 * k));
    }
    acc += d;
  }
  return out.copy(path[path.length - 1].p);
}
const duration = (path: Flying["path"]) => path.reduce((a, s) => a + s.d, 0);

/** Column of marbles pushed up through the transporter tube. */
function TransportColumn() {
  const mesh = useRef<THREE.InstancedMesh>(null);
  const curve = useMemo(() => new THREE.CatmullRomCurve3(TRANSPORT_PATH.map(v), false, "centripetal"), []);
  const length = useMemo(() => curve.getLength(), [curve]);
  const count = Math.floor(length / SPACING);
  const state = useRef({ offset: 0, target: 0, wraps: new Int32Array(count).fill(-1) });

  useEffect(
    () =>
      twin.onEvent((e) => {
        if (e.kind === "release") state.current.target += SPACING;
      }),
    [],
  );

  const o = useMemo(() => new THREE.Object3D(), []);
  const c = useMemo(() => new THREE.Color(), []);
  useFrame((_, dt) => {
    const m = mesh.current;
    if (!m) return;
    const st = state.current;
    // idle creep while the screw turns, plus a step for every released marble
    if (twin.get().motorEnabled) st.target += dt * 2;
    st.offset = THREE.MathUtils.damp(st.offset, st.target, 6, dt);
    let colorsDirty = false;
    for (let i = 0; i < count; i++) {
      const s = i * SPACING + st.offset;
      const wrap = Math.floor(s / length);
      const u = (s - wrap * length) / length;
      o.position.copy(curve.getPointAt(u));
      // shrink marbles right at the tube exit so they "leave" instead of popping
      const edge = Math.min(1, (1 - u) * length / SPACING);
      o.scale.setScalar(Math.max(0.001, edge));
      o.updateMatrix();
      m.setMatrixAt(i, o.matrix);
      if (st.wraps[i] !== wrap) {
        st.wraps[i] = wrap;
        m.setColorAt(i, c.set(LABEL_COLORS[LABELS[Math.floor(Math.random() * LABELS.length)]]));
        colorsDirty = true;
      }
    }
    m.instanceMatrix.needsUpdate = true;
    if (colorsDirty && m.instanceColor) m.instanceColor.needsUpdate = true;
  });

  return (
    <instancedMesh ref={mesh} args={[undefined, undefined, count]} castShadow>
      <sphereGeometry args={[MARBLE_RADIUS, 20, 14]} />
      <meshStandardMaterial roughness={0.25} />
    </instancedMesh>
  );
}

function FallingMarbles() {
  const flying = useRef<Flying[]>([]);
  const meshes = useRef<(THREE.Mesh | null)[]>([]);
  const materials = useMemo(
    () => Array.from({ length: MAX_FLYING }, () => new THREE.MeshStandardMaterial({ roughness: 0.2 })),
    [],
  );

  useEffect(
    () =>
      twin.onEvent((e) => {
        const list = flying.current;
        if (e.kind === "release") {
          if (list.length >= MAX_FLYING) list.shift();
          list.push({ id: e.id, label: e.label, phase: "a", t: 0, side: null, path: pathA() });
          return;
        }
        const { label, side } = e.detection;
        const waiting = list.find((f) => f.side === null);
        if (waiting) {
          waiting.label = label;
          waiting.side = side;
        } else {
          // live mode without release events: the marble appears at the camera
          if (list.length >= MAX_FLYING) list.shift();
          list.push({ id: e.detection.id, label, phase: "hold", t: TIMING.hold, side, path: pathA() });
        }
      }),
    [],
  );

  const pos = useMemo(() => new THREE.Vector3(), []);
  useFrame((_, dt) => {
    const list = flying.current;
    for (let i = list.length - 1; i >= 0; i--) {
      const f = list[i];
      f.t += dt;
      if (f.phase === "a" && f.t >= duration(f.path)) {
        f.phase = "hold";
        f.t = 0;
      }
      if (f.phase === "hold") {
        const timedOut = f.t > TIMING.detectionTimeout;
        if ((f.side && f.t >= TIMING.hold) || timedOut) {
          f.side ??= twin.get().solenoidOn ? "left" : "right";
          f.phase = "b";
          f.t = 0;
          f.path = pathB(f.side, twin.get().bins[f.side].length);
        }
      }
      if (f.phase === "b" && f.t >= duration(f.path)) {
        twin.landed(f.side!, f.label);
        list.splice(i, 1);
      }
    }
    for (let i = 0; i < MAX_FLYING; i++) {
      const m = meshes.current[i];
      const f = list[i];
      if (!m) continue;
      m.visible = !!f;
      if (!f) continue;
      if (f.phase === "hold") m.position.copy(f.path[f.path.length - 1].p);
      else sample(f.path, f.t, pos) && m.position.copy(pos);
      materials[i].color.set(LABEL_COLORS[f.label]);
    }
  });

  return (
    <group>
      {materials.map((mat, i) => (
        <mesh key={i} ref={(el) => void (meshes.current[i] = el)} material={mat} visible={false} castShadow>
          <sphereGeometry args={[MARBLE_RADIUS, 24, 16]} />
        </mesh>
      ))}
    </group>
  );
}

/** Sorted marbles lying in the two cups. */
function CupPile({ side }: { side: Side }) {
  const pile = useTwin((s) => s.bins[side]);
  const mesh = useRef<THREE.InstancedMesh>(null);
  useEffect(() => {
    const m = mesh.current!;
    const o = new THREE.Object3D();
    const c = new THREE.Color();
    const sx = side === "left" ? -CUP_X : CUP_X;
    for (let i = 0; i < 21; i++) {
      const slot = pileSlot(i);
      o.position.set(sx + slot[0], slot[1], slot[2]);
      o.scale.setScalar(i < pile.length ? 1 : 0.0001);
      o.updateMatrix();
      m.setMatrixAt(i, o.matrix);
      m.setColorAt(i, c.set(LABEL_COLORS[pile[i] ?? "black"]));
    }
    m.instanceMatrix.needsUpdate = true;
    if (m.instanceColor) m.instanceColor.needsUpdate = true;
  }, [pile, side]);
  return (
    <instancedMesh ref={mesh} args={[undefined, undefined, 21]} castShadow>
      <sphereGeometry args={[MARBLE_RADIUS, 20, 14]} />
      <meshStandardMaterial roughness={0.25} />
    </instancedMesh>
  );
}

export default function MarbleFlow() {
  const visible = useUi((s) => s.visible);
  return (
    <group>
      {visible.transporter && <TransportColumn />}
      <FallingMarbles />
      {visible.gate && <CupPile side="left" />}
      {visible.gate && <CupPile side="right" />}
    </group>
  );
}
