"""Marble Sorter – Main control loop.

Runs the full sorting pipeline, controlled by START/STOP buttons in the
on-screen display:
1. Verify the Coral Edge TPU model file exists.
2. Initialise hardware and show the fullscreen display.
3. Wait until the user presses START (statistics are cleared on each start).
4. While running, stream camera frames and detect marble presence via OpenCV.
5. If detected, classify with the Coral Edge TPU model.
6. Trigger the solenoid to sort left/right based on color.
7. Keep running until STOP is pressed, then return to step 3.
8. Exit cleanly only when the window is closed or on Ctrl+C.

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
from display import MarbleDisplay

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

# Only classify/sort a marble when its detected centre lies within this
# fraction of the frame (width and height) around the image centre. e.g. 0.50
# means the marble's centre must be inside the central 50% band. Increase to
# accept marbles further from the middle; decrease to require tighter centring.
# If some marbels are not detected set this to 1.
CENTER_TOLERANCE = 1.0

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


def detect_marble_present(frame_bayer, crop_size=300, min_area=2000, max_area=100000,
                          thresh_val=100, require_centered=True,
                          center_tolerance=CENTER_TOLERANCE):
    """
    Detects if a marble is present in the center of the given image.

    Args:
        frame_bayer (np.ndarray): The input bayer image.
        crop_size (int): Size of the center square crop.
        min_area (int): Minimum contour area to be considered a marble.
        max_area (int): Maximum contour area to be considered a marble.
        thresh_val (int): Threshold value for binarization.
        require_centered (bool): If True, only count a marble when its centre
            lies within ``center_tolerance`` of the crop centre. Set to False
            to accept a marble anywhere inside the crop.
        center_tolerance (float): Fraction (0-1) of the crop width/height that
            forms the central band the marble centre must fall within.

    Returns:
        bool: True if a marble is detected, False otherwise.
    """
    # 1. Check Image
    if frame_bayer is None:
        print("Warning: Could not load image")
        return False

    height, width = frame_bayer.shape[:2]

    # 2. Fast Cropping
    start_x = max(0, width // 2 - crop_size // 2)
    start_y = max(0, height // 2 - crop_size // 2)

    # Slice the numpy array
    center_crop = frame_bayer[start_y:start_y+crop_size, start_x:start_x+crop_size]

    # 3. Optimized Processing (Grayscale -> Blur -> Threshold -> Invert)
    frame_gray = cv2.cvtColor(center_crop, cv2.COLOR_BAYER_RG2GRAY)
    blurred = cv2.GaussianBlur(frame_gray, (5, 5), 0)

    _, thresh = cv2.threshold(blurred, thresh_val, 255, cv2.THRESH_BINARY)
    inv_thresh = cv2.bitwise_not(thresh)

    # 4. Contour Detection
    contours, _ = cv2.findContours(inv_thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # 5. Validation
    # A contour matching the area criteria means a marble is present. When
    # require_centered is set, its centroid must also sit within the central
    # band of the crop, so marbles drifting in/out of frame are ignored.
    crop_h, crop_w = inv_thresh.shape[:2]
    cx_lo = crop_w * (0.5 - center_tolerance / 2)
    cx_hi = crop_w * (0.5 + center_tolerance / 2)
    cy_lo = crop_h * (0.5 - center_tolerance / 2)
    cy_hi = crop_h * (0.5 + center_tolerance / 2)

    for c in contours:
        area = cv2.contourArea(c)
        if not (min_area <= area <= max_area):
            continue
        if not require_centered:
            return True
        moments = cv2.moments(c)
        if moments["m00"] == 0:
            continue
        cx = moments["m10"] / moments["m00"]
        cy = moments["m01"] / moments["m00"]
        if cx_lo <= cx <= cx_hi and cy_lo <= cy <= cy_hi:
            return True

    return False


def run_elevator(motor, running_event, quit_event):
    """Rotate the elevator motor while *running_event* is set.

    Runs until *quit_event* is set (full program shutdown). The driver is only
    energised while the sorter is actually running; when stopped it is disabled
    so the motor has no holding current (no constant tension/heat) and cannot
    twitch from electrical noise.
    """
    enabled = False
    try:
        while not quit_event.is_set():
            if running_event.is_set():
                if not enabled:
                    motor.enable()
                    enabled = True
                motor.rotate(steps=ELEVATOR_STEPS, pause_seconds=ELEVATOR_PAUSE)
            else:
                if enabled:
                    motor.disable()
                    enabled = False
                time.sleep(0.05)
    finally:
        motor.disable()


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
    print(f"[OK] Coral interpreter ready - input size {input_size}")

    # ------------------------------------------------------------------
    # 3. Initialise hardware
    # ------------------------------------------------------------------
    elevator = ElevatorMotorController()
    leds = NeoPixelController()
    solenoid = SolenoidController()
    cam = Camera()

    # Sleep mode: after a period of inactivity the display blanks itself and
    # the NeoPixels switch off. Touching the screen wakes everything back up.
    def _on_sleep() -> None:
        leds.turn_off()

    def _on_wake() -> None:
        # Restore the LEDs to the state matching the current mode.
        if display.running.is_set():
            leds.set_color((255, 255, 255), 0.5)
        else:
            leds.set_color((0, 255, 0), 0.05)

    display = MarbleDisplay(on_sleep=_on_sleep, on_wake=_on_wake)

    if cam.camera is None:
        sys.exit("No camera detected. Exiting.")
    cam.print_camera_info()
    # Disable auto-exposure and force a short shutter so fast-moving marbles
    # are captured sharply instead of motion-blurred.
    cam.unlock_max_framerate()

    # ------------------------------------------------------------------
    # 4. Start elevator (background thread).
    #    It only spins while the user has pressed START (display.running).
    # ------------------------------------------------------------------
    elevator_thread = threading.Thread(
        target=run_elevator,
        args=(elevator, display.running, display.quit),
        daemon=True,
    )
    elevator_thread.start()
    print("[OK] Elevator thread ready (idle until START).")

    # ------------------------------------------------------------------
    # 6. Main control loop
    #    Wait for the user to press START, sort until STOP is pressed, then
    #    return to waiting. The program only exits when the window is closed
    #    (display.quit) or on Ctrl+C.
    # ------------------------------------------------------------------
    print("\n--- Ready. Press START in the window to begin sorting. ---\n")

    # Ready state: light the NeoPixel rings a soft green until the user starts.
    leds.set_color((0, 255, 0), 0.05)

    try:
        while not display.quit.is_set():
            # Wait (idle) until the user presses START.
            while not display.running.is_set() and not display.quit.is_set():
                time.sleep(0.05)
            if display.quit.is_set():
                break

            # New session: clear all statistics and light up.
            frame_count = 0
            sorted_count = 0
            sort_stats = {"red": 0, "green": 0, "orange": 0, "black": 0}
            leds.set_color((255, 255, 255), 0.5)
            print("\n--- Sorting started ---\n")

            for raw_frame in cam.stream_while_running(
                lambda: display.running.is_set() and not display.quit.is_set()
            ):
                frame_count += 1

                # Convert raw Bayer to BGR
                frame_bgr = cv2.cvtColor(raw_frame, cv2.COLOR_BAYER_BG2BGR) #cv2.COLOR_BAYER_BG2BGR

                # Fast check: is there a marble in the frame?
                is_marbel = detect_marble_present(raw_frame)
                if is_marbel is False:
                    continue

                print("OPENCV erkannt")
                start_time = time.perf_counter()

                # Classify the detected marble with the Coral TPU
                pil_img = Image.fromarray(cv2.cvtColor(raw_frame, cv2.COLOR_BAYER_RG2BGR))
                pil_img = pil_img.resize(input_size, Image.LANCZOS)
                common.set_input(interpreter, pil_img)
                interpreter.invoke()
                objs = detect.get_objects(interpreter, DETECTION_THRESHOLD)

                inference_time = time.perf_counter() - start_time

                if not objs:
                    continue

                best = max(objs, key=lambda o: o.score)
                label = labels.get(best.id, f"unknown_{best.id}")
                confidence = best.score * 100
                sorted_count += 1

                # The model bbox is in the input-tensor space (input_size),
                # so scale it back to the full-resolution frame and convert
                # from (xmin, ymin, xmax, ymax) to (x, y, w, h).
                fh, fw = frame_bgr.shape[:2]
                scale_x = fw / input_size[0]
                scale_y = fh / input_size[1]
                bb = best.bbox
                disp_bbox = (
                    int(bb.xmin * scale_x),
                    int(bb.ymin * scale_y),
                    int((bb.xmax - bb.xmin) * scale_x),
                    int((bb.ymax - bb.ymin) * scale_y),
                )

                # Solenoid ON  → deflect to GREEN side (left)
                # Solenoid OFF → marble falls to RED side (right, default)
                display.update_detection(frame_bgr, label, confidence, disp_bbox)

                if label == "green":
                    solenoid.turn_on()
                    sort_stats["green"] += 1
                    print(f"  Frame {frame_count}: {label} ({confidence:.1f}%) -> LEFT ({inference_time*1000:.2f}ms)")
                elif label == "red":
                    solenoid.turn_off()
                    sort_stats["red"] += 1
                    print(f"  Frame {frame_count}: {label} ({confidence:.1f}%) -> RIGHT ({inference_time*1000:.2f}ms)")
                elif label == "orange":
                    solenoid.turn_on()
                    sort_stats["orange"] += 1
                    print(f"  Frame {frame_count}: {label} ({confidence:.1f}%) -> LEFT ({inference_time*1000:.2f}ms)")
                elif label == "black":
                    solenoid.turn_off()
                    sort_stats["black"] += 1
                    print(f"  Frame {frame_count}: {label} ({confidence:.1f}%) -> RIGHT ({inference_time*1000:.2f}ms)")

                # Cooldown so we don't re-classify the same marble
                time.sleep(COOLDOWN_SECONDS)

                cam.flush_image_queue()

            # Session stopped (STOP pressed or window closed).
            solenoid.turn_off()
            # Back to the ready state: green again (unless we're shutting down).
            if not display.quit.is_set():
                leds.set_color((0, 255, 0), 0.05)
            else:
                leds.turn_off()

            print(f"\n{'=' * 30}")
            print("      SORTING RESULTS")
            print(f"{'=' * 30}")
            print(f"  Frames processed : {frame_count}")
            print(f"  Marbles sorted   : {sorted_count}")
            print(f"  Red   (right)    : {sort_stats['red']}")
            print(f"  Green (left)     : {sort_stats['green']}")
            print(f"  Orange (left)    : {sort_stats['orange']}")
            print(f"  Black (right)    : {sort_stats['black']}")
            print(f"{'=' * 30}")
            if not display.quit.is_set():
                print("\n--- Sorting stopped. Press START to run again. ---\n")

    except KeyboardInterrupt:
        print("\nSorting interrupted by user.")

    finally:
        # --------------------------------------------------------------
        # 7. Shutdown
        # --------------------------------------------------------------
        print("\nShutting down...")

        display.running.clear()
        display.quit.set()
        display.close()
        elevator_thread.join(timeout=5)
        elevator.cleanup()
        print("[OK] Elevator stopped.")

        solenoid.turn_off()
        print("[OK] Solenoid off.")

        leds.turn_off()
        print("[OK] LEDs off.")

        cam.release_camera()
        print("[OK] Camera released.")


if __name__ == "__main__":
    main()
