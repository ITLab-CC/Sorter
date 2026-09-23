"use client";

import { useLoader } from "@react-three/fiber";
import { useMemo } from "react";
import * as THREE from "three";
import { ThreeMFLoader } from "three/examples/jsm/loaders/3MFLoader.js";
import { toCreasedNormals } from "three/examples/jsm/utils/BufferGeometryUtils.js";

export const modelUrl = (file: string) => `/models/${file}.3mf`;

const CREASE = THREE.MathUtils.degToRad(35);
const prepared = new WeakSet<THREE.Object3D>();

/** Smooth curved surfaces but keep hard edges on the printed parts. */
function prepare(source: THREE.Group) {
  if (prepared.has(source)) return;
  source.traverse((o) => {
    const mesh = o as THREE.Mesh;
    if (mesh.isMesh) mesh.geometry = toCreasedNormals(mesh.geometry, CREASE);
  });
  prepared.add(source);
}

type Props = {
  file: string;
  color?: string;
  opacity?: number;
  highlight?: boolean;
};

/** Loads one 3MF file from /public/models and renders it in its native (Z-up, mm) frame. */
export default function PartModel({ file, color = "#f3f1ec", opacity = 1, highlight = false }: Props) {
  const source = useLoader(ThreeMFLoader, modelUrl(file));
  prepare(source);

  const material = useMemo(
    () =>
      new THREE.MeshStandardMaterial({
        color,
        roughness: 0.62,
        metalness: 0,
        transparent: opacity < 1,
        opacity,
        depthWrite: opacity >= 1,
        side: THREE.DoubleSide,
        emissive: highlight ? "#3b82f6" : "#000000",
        emissiveIntensity: highlight ? 0.35 : 0,
      }),
    [color, opacity, highlight],
  );
  const object = useMemo(() => {
    const clone = source.clone(true);
    clone.traverse((o) => {
      const mesh = o as THREE.Mesh;
      if (mesh.isMesh) {
        mesh.material = material;
        mesh.castShadow = opacity >= 1;
        mesh.receiveShadow = true;
      }
    });
    return clone;
  }, [source, material, opacity]);

  return <primitive object={object} />;
}
