"use client";

import { GROUPS, PARTS, type GroupId } from "@/lib/layout";
import { useTwin } from "@/lib/twin/store";
import { LABEL_COLORS, LABEL_NAMES_DE, LABELS, SORT_RULES, type MarbleLabel } from "@/lib/twin/types";
import { ui, useUi, VIEWS, type ViewPreset } from "@/lib/ui";

type Props = {
  onStart: () => void;
  onStop: () => void;
  onDrop: (label: MarbleLabel) => void;
  onReset: () => void;
  onSource: (kind: "sim" | "live") => void;
  onUrl: (url: string) => void;
  onConnect: () => void;
};

const CONNECTION_DE = {
  idle: "nicht verbunden",
  connecting: "verbinde …",
  open: "verbunden",
  closed: "Verbindung getrennt",
  error: "Fehler",
} as const;

export default function ControlPanel({ onStart, onStop, onDrop, onReset, onSource, onUrl, onConnect }: Props) {
  const s = useTwin((x) => x);
  const visible = useUi((x) => x.visible);
  const xray = useUi((x) => x.xray);
  const focus = useUi((x) => x.selected ?? x.hovered);
  const part = PARTS.find((p) => p.id === focus);
  const live = s.source === "live";
  const [r, g, b] = s.led.rgb;
  const total = LABELS.reduce((a, l) => a + s.counts[l], 0);

  return (
    <>
      <aside className="panel">
        <header>
          <h1>KI-Sorter</h1>
          <p>Digitaler Zwilling · Murmel-Sortiermaschine</p>
        </header>

        <section>
          <div className="seg" role="tablist" aria-label="Datenquelle">
            <button className={!live ? "on" : ""} onClick={() => onSource("sim")}>Simulation</button>
            <button className={live ? "on" : ""} onClick={() => onSource("live")}>Echter Sorter</button>
          </div>
          {live && (
            <div className="live">
              <input
                value={s.liveUrl}
                onChange={(e) => onUrl(e.target.value)}
                spellCheck={false}
                aria-label="WebSocket-Adresse"
              />
              <button onClick={onConnect}>Verbinden</button>
              <p className="status">
                <span className={`dot ${s.connection}`} /> {CONNECTION_DE[s.connection]}
              </p>
            </div>
          )}
        </section>

        <section>
          <h2>Steuerung</h2>
          {!live ? (
            <>
              <div className="row">
                <button className="primary" onClick={s.running ? onStop : onStart}>
                  {s.running ? "■ STOP" : "▶ START"}
                </button>
                <button onClick={onReset}>Zähler zurücksetzen</button>
              </div>
              <div className="drops">
                <span>Murmel einwerfen:</span>
                {LABELS.map((l) => (
                  <button key={l} title={LABEL_NAMES_DE[l]} onClick={() => onDrop(l)} style={{ background: LABEL_COLORS[l] }} aria-label={`${LABEL_NAMES_DE[l]}e Murmel einwerfen`} />
                ))}
              </div>
            </>
          ) : (
            <p className="muted">Im Live-Modus kommt der Zustand vom Raspberry Pi. START/STOP erfolgt am Touchscreen.</p>
          )}
        </section>

        <section>
          <h2>Aktoren &amp; Sensoren</h2>
          <dl className="io">
            <dt>Sortierung</dt>
            <dd><b className={s.running ? "ok" : ""}>{s.running ? "läuft" : "gestoppt"}</b></dd>
            <dt>Schrittmotor <small>GPIO 17/27/22</small></dt>
            <dd>{s.motorEnabled ? "dreht" : "aus"}</dd>
            <dt>Hubmagnet <small>GPIO 16</small></dt>
            <dd>{s.solenoidOn ? "AN → links" : "AUS → rechts"}</dd>
            <dt>LED-Ring <small>GPIO 18</small></dt>
            <dd>
              <span className="swatch" style={{ background: `rgb(${r},${g},${b})`, opacity: 0.35 + s.led.brightness }} />
              {Math.round(s.led.brightness * 100)} %
            </dd>
          </dl>
        </section>

        <section>
          <h2>Erkennung</h2>
          {s.lastDetection ? (
            <div className="det">
              <span className="marble" style={{ background: LABEL_COLORS[s.lastDetection.label] }} />
              <div>
                <b>{LABEL_NAMES_DE[s.lastDetection.label]}</b> · {(s.lastDetection.confidence * 100).toFixed(1)} %
                <br />
                <small>→ {s.lastDetection.side === "left" ? "links" : "rechts"}</small>
              </div>
            </div>
          ) : (
            <p className="muted">Noch keine Murmel erkannt.</p>
          )}
          <table className="counts">
            <tbody>
              {LABELS.map((l) => (
                <tr key={l}>
                  <td><span className="marble sm" style={{ background: LABEL_COLORS[l] }} /> {LABEL_NAMES_DE[l]}</td>
                  <td className="muted">{SORT_RULES[l] === "left" ? "links" : "rechts"}</td>
                  <td className="num">{s.counts[l]}</td>
                </tr>
              ))}
              <tr className="sum">
                <td>Gesamt</td>
                <td />
                <td className="num">{total}</td>
              </tr>
            </tbody>
          </table>
        </section>

        <section>
          <h2>Ansicht</h2>
          <div className="views">
            {(Object.keys(VIEWS) as ViewPreset[]).map((v) => (
              <button key={v} onClick={() => ui.set({ view: v, viewNonce: ui.get().viewNonce + 1 })}>
                {VIEWS[v].label}
              </button>
            ))}
          </div>
          <label className="check">
            <input type="checkbox" checked={xray} onChange={(e) => ui.set({ xray: e.target.checked })} />
            Röntgenblick (Gehäuse durchsichtig)
          </label>
          {(Object.keys(GROUPS) as GroupId[]).map((g) => (
            <label key={g} className="check">
              <input
                type="checkbox"
                checked={visible[g]}
                onChange={(e) => ui.set({ visible: { ...visible, [g]: e.target.checked } })}
              />
              {GROUPS[g].name} <small>{GROUPS[g].hint}</small>
            </label>
          ))}
        </section>
      </aside>

      <div className={`partinfo ${part ? "show" : ""}`} aria-live="polite">
        {part ? (
          <>
            <b>{part.name}</b>
            <span>{part.desc}</span>
            <code>3d-files/3mf/{part.file.replace("deg", "°")}.3mf</code>
          </>
        ) : (
          <span className="muted">Maus über ein Bauteil bewegen · ziehen = drehen · scrollen = zoomen</span>
        )}
      </div>
    </>
  );
}
