"use client";

/**
 * Bought parts that are not part of the 3D-print files (motor, camera,
 * display, LEDs, lab stand …) as simple primitives, placed in the same
 * Z-up millimetre frame as the printed parts.
 */
import { useFrame } from "@react-three/fiber";
import { useEffect, useMemo, useRef } from "react";
import * as THREE from "three";
import {
  BOX,
  CHAMBER_BOTTOM,
  CHAMBER_RADIUS,
  GATE_TOP,
  LENS_Z,
  MARBLE_RADIUS,
  MOTOR_CENTER,
} from "@/lib/layout";
import { twin, useTwin } from "@/lib/twin/store";
import { LABEL_COLORS, LABELS } from "@/lib/twin/types";
import { useUi } from "@/lib/ui";

const BLACK = "#16171a";
const ALU = "#b8bcc2";

/** three's cylinders run along local Y; these rotations point them along X/Z. */
const ALONG_X: [number, number, number] = [0, 0, Math.PI / 2];
const ALONG_Z: [number, number, number] = [Math.PI / 2, 0, 0];

function StepperMotor() {
  const [x, y, z] = MOTOR_CENTER;
  return (
    <group position={[x, y, z]}>
      <mesh castShadow>
        <boxGeometry args={[42, 26, 42]} />
        <meshStandardMaterial color="#2a2c30" roughness={0.5} metalness={0.3} />
      </mesh>
      {[-17, 17].map((dy) => (
        <mesh key={dy} position={[0, dy, 0]} castShadow>
          <boxGeometry args={[42.3, 8, 42.3]} />
          <meshStandardMaterial color={ALU} roughness={0.35} metalness={0.7} />
        </mesh>
      ))}
      {/* shaft + coupler into the transporter wall */}
      <mesh position={[0, 27, 0]}>
        <cylinderGeometry args={[5, 5, 14, 16]} />
        <meshStandardMaterial color={ALU} metalness={0.8} roughness={0.3} />
      </mesh>
      {/* connector */}
      <mesh position={[0, -14, 22]}>
        <boxGeometry args={[16, 6, 4]} />
        <meshStandardMaterial color="#f4f4f4" />
      </mesh>
    </group>
  );
}

function FlirCamera() {
  return (
    <group>
      {/* lens (Edmund Optics UC 4 mm + spacer) */}
      <mesh position={[68, 0, LENS_Z]} rotation={ALONG_X} castShadow>
        <cylinderGeometry args={[15, 15, 48, 40]} />
        <meshStandardMaterial color={BLACK} roughness={0.35} metalness={0.4} />
      </mesh>
      {[56, 76].map((x) => (
        <mesh key={x} position={[x, 0, LENS_Z]} rotation={ALONG_X}>
          <cylinderGeometry args={[15.6, 15.6, 3, 40]} />
          <meshStandardMaterial color="#2c2d31" roughness={0.9} />
        </mesh>
      ))}
      {/* Blackfly S body */}
      <mesh position={[107, 0, LENS_Z]} castShadow>
        <boxGeometry args={[30, 29, 29]} />
        <meshStandardMaterial color={BLACK} roughness={0.55} metalness={0.2} />
      </mesh>
      <mesh position={[125, 0, LENS_Z]} rotation={ALONG_X}>
        <cylinderGeometry args={[5, 5, 8, 16]} />
        <meshStandardMaterial color="#333" />
      </mesh>
    </group>
  );
}

function LedRing() {
  const rgb = useTwin((s) => s.led.rgb);
  const brightness = useTwin((s) => s.led.brightness);
  const flash = useRef(0);
  const light = useRef<THREE.PointLight>(null);
  const material = useMemo(() => new THREE.MeshStandardMaterial({ color: "#ffffff", roughness: 0.3 }), []);
  const color = useMemo(() => new THREE.Color(rgb[0] / 255, rgb[1] / 255, rgb[2] / 255), [rgb]);

  useEffect(
    () =>
      twin.onEvent((e) => {
        if (e.kind === "detection") flash.current = 1;
      }),
    [],
  );

  useFrame((_, dt) => {
    flash.current = Math.max(0, flash.current - dt * 3);
    const level = Math.min(1, brightness + flash.current * 0.6);
    material.emissive.copy(color);
    material.emissiveIntensity = 0.3 + level * 3.5;
    if (light.current) {
      light.current.color.copy(color);
      light.current.intensity = level * 6;
    }
  });

  const leds = Array.from({ length: 24 }, (_, i) => (i / 24) * Math.PI * 2);
  const z = CHAMBER_BOTTOM + 7;
  return (
    <group>
      <mesh position={[0, 0, z - 1.5]} rotation={ALONG_Z}>
        <cylinderGeometry args={[36, 36, 1.6, 48, 1, true]} />
        <meshStandardMaterial color={BLACK} side={THREE.DoubleSide} />
      </mesh>
      <mesh position={[0, 0, z - 2]}>
        <ringGeometry args={[27, 36, 48]} />
        <meshStandardMaterial color={BLACK} side={THREE.DoubleSide} />
      </mesh>
      {leds.map((a) => (
        <mesh key={a} position={[Math.cos(a) * 31.5, Math.sin(a) * 31.5, z]} rotation={[0, 0, a]} material={material}>
          <boxGeometry args={[5, 5, 1.6]} />
        </mesh>
      ))}
      <pointLight ref={light} position={[0, 0, z + 25]} distance={160} decay={0} />
    </group>
  );
}

