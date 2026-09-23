"use client";

import { Canvas, useThree } from "@react-three/fiber";
import { Suspense, useLayoutEffect, useRef } from "react";
import * as THREE from "three";
import PartModel from "@/components/PartModel";

const VIEWS: Record<string, { dir: [number, number, number]; up: [number, number, number] }> = {
  iso: { dir: [1, -1.4, 0.9], up: [0, 0, 1] },
  "front (-Y)": { dir: [0, -1, 0], up: [0, 0, 1] },
  "right (+X)": { dir: [1, 0, 0], up: [0, 0, 1] },
  "top (+Z)": { dir: [0, 0, 1], up: [0, 1, 0] },
};

function Fit({ dir, up, children }: { dir: [number, number, number]; up: [number, number, number]; children: React.ReactNode }) {
  const group = useRef<THREE.Group>(null);
  const { camera, size } = useThree();
  useLayoutEffect(() => {
    const box = new THREE.Box3().setFromObject(group.current!);
    const c = box.getCenter(new THREE.Vector3());
    const s = box.getSize(new THREE.Vector3()).length();
    const cam = camera as THREE.OrthographicCamera;
    cam.up.set(...up);
    cam.position.copy(c).add(new THREE.Vector3(...dir).normalize().multiplyScalar(2000));
    cam.lookAt(c);
    cam.near = 1; cam.far = 5000;
    cam.zoom = Math.min(size.width, size.height) / (s * 1.1);
    cam.updateProjectionMatrix();
    (window as unknown as { bbox: unknown }).bbox = { min: box.min, max: box.max };
  });
  return <group ref={group}>{children}</group>;
}

export default function DebugViewer({ parts }: { parts: string[] }) {
  return (
    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 4, height: "100vh", background: "#ddd" }}>
      {Object.entries(VIEWS).map(([name, v]) => (
        <div key={name} style={{ position: "relative", background: "#fff" }}>
          <span style={{ position: "absolute", zIndex: 1, left: 6, top: 4, font: "12px monospace" }}>
            {parts.join(" + ")} — {name} (X red, Y green, Z blue)
          </span>
          <Canvas orthographic>
            <ambientLight intensity={0.7} />
            <directionalLight position={[300, -500, 800]} intensity={1.6} />
            <axesHelper args={[40]} />
            <Suspense fallback={null}>
              <Fit dir={v.dir} up={v.up}>
                {parts.map((p, i) => (
                  <PartModel key={p} file={p} color={["#b9b4aa", "#7a9cc6", "#c67a7a", "#8cc67a", "#c6b37a"][i % 5]} />
                ))}
              </Fit>
            </Suspense>
          </Canvas>
        </div>
      ))}
    </div>
  );
}
