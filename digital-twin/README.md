# KI-Sorter · Digitaler Zwilling

Interaktives 3D-Modell des Murmelsortierers als Next.js-Web-App. Die App lädt
die **originalen 3MF-Dateien** aus [`../3d-files/3mf`](../3d-files/3mf), setzt sie
wie im echten Aufbau zusammen und zeigt den Ablauf:

```
Vorratskasten → Archimedes-Schnecke → Steigrohr → Trichter → Kamerakammer (LED + FLIR)
             → Erkennung → Hubmagnet kippt die Rinne → Auslauf links / rechts → Becher
```

Es gibt keine KI und keine Physik-Simulation: Die Murmeln folgen fest definierten
Wegpunkten. Das Modell zeigt, wie die Maschine funktioniert, und lässt sich später
über einen WebSocket mit dem echten Sorter verbinden.

## Starten

```bash
cd digital-twin
npm install
npm run dev          # http://localhost:3000
```

`npm run dev` / `npm run build` kopieren vorher automatisch alle `.3mf` aus
`../3d-files/3mf` nach `public/models` (`scripts/sync-models.mjs`). Wer ein Teil in
Fusion neu exportiert, sieht es also direkt in der Web-App.

Deep-Links für Präsentationen: `/?view=chamber`, `/?view=gate&xray=1`
(`overview`, `chamber`, `gate`, `transporter`).

## Bedienung

- **Simulation**: START/STOP wie am Touchscreen, Murmeln einer Farbe gezielt einwerfen,
  Zähler zurücksetzen.
- **Echter Sorter**: WebSocket-Adresse eintragen und verbinden, dann zeigt das Modell
  den Live-Zustand des Raspberry Pi.
- Maus über ein Bauteil zeigt Name, Funktion und Quelldatei. Klick hält die Auswahl fest.
- **Röntgenblick** macht die Gehäuse durchsichtig, so sieht man die Murmel in Kammer,
  Weiche und Steigrohr.
- Baugruppen lassen sich einzeln ausblenden.

Sortierregel wie in `main.py`: Grün/Orange → Magnet AN → **links**,
Rot/Schwarz → Magnet AUS → **rechts**.

## Anbindung an den echten Sorter

Die App ist so gebaut, dass nur die Datenquelle wechselt, die Szene bleibt gleich:

| Datei | Aufgabe |
|---|---|
| `lib/twin/types.ts` | Datenmodell (`TwinState`) und Nachrichtenformat (`LiveMessage`) |
| `lib/twin/store.ts` | Zustand + Ereignisse (`release`, `detection`) |
| `lib/twin/sources.ts` | `SimulationSource` (Demo) und `LiveSource` (WebSocket) |
| `bridge/twin_bridge.py` | WebSocket-Server für den Raspberry Pi |

Nachrichten (JSON, eine pro WebSocket-Frame; alle `state`-Felder optional):

```json
{"type": "state", "running": true, "motor": true, "solenoid": false,
 "led": {"rgb": [255, 255, 255], "brightness": 0.5}}
{"type": "detection", "label": "green", "confidence": 0.93, "side": "left"}
{"type": "release", "label": "red"}
{"type": "reset"}
```

Ohne Hardware testen:

```bash
pip install websockets
python bridge/twin_bridge.py --demo
# Web-App → „Echter Sorter“ → ws://localhost:8765 → Verbinden
```

Später in `main.py` einbinden (nicht blockierend, eigener Thread):

```python
from twin_bridge import TwinBridge          # Datei auf den Pi kopieren
twin = TwinBridge(port=8765); twin.start()

# bei START / STOP
twin.state(running=True, motor=True, led=((255, 255, 255), 0.5))
twin.state(running=False, motor=False, solenoid=False, led=((0, 255, 0), 0.05))

# nach jeder Klassifizierung
twin.detection(label, confidence / 100, "left" if label in ("green", "orange") else "right")
twin.state(solenoid=label in ("green", "orange"))
```

## Aufbau des 3D-Modells

- Alle Teile werden in einem gemeinsamen Koordinatensystem platziert:
  Z oben, Millimeter, Tischplatte bei z = 0 (`lib/layout.ts`).
- Jedes Teil hat `basis` (Ausrichtung), `pivot` (Bezugspunkt im Teil) und `at`
  (Position in der Welt). Die Maße stammen direkt aus den Meshes.
- Zukaufteile ohne 3MF-Datei (NEMA-17, FLIR-Kamera mit Objektiv, 7"-Display,
  NeoPixel-Ring, Platinen, Laborstativ) sind einfache Grundkörper
  (`components/scene/Hardware.tsx`).
- `/debug?part=Kamera/main_chamber,Kamera/Deckel` zeigt Teile in ihrem eigenen
  Koordinatensystem aus vier Richtungen. Das hilft beim Ausrichten neuer Teile.

Bewusst weggelassen: `Case.3mf` (auf den Fotos nicht verbaut),
`Kurbelschleifen_Funktionstester.3mf` (Testvorrichtung), `Kurbelschleife.3mf`
(sitzt verdeckt im Magnetgehäuse der Weiche). Die Anordnung ist nach den
Aufbaufotos rekonstruiert. Hilfsstützen aus der Bauphase fehlen.
