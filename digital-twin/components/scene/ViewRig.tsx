"use client";

import { useFrame, useThree } from "@react-three/fiber";
import { useEffect, useRef } from "react";
import * as THREE from "three";
import type { OrbitControls as OrbitControlsImpl } from "three-stdlib";
import { useUi, VIEWS } from "@/lib/ui";

export default function ViewRig() {
  const view = useUi((s) => s.view);
  const nonce = useUi((s) => s.viewNonce);
  const { camera, controls } = useThree();
  const anim = useRef<{ pos: THREE.Vector3; target: THREE.Vector3; t: number } | null>(null);

  useEffect(() => {
    const v = VIEWS[view];
    anim.current = { pos: new THREE.Vector3(...v.pos), target: new THREE.Vector3(...v.target), t: 0 };
  }, [view, nonce]);

  useFrame((_, dt) => {
    const a = anim.current;
    const c = controls as unknown as OrbitControlsImpl | null;
    if (!a || !c) return;
    a.t += dt;
    const k = 1 - Math.exp(-dt * 5);
    camera.position.lerp(a.pos, k);
    c.target.lerp(a.target, k);
    c.update();
    if (a.t > 1.6 || camera.position.distanceTo(a.pos) < 0.5) anim.current = null;
  });

  // stop the transition as soon as the user grabs the camera
  useEffect(() => {
    const c = controls as unknown as OrbitControlsImpl | null;
    if (!c) return;
    const cancel = () => (anim.current = null);
    c.addEventListener("start", cancel);
    return () => c.removeEventListener("start", cancel);
  }, [controls]);

  return null;
}
