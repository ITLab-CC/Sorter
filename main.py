"""Marble Sorter – Main control loop.

Runs the full sorting pipeline for a configurable duration:
1. Verify the Coral Edge TPU model file exists.
2. Start the elevator motor (background thread).
3. Turn on the LED ring for camera illumination.
4. Stream camera frames for SORT_DURATION seconds.
5. For each frame, detect marble presence via OpenCV contours.
6. If detected, classify with the Coral Edge TPU model.
7. Trigger the solenoid to sort left/right based on color.
8. Shut everything down cleanly.

Usage:
    sudo .venv-3.10/bin/python main.py
"""

import os
import re
import sys
import time
import threading

import cv2
import numpy as np
from PIL import Image
from pycoral.adapters import common, detect
from pycoral.utils.edgetpu import make_interpreter

from actuator.elevator_motor import ElevatorMotorController
from actuator.led_neopixel import NeoPixelController
from actuator.switch_solenoid_motor import SolenoidController
from sensor.camera import Camera

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
MODEL_PATH = "my-models/marbel_coral.tflite"
LABELS_PATH = "my-models/labels.txt"
LABEL_MAP_PATH = "label_map.pbtxt"

# ---------------------------------------------------------------------------
# Sorting parameters
# ---------------------------------------------------------------------------
SORT_DURATION = 30          # seconds
DETECTION_THRESHOLD = 0.4   # minimum confidence for a detection
COOLDOWN_SECONDS = 0.5      # pause after sorting a marble to avoid re-detecting

# ---------------------------------------------------------------------------
# OpenCV marble-presence detection (mirrored from label_dataset.py)
# ---------------------------------------------------------------------------
CROP_SIZE_X = 300
CROP_SIZE_Y = 540
MIN_AREA = 2000
MAX_AREA = 100000
THRESH_VAL = 100

# ---------------------------------------------------------------------------
# Elevator motor
# ---------------------------------------------------------------------------
ELEVATOR_STEPS = 400
ELEVATOR_PAUSE = 0.002


# ═══════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════

def load_labels():
    """Load class labels from labels.txt or label_map.pbtxt.

    Returns a ``{id: name}`` dict (0-indexed as expected by pycoral).
    """
    labels = {}

    # Prefer my-models/labels.txt (format: "id name")
    if os.path.exists(LABELS_PATH):
        with open(LABELS_PATH, "r") as fh:
            for line in fh:
                pair = line.strip().split(maxsplit=1)
                if len(pair) == 2:
                    labels[int(pair[0])] = pair[1]
        return labels

    # Fall back to label_map.pbtxt (1-indexed, so subtract 1)
    if os.path.exists(LABEL_MAP_PATH):
        text = open(LABEL_MAP_PATH).read()
        for block in re.finditer(r"item\s*\{(.*?)\}", text, re.DOTALL):
            body = block.group(1)
            id_match = re.search(r"id:\s*(\d+)", body)
            name_match = re.search(r"name:\s*'([^']+)'", body)
            if id_match and name_match:
                labels[int(id_match.group(1)) - 1] = name_match.group(1)
        return labels

    print("Warning: No label file found. Using numeric class IDs.")
    return labels


