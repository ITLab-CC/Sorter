"use client";

import dynamic from "next/dynamic";
import { useCallback, useEffect, useRef } from "react";
import ControlPanel from "@/components/ControlPanel";
import { LiveSource, SimulationSource, type TwinSource } from "@/lib/twin/sources";
import { LED_IDLE, twin } from "@/lib/twin/store";
import type { MarbleLabel } from "@/lib/twin/types";
import { ui, VIEWS, type ViewPreset } from "@/lib/ui";

const SorterScene = dynamic(() => import("@/components/SorterScene"), { ssr: false });

export default function TwinApp() {
  const source = useRef<TwinSource | null>(null);

  const switchSource = useCallback((kind: "sim" | "live") => {
    source.current?.dispose();
    twin.set({ source: kind, running: false, motorEnabled: false, solenoidOn: false, led: LED_IDLE, connection: "idle" });
    twin.resetStats();
    source.current = kind === "sim" ? new SimulationSource() : new LiveSource(twin.get().liveUrl);
    if (kind === "live") source.current.start();
  }, []);

  useEffect(() => {
    // deep links for presentations: /?view=gate&xray=1
    const q = new URLSearchParams(window.location.search);
    const view = q.get("view");
    if (view && view in VIEWS) ui.set({ view: view as ViewPreset });
    if (q.get("xray") === "1") ui.set({ xray: true });

    switchSource("sim");
    const sim = source.current as SimulationSource;
    // start the demo right away
    const t = setTimeout(() => sim.start(), 1200);
    return () => {
      clearTimeout(t);
      source.current?.dispose();
    };
  }, [switchSource]);

  const drop = (label: MarbleLabel) => {
    if (source.current instanceof SimulationSource) source.current.drop(label);
  };

  return (
    <main className="app">
      <SorterScene />
      <ControlPanel
        onStart={() => source.current?.start()}
        onStop={() => source.current?.stop()}
        onDrop={drop}
        onReset={() => twin.resetStats()}
        onSource={switchSource}
        onUrl={(url) => twin.set({ liveUrl: url })}
        onConnect={() => switchSource("live")}
      />
    </main>
  );
}