/** Official Raspberry Pi 7" touch display showing the sorter UI. */
function TouchDisplay() {
  const running = useTwin((s) => s.running);
  const last = useTwin((s) => s.lastDetection);
  const counts = useTwin((s) => s.counts);

  const { canvas, texture } = useMemo(() => {
    const canvas = document.createElement("canvas");
    canvas.width = 800;
    canvas.height = 480;
    const texture = new THREE.CanvasTexture(canvas);
    texture.colorSpace = THREE.SRGBColorSpace;
    texture.anisotropy = 4;
    return { canvas, texture };
  }, []);

  useEffect(() => {
    const g = canvas.getContext("2d")!;
    g.fillStyle = "#101216";
    g.fillRect(0, 0, 800, 480);
    g.fillStyle = "#e9edf2";
    g.font = "600 34px system-ui, sans-serif";
    g.fillText("AI-Sorter", 32, 58);
    g.fillStyle = running ? "#1f9d55" : "#b42318";
    g.beginPath();
    g.roundRect(560, 24, 208, 48, 24);
    g.fill();
    g.fillStyle = "#fff";
    g.font = "600 24px system-ui, sans-serif";
    g.textAlign = "center";
    g.fillText(running ? "RUNNING" : "STOPPED", 664, 57);

    // last detection
    g.textAlign = "left";
    if (last) {
      g.fillStyle = LABEL_COLORS[last.label];
      g.beginPath();
      g.arc(120, 200, 70, 0, Math.PI * 2);
      g.fill();
      g.strokeStyle = "#ffffff55";
      g.lineWidth = 3;
      g.stroke();
      g.fillStyle = "#e9edf2";
      g.font = "600 44px system-ui, sans-serif";
      g.fillText(last.label, 220, 190);
      g.font = "28px system-ui, sans-serif";
      g.fillStyle = "#9aa4b2";
      g.fillText(`${(last.confidence * 100).toFixed(1)} %  →  ${last.side === "left" ? "LEFT" : "RIGHT"}`, 220, 236);
    } else {
      g.fillStyle = "#9aa4b2";
      g.font = "28px system-ui, sans-serif";
      g.fillText("Waiting for marbles …", 40, 210);
    }

    // counts
    const max = Math.max(1, ...LABELS.map((l) => counts[l]));
    LABELS.forEach((l, i) => {
      const y = 320 + i * 38;
      g.fillStyle = "#9aa4b2";
      g.font = "22px system-ui, sans-serif";
      g.fillText(l, 40, y + 20);
      g.fillStyle = "#232730";
      g.fillRect(150, y, 520, 26);
      g.fillStyle = LABEL_COLORS[l];
      g.fillRect(150, y, (520 * counts[l]) / max, 26);
      g.fillStyle = "#e9edf2";
      g.fillText(String(counts[l]), 690, y + 20);
    });
    texture.needsUpdate = true;
  }, [canvas, texture, running, last, counts]);

  const x = -CHAMBER_RADIUS - 6 - 97;
  const z = CHAMBER_BOTTOM + 30;
  return (
    <group position={[x, -6.5, z]}>
      <mesh castShadow>
        <boxGeometry args={[194, 20, 110]} />
        <meshStandardMaterial color={BLACK} roughness={0.3} metalness={0.1} />
      </mesh>
      <mesh position={[0, -10.1, 0]} rotation={[Math.PI / 2, 0, 0]}>
        <planeGeometry args={[155, 86]} />
        <meshBasicMaterial map={texture} toneMapped={false} />
      </mesh>
    </group>
  );
}

