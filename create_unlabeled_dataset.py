import threading
import time
from typing import List
import os
import glob

import numpy as np
import cv2

from actuator.elevator_motor import ElevatorMotorController
from actuator.led_neopixel import NeoPixelController
from sensor.camera import Camera


def run_motor_until_stopped(
    motor: ElevatorMotorController,
    stop_event: threading.Event,
    pause_seconds: float = 0.002,
    steps_per_batch: int = 200,
) -> None:
    """Continuously rotate the elevator motor until stop_event is set."""
    try:
        motor.enable()
        while not stop_event.is_set():
            motor.rotate(steps=steps_per_batch, pause_seconds=pause_seconds)
    except Exception as exc:
        print(f"Motor thread error: {exc}")

def contains_marble(frame_bayer, crop_size=300, min_area=2000, max_area=100000, thresh_val=100):
    """
    Detects if a marble is present in the center of the given image.
    
    Args:
        frame_bayer (np.ndarray): The input bayer image.
        crop_size (int): Size of the center square crop.
        min_area (int): Minimum contour area to be considered a marble.
        max_area (int): Maximum contour area to be considered a marble.
        thresh_val (int): Threshold value for binarization.
        
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
    # If any contour matches the area criteria, a marble is present
    for c in contours:
        area = cv2.contourArea(c)
        if min_area <= area <= max_area:
            return True

    return False


def main() -> None:
    capture_seconds = 30
    out_dir = "dataset/out"
    led_color = (255, 255, 255)

    # create out dir
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    leds = NeoPixelController()
    motor = ElevatorMotorController()
    camera = Camera()

    stop_motor_event = threading.Event()
    motor_thread = threading.Thread(
        target=run_motor_until_stopped,
        args=(motor, stop_motor_event),
        daemon=True,
    )

    frames_to_save: List[np.ndarray] = []
    frames_processed = 0

    try:
        print("Turning LEDs on...")
        leds.set_color(led_color)

        print("Starting elevator motor...")
        motor_thread.start()

        print(f"Capturing and processing images live for {capture_seconds} seconds...")
        camera.print_camera_info()
        camera.unlock_max_framerate()
        
        # Initialize background subtractor BEFORE the loop
        backSub = cv2.createBackgroundSubtractorMOG2(history=20, varThreshold=50, detectShadows=False)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))

        # Consume the camera stream live
        for frame_ref in camera.stream_for_duration(capture_seconds):
            frames_processed += 1
            
            # analyse image with contains_marble
            if contains_marble(frame_ref):
                frames_to_save.append(frame_ref.copy())
                print(f"Marble detected in frame {frames_processed}. Total kept frames: {len(frames_to_save)}")


    except KeyboardInterrupt:
        print("Interrupted by user.")

    finally:
        print("Stopping elevator motor...")
        stop_motor_event.set()
        motor_thread.join(timeout=2.0)
        motor.cleanup()

        print("Turning LEDs off...")
        time.sleep(1)
        leds.turn_off()

        print("Releasing camera...")
        camera.release_camera()

        # --- Save only centered frames to disk ---
        if frames_to_save:
            # 1. Find all existing frame images in the output folder
            search_pattern = os.path.join(out_dir, "frame_*.png")
            existing_files = glob.glob(search_pattern)

            # 2. Extract the numbers and find the highest one
            highest_idx = -1
            for filepath in existing_files:
                filename = os.path.basename(filepath) # e.g., 'frame_0042.png'
                try:
                    # Split by '_' and '.' to extract '0042', then convert to integer
                    num = int(filename.split('_')[1].split('.')[0])
                    if num > highest_idx:
                        highest_idx = num
                except (IndexError, ValueError):
                    # Ignore any files that happen to match the glob but don't parse cleanly
                    pass 

            # 3. Set the new starting index (if no files exist, highest_idx is -1, so start_idx becomes 0)
            start_idx = highest_idx + 1

            print(f"Writing kept frames to disk, continuing from frame_{start_idx:04d}...")

            # 4. Use the 'start' argument in enumerate to offset the index
            for idx, frame_bayer in enumerate(frames_to_save, start=start_idx):
                # Convert Bayer to BGR right before saving to disk
                frame_bgr = cv2.cvtColor(frame_bayer, cv2.COLOR_BAYER_BG2BGR)
                
                # Create the filename using the offset index
                filename = os.path.join(out_dir, f"frame_{idx:04d}.png")
                cv2.imwrite(filename, frame_bgr)
                
            print(f"Total centered frames successfully saved: {len(frames_to_save)}")
        else:
            print("No frames met the condition. Nothing saved.")


if __name__ == "__main__":
    main()