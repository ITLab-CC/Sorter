"use client";

import { OrbitControls, useProgress } from "@react-three/drei";
import { Canvas } from "@react-three/fiber";
import { Suspense } from "react";
import * as THREE from "three";
import { PARTS } from "@/lib/layout";
import { ui, useUi } from "@/lib/ui";
import Hardware, { Table } from "./scene/Hardware";
import MarbleFlow from "./scene/MarbleFlow";
import PlacedPart from "./scene/PlacedPart";
import ViewRig from "./scene/ViewRig";

function Parts() {
  const visible = useUi((s) => s.visible);
  return (
    <>
      {PARTS.filter((p) => visible[p.group]).map((p) => (
        <PlacedPart key={p.id} part={p} />
      ))}
    </>
  );
}

function Loader() {
  const { progress, active } = useProgress();
  if (!active) return null;
  return <div className="loader">3D-Modelle werden geladen … {Math.round(progress)} %</div>;
}

export default function SorterScene() {
  return (
    <div className="scene">
      <Canvas
        shadows={{ type: THREE.PCFShadowMap }}
        dpr={[1, 2]}
        camera={{ position: [-420, 520, 760], fov: 35, near: 5, far: 6000 }}
        gl={{ antialias: true, toneMapping: THREE.ACESFilmicToneMapping }}
        onPointerMissed={() => ui.set({ selected: null })}
      >
        <color attach="background" args={["#eceae6"]} />
        <fog attach="fog" args={["#eceae6", 1800, 3600]} />
        <hemisphereLight args={["#ffffff", "#b9b4aa", 1.1]} />
        <directionalLight
          position={[-500, 900, 600]}
          intensity={2.2}
          castShadow
          shadow-mapSize={[2048, 2048]}
          shadow-camera-left={-500}
          shadow-camera-right={500}
          shadow-camera-top={600}
          shadow-camera-bottom={-400}
          shadow-camera-near={100}
          shadow-camera-far={2500}
          shadow-bias={-0.0004}
        />
        <directionalLight position={[600, 300, -500]} intensity={0.6} />

        {/* the whole assembly is modelled Z-up in millimetres, like the 3MF files */}
        <group rotation={[-Math.PI / 2, 0, 0]}>
          <Table />
          <Suspense fallback={null}>
            <Parts />
          </Suspense>
          <Hardware />
          <MarbleFlow />
        </group>

        <OrbitControls makeDefault target={[-20, 230, 0]} minDistance={150} maxDistance={2500} maxPolarAngle={Math.PI * 0.49} enableDamping />
        <ViewRig />
      </Canvas>
      <Loader />
    </div>
  );
}
