"use client";

import { useFrame, type ThreeEvent } from "@react-three/fiber";
import { useMemo, useRef } from "react";
import * as THREE from "three";
import PartModel from "@/components/PartModel";
import { CHUTE_ANGLE, placementQuaternion, type Placement } from "@/lib/layout";
import { twin } from "@/lib/twin/store";
import { TIMING } from "@/lib/twin/timing";
import { ui, useUi } from "@/lib/ui";

/** groups that turn see-through in X-ray mode, so the marble path is visible */
const XRAY_GROUPS = new Set(["chamber", "gate", "transporter"]);

export default function PlacedPart({ part }: { part: Placement }) {
  const quaternion = useMemo(() => placementQuaternion(part), [part]);
  const pivot = part.pivot ?? [0, 0, 0];
  const hovered = useUi((s) => s.hovered === part.id || s.selected === part.id);
  const xray = useUi((s) => s.xray && XRAY_GROUPS.has(part.group));
  const motion = useRef<THREE.Group>(null);

  useFrame((_, dt) => {
    const g = motion.current;
    if (!g) return;
    const s = twin.get();
    if (part.animated === "screw" && s.motorEnabled) {
      g.rotation.z -= dt * TIMING.screwRevPerSec * Math.PI * 2;
    }
    if (part.animated === "gate") {
      const target = THREE.MathUtils.degToRad(s.solenoidOn ? CHUTE_ANGLE : -CHUTE_ANGLE);
      g.rotation.y = THREE.MathUtils.damp(g.rotation.y, target, 18, dt);
    }
  });

  const events = {
    onPointerOver: (e: ThreeEvent<PointerEvent>) => {
      e.stopPropagation();
      ui.set({ hovered: part.id });
    },
    onPointerOut: () => {
      if (ui.get().hovered === part.id) ui.set({ hovered: null });
    },
    onClick: (e: ThreeEvent<MouseEvent>) => {
      e.stopPropagation();
      ui.set({ selected: ui.get().selected === part.id ? null : part.id });
    },
  };

  return (
    <group position={part.at} quaternion={quaternion} {...events}>
      <group ref={motion}>
        <group position={[-pivot[0], -pivot[1], -pivot[2]]}>
          <PartModel
            file={part.file}
            highlight={hovered}
            opacity={xray ? 0.28 : 1}
            color={part.animated === "gate" ? "#dfe7ee" : undefined}
          />
        </group>
      </group>
    </group>
  );
}