def detect_marble_present(frame_bgr):
    """Check whether a marble is visible in the center of *frame_bgr*.

    Uses the same center-crop + threshold + contour approach as
    ``label_dataset.process_image``.

    Returns the center-cropped BGR region when a marble is found,
    or ``None`` otherwise.
    """
    height, width = frame_bgr.shape[:2]

    start_x = max(0, width // 2 - CROP_SIZE_X // 2)
    start_y = max(0, height // 2 - CROP_SIZE_Y // 2)
    center_crop = frame_bgr[
        start_y : start_y + CROP_SIZE_Y,
        start_x : start_x + CROP_SIZE_X,
    ]

    frame_gray = cv2.cvtColor(center_crop, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(frame_gray, (5, 5), 0)
    _, thresh = cv2.threshold(blurred, THRESH_VAL, 255, cv2.THRESH_BINARY)
    inv_thresh = cv2.bitwise_not(thresh)

    contours, _ = cv2.findContours(
        inv_thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )
    valid = [c for c in contours if MIN_AREA <= cv2.contourArea(c) <= MAX_AREA]

    if not valid:
        return None
    return center_crop


def run_elevator(motor, stop_event):
    """Continuously rotate the elevator motor until *stop_event* is set."""
    motor.enable()
    while not stop_event.is_set():
        motor.rotate(steps=ELEVATOR_STEPS, pause_seconds=ELEVATOR_PAUSE)


# ═══════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════

def main():
    # ------------------------------------------------------------------
    # 1. Check that the Coral model is present
    # ------------------------------------------------------------------
    if not os.path.isfile(MODEL_PATH):
        sys.exit(
            f"Model not found: {MODEL_PATH}\n"
            "Copy marbel_coral.tflite into my-models/ first "
            "(see docs/05-run-sorter.md)."
        )
    print(f"[OK] Model found: {MODEL_PATH}")

    # ------------------------------------------------------------------
    # 2. Load labels & Coral interpreter
    # ------------------------------------------------------------------
    labels = load_labels()
    print(f"[OK] Labels: {labels}")

    try:
        interpreter = make_interpreter(MODEL_PATH)
        interpreter.allocate_tensors()
    except Exception as exc:
        sys.exit(
            f"Failed to load Coral model: {exc}\n"
            "Make sure the Coral USB Accelerator is connected and drivers "
            "are installed."
        )
    input_size = common.input_size(interpreter)
    print(f"[OK] Coral interpreter ready – input size {input_size}")

    # ------------------------------------------------------------------
    # 3. Initialise hardware
    # ------------------------------------------------------------------
    elevator = ElevatorMotorController()
    leds = NeoPixelController()
    solenoid = SolenoidController()
    cam = Camera()

    if cam.camera is None:
        sys.exit("No camera detected. Exiting.")
    cam.print_camera_info()

    # ------------------------------------------------------------------
    # 4. Start elevator (background thread)
    # ------------------------------------------------------------------
    stop_elevator = threading.Event()
    elevator_thread = threading.Thread(
        target=run_elevator,
        args=(elevator, stop_elevator),
        daemon=True,
    )
    elevator_thread.start()
    print("[OK] Elevator motor running.")

    # ------------------------------------------------------------------
    # 5. Turn on LEDs
    # ------------------------------------------------------------------
    leds.set_color((255, 255, 255))
    print("[OK] LEDs on.")

    # ------------------------------------------------------------------
    # 6. Sorting loop
    # ------------------------------------------------------------------
    frame_count = 0
    sorted_count = 0
    sort_stats = {"red": 0, "green": 0, "other": 0}

    print(f"\n--- Sorting for {SORT_DURATION} seconds ---\n")

    try:
        for raw_frame in cam.stream_for_duration(SORT_DURATION):
            frame_count += 1

            # Convert raw Bayer to BGR
            frame_bgr = cv2.cvtColor(raw_frame, cv2.COLOR_BAYER_RG2BGR)

            # Fast check: is there a marble in the frame?
            crop = detect_marble_present(frame_bgr)
            if crop is None:
                continue

            # Classify the detected marble with the Coral TPU
            pil_img = Image.fromarray(cv2.cvtColor(crop, cv2.COLOR_BGR2RGB))
            pil_img = pil_img.resize(input_size, Image.LANCZOS)
            common.set_input(interpreter, pil_img)
            interpreter.invoke()
            objs = detect.get_objects(interpreter, DETECTION_THRESHOLD)

            if not objs:
                continue

            best = max(objs, key=lambda o: o.score)
            label = labels.get(best.id, f"unknown_{best.id}")
            confidence = best.score * 100
            sorted_count += 1

            # Solenoid ON  → deflect to GREEN side (left)
            # Solenoid OFF → marble falls to RED side (right, default)
            if label == "green":
                solenoid.turn_on()
                sort_stats["green"] += 1
                print(f"  Frame {frame_count}: {label} ({confidence:.1f}%) -> LEFT")
            elif label == "red":
                solenoid.turn_off()
                sort_stats["red"] += 1
                print(f"  Frame {frame_count}: {label} ({confidence:.1f}%) -> RIGHT")
            else:
                sort_stats["other"] += 1
                print(f"  Frame {frame_count}: {label} ({confidence:.1f}%) -> SKIP")

            # Cooldown so we don't re-classify the same marble
            time.sleep(COOLDOWN_SECONDS)

    except KeyboardInterrupt:
        print("\nSorting interrupted by user.")

    finally:
        # --------------------------------------------------------------
        # 7. Shutdown
        # --------------------------------------------------------------
        print("\nShutting down...")

        stop_elevator.set()
        elevator_thread.join(timeout=5)
        elevator.cleanup()
        print("[OK] Elevator stopped.")

        solenoid.turn_off()
        print("[OK] Solenoid off.")

        leds.turn_off()
        print("[OK] LEDs off.")

        cam.release_camera()
        print("[OK] Camera released.")

        # Summary
        print(f"\n{'=' * 30}")
        print("      SORTING RESULTS")
        print(f"{'=' * 30}")
        print(f"  Frames processed : {frame_count}")
        print(f"  Marbles sorted   : {sorted_count}")
        print(f"  Red   (right)    : {sort_stats['red']}")
        print(f"  Green (left)     : {sort_stats['green']}")
        print(f"  Other (skipped)  : {sort_stats['other']}")
        print(f"{'=' * 30}")


if __name__ == "__main__":
    main()
