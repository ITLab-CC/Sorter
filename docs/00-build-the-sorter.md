# Step 0 — Build the Sorter

This guide walks you through building the marble sorter from scratch: the bill
of materials (with purchase links), the 3D-printed parts, the wiring and GPIO
pin map, and step-by-step mechanical assembly.

> **Machine:** Workbench
> **Time:** ~1–2 days (plus 3D-printing time)
> **Skill level:** Basic soldering, wiring, and 3D printing

![Finished marble sorter](img/build/00-overview.jpg)

---

## How It Works

Marbles are lifted from a hopper by a motor-driven **Archimedes screw**, singled
out by a crank-driven feeder (the *Tippything*), and dropped one at a time
through a **camera chamber**. A ring of NeoPixel LEDs lights the marble while a
FLIR machine-vision camera captures it. The Coral Edge TPU classifies the
marble's color, and a **solenoid-actuated gate** diverts it left or right into
the correct bin. A touchscreen shows live detections and START/STOP controls.

```
Hopper → Archimedes screw (stepper) → Feeder → Camera chamber (LED + camera)
       → Classify (Coral TPU) → Solenoid gate → Sorted bins
```

---

## Bill of Materials (BOM)

> Quantities assume a single sorter.

### Compute & Vision

| # | Part | Qty | Notes | Link |
|---|------|-----|-------|------|
| 1 | Raspberry Pi 4 (4 GB+) — or better | 1 | Main controller, runs the sorter software | [buy](https://www.raspberrypi.com/products/raspberry-pi-5/) |
| 2 | microSD card (32 GB+, A2/U3) — or better | 1 | OS + project files | [buy](https://www.sandisk.com/de-de/product-portfolio/memory-cards/microsd-cards) |
| 3 | Official Raspberry Pi 27 W USB-C PSU (Pi 5) | 1 | Stable 5 V/5 A supply for the Pi | [buy](https://www.berrybase.de/raspberry-pi-27w-usb-c-power-supply-netzteil-weiss) |
| 4 | Google Coral USB Accelerator | 1 | Edge TPU for real-time inference (~6 ms/frame) | [buy](https://www.berrybase.de/google-coral-usb-accelerator-fuer-raspberry-pi) |
| 5 | FLIR/Teledyne machine-vision camera (USB3, Bayer) | 1 | Captures the marbles (Spinnaker SDK) | [buy](https://www.teledynevisionsolutions.com/de-de/products/blackfly-s-usb3/?model=BFS-U3-04S2C-C&vertical=machine%20vision&segment=iis) |
| 6 | 4mm UC Series Fixed Focal Length Lens | 1 |  | [buy](https://www.edmundoptics.com/p/4mm-uc-series-fixed-focal-length-lens/2966/) |
| 7 | C/CS-mount lens for the camera | 1 | Match focal length to chamber distance | [buy](https://www.vision-dimension.com/de/objektive/objektiv-zubehoer/zwischenringe/zwischenring-5mm-c-cs-mount-adapter-hq/376) |
| 8 | USB 3.0 cable (locking, for the camera) | 1 | Camera ↔ Pi | [buy](https://www.amazon.com/AmazonBasics-USB-3-0-Cable-Male/dp/B00NH13G5A/ref=pd_sbs_147_t_2/147-0313126-2098633?_encoding=UTF8&refRID=P0RXBWY6EDG34QTJWV3H) |
| 9 | Touchscreen display (DSI or HDMI, e.g. 7") | 1 | On-screen UI / START–STOP | [buy](https://www.berrybase.de/offizielles-raspberry-pi-7-display-mit-kapazitiven-touchscreen) |

### Motion & Actuation

| # | Part | Qty | Notes | Link |
|---|------|-----|-------|------|
| 10 | NEMA 17 stepper motor | 1 | Drives the Archimedes screw transporter | [buy](https://www.omc-stepperonline.com/de/nema-17-bipolar-schrittmotor-42ncm-59-48oz-in-1-7a-42x42x37-5mm-4-adern-mit-1m-kabel-und-stecker-17he15-1704s) |
| 11 | Stepper driver (A4988 or DRV8825) | 1 | Mounted in `MotorController_Halterung` | [buy](https://www.reichelt.de/de/de/shop/produkt/entwicklerboards_-_schrittmotorsteuerung_a4988-282646?PROVID=2788) |
| 12 | 12 V solenoid (push/pull) | 1 | Actuates the sorting gate | [buy](https://www.amazon.de/TAU-0730B-0730S-Elektromagnet-Open-Frame-Solenoid-Elektromagnet-Druckhub/dp/B0DKBRJH9H) |
| 13 | Logic-level N-channel MOSFET module (e.g. IRLZ44N) | 1 | Switches the solenoid from a 3.3 V GPIO | [buy](https://www.reichelt.de/de/de/shop/produkt/entwicklerboards_-_mos_treiber_modul_3_3_5_v_0_24_v_irf52-282562?PROVID=2788) |

### Lighting & Sensing

| # | Part | Qty | Notes | Link |
|---|------|-----|-------|------|
| 14 | NeoPixel (WS2812B) ring(s), 24 LEDs total | 1–2 | Illuminates the camera chamber (firmware uses 24) | [buy](https://www.adafruit.com/product/1586) |
| 15 | MCP3008 8-channel ADC | 1 | Reads the analog light-beam sensor over SPI | [buy](https://www.reichelt.de/de/de/shop/produkt/10-bit_serieller_a_d-wandler_8-kanal_2_7v_spi_dip-16-280371?PROVID=2788) |

### Power & Electronics

| # | Part | Qty | Notes | Link |
|---|------|-----|-------|------|
| 16 | 9 V power supply (2 A) | 1 | Stepper + solenoid rail | [buy](https://www.conrad.de/de/p/hn-power-hnp06-090l6-steckernetzteil-festspannung-9-v-dc-840-ma-6-w-stabilisiert-1527541.html?qwer=Cj0KCQjwrs7RBhDuARIsAIVfBD1PziCrJDfHuDaPcAD64H2dpeSmNBDl83h1PRjsIMu9bYYzNGm3Qn8aAs-mEALw_wcB) |

### Mechanical & Fasteners

| # | Part | Qty | Notes | Link |
|---|------|-----|-------|------|
| 17 | Marbles to sort | a handful | Test material | [buy](https://amzn.eu/d/0aglnTU7) |
| 18 | Marbles to sort | a handful | Test material | [buy](https://amzn.eu/d/0dsa3RWX) |

### Filament

| # | Part | Qty | Notes | Link |
|---|------|-----|-------|------|
| 19 | PLA or PETG filament | ~1 kg | For all printed parts (see below) | [buy](https://eu.store.bambulab.com/de/collections/pla) |

---

## 3D-Printed Parts

All source models live in [`3d-files/`](../3d-files): editable Fusion 360 files
in `f3d/` and ready-to-slice meshes in `3mf/`. Parts are grouped by
sub-assembly.

**Suggested print settings (starting point):**

| Setting | Value |
|---|---|
| Material | PLA (or PETG for higher temp/strength) |
| Layer height | 0.2 mm |
| Infill | 20 % (40 % for the motor/screw mounts) |
| Walls / perimeters | 3 |
| Supports | Only where noted below |

### Transporter (Archimedes screw lift) — [`3d-files/3mf/Transporter`](../3d-files/3mf/Transporter)

| File | Description | Supports |
|---|---|---|
| `Archimedes_Screw.3mf` | The screw that lifts marbles upward | Yes |
| `Motor_Holder.3mf` | Mount for the NEMA 17 stepper | No |
| `Transporter_Case.3mf` | Main body of the lift | Yes |
| `Transporter_Case_Wall.3mf` | Side wall / cover | No |
| `Transporter_Adapter.3mf` | Couples the transporter to the chamber | No |
| `Tube_Straight.3mf` | Straight marble guide tube | Yes |
| `Tube_Curved_67.5°.3mf` | 67.5° marble guide tube | Yes |
| `Tube_Curved_90°.3mf` | 90° marble guide tube | Yes |

![Transporter assembly](img/build/10-transporter.jpg)

### Feeder / "Tippything" (single-marble metering) — [`3d-files/3mf/Tippything`](../3d-files/3mf/Tippything)

| File | Description | Supports |
|---|---|---|
| `Tippything_Case.3mf` | Feeder housing | Yes |
| `Box.3mf` | Hopper / collection box | No |
| `Kurbelschleife.3mf` | Scotch-yoke (crank) that singles out marbles | No |
| `Kurbelschleifen_Funktionstester.3mf` | Test jig for the crank mechanism | No |
| `Track.3mf` | Marble track | No |
| `Rohr.3mf` | Tube | No |
| `Trichter.3mf` | Funnel | No |
| `Plexiglashalter.3mf` | Holder for the acrylic window | No |

![Feeder / Tippything assembly](img/build/11-feeder.jpg)

### Camera chamber — [`3d-files/3mf/Kamera`](../3d-files/3mf/Kamera)

| File | Description | Supports |
|---|---|---|
| `main_chamber.3mf` | Imaging chamber (holds the LED ring + window) | Yes |
| `Kameraholder.3mf` | Camera mount | No |
| `Deckel.3mf` | Chamber lid | No |
| `Unterteil.3mf` | Chamber base | No |
| `MCP3008_Halter.3mf` | Mount for the MCP3008 ADC board | No |

![Camera chamber assembly](img/build/12-camera-chamber.jpg)

### Display & electronics mounts — [`3d-files/3mf/Display`](../3d-files/3mf/Display)

| File | Description | Supports |
|---|---|---|
| `Bildschirmhalterung.3mf` | Touchscreen mount | No |
| `RaspberryPI_Halterung.3mf` | Raspberry Pi mount | No |
| `MotorController_Halterung.3mf` | Stepper-driver mount | No |
| `MOSFET_Halterung.3mf` | MOSFET module mount | No |

![Electronics & display mounts](img/build/13-electronics-mounts.jpg)

### Outer case — [`3d-files/3mf/Case.3mf`](../3d-files/3mf)

| File | Description | Supports |
|---|---|---|
| `Case.3mf` | Main enclosure tying everything together | Yes |

![Outer case](img/build/14-case.jpg)

---

## Tools Required

- Soldering iron + solder (for the NeoPixel, MOSFET, and sensor wiring)
- Soldering iron tip / press for installing M3 heat-set inserts
- Screwdrivers and hex keys (M3)
- Wire cutters / strippers
- Multimeter (to verify rails before powering logic)
- 3D printer

---

## Wiring & GPIO Pin Map

All GPIO numbers are **BCM** (the same numbering the code uses). Pin assignments
come directly from the controller classes in [`actuator/`](../actuator) and
[`sensor/`](../sensor).

| Function | Component | Pi GPIO (BCM) | Source |
|---|---|---|---|
| Stepper ENABLE (active-low) | Stepper driver `EN` | **GPIO 17** | `actuator/elevator_motor.py` |
| Stepper DIR | Stepper driver `DIR` | **GPIO 27** | `actuator/elevator_motor.py` |
| Stepper STEP | Stepper driver `STEP` | **GPIO 22** | `actuator/elevator_motor.py` |
| Solenoid switch | MOSFET gate | **GPIO 16** | `actuator/switch_solenoid_motor.py` |
| NeoPixel data | LED ring `DIN` (via level shifter) | **GPIO 18** | `actuator/led_neopixel.py` |
| Light-beam ADC (SPI) | MCP3008 `CH0` | SPI0 (see below) | `sensor/light_beam.py` |

**MCP3008 ↔ Raspberry Pi (SPI0):**

| MCP3008 pin | Pi pin |
|---|---|
| `VDD` / `VREF` | 3.3 V |
| `AGND` / `DGND` | GND |
| `CLK` | SCLK (GPIO 11) |
| `DOUT` | MISO (GPIO 9) |
| `DIN` | MOSI (GPIO 10) |
| `CS/SHDN` | CE0 (GPIO 8) |

> Enable SPI on the Pi (`sudo raspi-config` → Interface Options → SPI) so the
> MCP3008 / light-beam sensor works.

### Power & safety notes

- The **stepper** and **solenoid** run from the **12 V** rail — keep this
  separate from the Pi's 5 V logic supply and join only the **grounds**.
- Put a **flyback diode** across the solenoid coil; switch it through the
  **MOSFET** on GPIO 16, never directly from a GPIO.
- Drive NeoPixel data through a **74AHCT125 level shifter** (3.3 V → 5 V) and add
  a **1000 µF capacitor** across the LED 5 V supply.
- The stepper `ENABLE` line is **active-low**; the firmware boots it HIGH
  (disabled) so the motor doesn't buzz or heat up at idle.

![Wiring diagram](img/build/20-wiring-diagram.jpg)

---

## Assembly

### 1. Print and prep parts

Print everything in the [3D-Printed Parts](#3d-printed-parts) section. Install
M3 heat-set inserts into the marked bosses. Cut the acrylic window to fit the
`Plexiglashalter`.

![Printed parts laid out](img/build/30-printed-parts.jpg)

### 2. Build the transporter

Fit the **Archimedes screw** into the `Transporter_Case`, mount the **NEMA 17
stepper** to the `Motor_Holder`, and couple it to the screw shaft. Close it with
the `Transporter_Case_Wall`.

![Transporter build](img/build/31-build-transporter.jpg)

### 3. Build the feeder (Tippything)

Assemble the `Tippything_Case`, install the `Kurbelschleife` (scotch-yoke)
mechanism, and attach the `Trichter` funnel and `Box` hopper. This meters
marbles one at a time onto the `Track`.

![Feeder build](img/build/32-build-feeder.jpg)

### 4. Build the camera chamber

Mount the **camera** to the `Kameraholder`, seat the **NeoPixel ring** inside
`main_chamber`, fit the acrylic window, and close it with `Deckel`/`Unterteil`.
Keep the inside matte black to avoid glare.

![Camera chamber build](img/build/33-build-camera-chamber.jpg)

### 5. Mount electronics & display

Attach the **Raspberry Pi**, **stepper driver**, and **MOSFET module** to their
holders (`RaspberryPI_Halterung`, `MotorController_Halterung`,
`MOSFET_Halterung`). Mount the **touchscreen** to the `Bildschirmhalterung` and
the **MCP3008** to the `MCP3008_Halter`.

![Electronics mounting](img/build/34-mount-electronics.jpg)

### 6. Wire everything

Wire according to the [pin map](#wiring--gpio-pin-map). Double-check the 12 V and
5 V rails with a multimeter **before** connecting the Pi.

![Wiring in progress](img/build/35-wiring.jpg)

### 7. Install the solenoid sorting gate

Mount the **solenoid** at the chamber outlet so its plunger swings the gate
between the two bins. Solenoid ON = one side, OFF = the other (default).

![Solenoid gate](img/build/36-solenoid-gate.jpg)

### 8. Final assembly

Combine all sub-assemblies into the `Case`, route and tidy the cables, and
attach the marble bins under the gate.

![Final assembly](img/build/37-final-assembly.jpg)

---

## First Power-On & Smoke Tests

Before running the full sorter, test each subsystem with the standalone scripts
(run from the project root). See [`actuator/README.md`](../actuator/README.md)
and [`sensor/README.md`](../sensor/README.md) for environment setup.

```bash
# Stepper / transporter
sudo .venv-3.10/bin/python actuator/motor_test.py

# Solenoid gate
sudo .venv-3.10/bin/python actuator/solenoid_test.py

# NeoPixel lighting
sudo .venv-3.10/bin/python actuator/neopixel_test.py

# Light-beam sensor
sudo .venv-3.10/bin/python sensor/light_beam.py

# Camera capture
sudo .venv-3.10/bin/python sensor/camera.py
```

If each part responds correctly, the hardware build is done.

---

**Next:** [Step 1 — Raspberry Pi Setup](01-raspberry-pi-setup.md)

[**Home**](../README.md)