/** Lab stand that holds chamber and gate in the photos (not a printed part). */
function LabStand() {
  const sx = -70;
  const sy = 150;
  const grey = <meshStandardMaterial color="#a3a8ad" roughness={0.4} metalness={0.3} />;
  const arm = (from: THREE.Vector3, to: THREE.Vector3, key: string) => {
    const mid = from.clone().add(to).multiplyScalar(0.5);
    const len = from.distanceTo(to);
    const q = new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0, 1, 0), to.clone().sub(from).normalize());
    return (
      <group key={key}>
        <mesh position={mid} quaternion={q} castShadow>
          <cylinderGeometry args={[4, 4, len, 16]} />
          {grey}
        </mesh>
        <mesh position={from} castShadow>
          <boxGeometry args={[22, 22, 18]} />
          <meshStandardMaterial color="#8e9399" roughness={0.5} metalness={0.3} />
        </mesh>
      </group>
    );
  };
  return (
    <group>
      <mesh position={[sx + 30, sy + 10, 5]} castShadow receiveShadow>
        <boxGeometry args={[200, 130, 10]} />
        <meshStandardMaterial color="#b4b8bc" roughness={0.5} metalness={0.2} />
      </mesh>
      <mesh position={[sx, sy, 330]} rotation={ALONG_Z} castShadow>
        <cylinderGeometry args={[6, 6, 640, 20]} />
        <meshStandardMaterial color="#c9ccd0" roughness={0.3} metalness={0.35} />
      </mesh>
      {arm(new THREE.Vector3(sx, sy, CHAMBER_BOTTOM + 80), new THREE.Vector3(-18, CHAMBER_RADIUS - 4, CHAMBER_BOTTOM + 80), "a1")}
      {arm(new THREE.Vector3(sx, sy, GATE_TOP - 20), new THREE.Vector3(-45, 12, GATE_TOP - 20), "a2")}
    </group>
  );
}

function Pcb({ at, size, color }: { at: [number, number, number]; size: [number, number]; color: string }) {
  return (
    <mesh position={at} castShadow>
      <boxGeometry args={[size[0], size[1], 1.6]} />
      <meshStandardMaterial color={color} roughness={0.6} />
    </mesh>
  );
}

function Electronics() {
  return (
    <group>
      <Pcb at={[-228, 282, 8]} size={[56, 85]} color="#1f6f43" />
      <mesh position={[-228, 250, 16]} castShadow>
        <boxGeometry args={[40, 20, 14]} />
        <meshStandardMaterial color="#c0c4c8" metalness={0.6} roughness={0.35} />
      </mesh>
      <Pcb at={[-157, 300, 9]} size={[20, 15]} color="#b91c1c" />
      <Pcb at={[-101, 305, 9]} size={[26, 33]} color="#1d4ed8" />
      <mesh position={[-107, 250, 8]}>
        <boxGeometry args={[20, 8, 4]} />
        <meshStandardMaterial color={BLACK} />
      </mesh>
      {/* Coral USB accelerator */}
      <mesh position={[-270, 200, 4.5]} castShadow>
        <boxGeometry args={[65, 30, 8]} />
        <meshStandardMaterial color="#e6e6e6" roughness={0.4} />
      </mesh>
    </group>
  );
}

/** Unsorted marbles lying in the transporter box. */
function HopperMarbles() {
  const mesh = useRef<THREE.InstancedMesh>(null);
  const count = 46;
  useEffect(() => {
    const m = mesh.current!;
    let seed = 7;
    const rnd = () => ((seed = (seed * 16807) % 2147483647) / 2147483647);
    const o = new THREE.Object3D();
    const c = new THREE.Color();
    for (let i = 0; i < count; i++) {
      const col = i % 7;
      const row = Math.floor(i / 7);
      o.position.set(
        BOX[0] + 50 + (col - 3) * 13.5 + (row % 2) * 5 - 2 + rnd() * 2,
        BOX[1] - 22 - row * 15.5 - rnd() * 3,
        47 + (col % 2) * 4 + rnd() * 6,
      );
      o.updateMatrix();
      m.setMatrixAt(i, o.matrix);
      m.setColorAt(i, c.set(LABEL_COLORS[LABELS[Math.floor(rnd() * 4)]]));
    }
    m.instanceMatrix.needsUpdate = true;
    if (m.instanceColor) m.instanceColor.needsUpdate = true;
  }, []);
  return (
    <instancedMesh ref={mesh} args={[undefined, undefined, count]} castShadow>
      <sphereGeometry args={[MARBLE_RADIUS, 20, 14]} />
      <meshStandardMaterial roughness={0.25} />
    </instancedMesh>
  );
}

export function Table() {
  return (
    <mesh position={[0, 0, -0.5]} receiveShadow>
      <planeGeometry args={[4000, 4000]} />
      <meshStandardMaterial color="#e4e2dd" roughness={0.9} />
    </mesh>
  );
}

export default function Hardware() {
  const visible = useUi((s) => s.visible);
  return (
    <group>
      {visible.transporter && <StepperMotor />}
      {visible.transporter && <HopperMarbles />}
      {visible.chamber && <FlirCamera />}
      {visible.chamber && <LedRing />}
      {visible.electronics && <TouchDisplay />}
      {visible.electronics && <Electronics />}
      {visible.helpers && <LabStand />}
    </group>
  );
}

