"""Build a marble detection/classification dataset CSV from a folder of frames.

Ported from test.ipynb. For each image in ``out/`` this script:
  1. Crops a 300x300 region around the image center.
  2. Thresholds + finds contours to locate a marble.
  3. Classifies the marble color (red/green/blue/black/white) via HSV.
  4. Writes one CSV row per image to ``marble_dataset.csv``.
"""

import csv
import os

import cv2
import numpy as np

SOURCE_FOLDER = "out"
CSV_FILENAME = "marble_dataset.csv"
CROP_SIZE = 300
MIN_AREA = 2000
MAX_AREA = 100000
THRESH_VAL = 100

CSV_HEADER = ["filename", "width", "height", "class", "xmin", "ymin", "xmax", "ymax"]


def classify_color(bgr_roi, mask=None):
    """Return one of: 'red', 'green', 'blue', 'black', 'white', 'unknown'."""
    if bgr_roi.size == 0:
        return "unknown"

    hsv = cv2.cvtColor(bgr_roi, cv2.COLOR_BGR2HSV)

    if mask is None:
        mask = np.full(bgr_roi.shape[:2], 255, dtype=np.uint8)

    if cv2.countNonZero(mask) == 0:
        return "unknown"

    m = mask > 0
    h_med = float(np.median(hsv[:, :, 0][m]))
    s_med = float(np.median(hsv[:, :, 1][m]))
    v_med = float(np.median(hsv[:, :, 2][m]))

    # Achromatic checks first.
    if s_med < 60 and v_med < 70:
        return "black"
    if s_med < 50 and v_med > 170:
        return "white"

    # Chromatic: decide by hue (OpenCV hue range 0..179).
    if h_med < 10 or h_med >= 160:
        return "red"
    if 35 <= h_med <= 85:
        return "green"
    if 90 <= h_med <= 135:
        return "blue"

    if v_med < 80:
        return "black"
    if s_med < 60:
        return "white"
    return "red" if (h_med < 20 or h_med > 150) else "unknown"


def process_image(image_path):
    """Detect marble in ``image_path`` and return a CSV row (list) or None."""
    frame_bgr = cv2.imread(image_path)
    if frame_bgr is None:
        print(f"Warning: could not load {image_path}")
        return None

    height, width = frame_bgr.shape[:2]

    # Center crop.
    start_x = max(0, width // 2 - CROP_SIZE // 2)
    start_y = max(0, height // 2 - CROP_SIZE // 2)
    center_crop = frame_bgr[start_y:start_y + CROP_SIZE, start_x:start_x + CROP_SIZE]

    # Grayscale -> Blur -> Threshold -> Invert.
    frame_gray = cv2.cvtColor(center_crop, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(frame_gray, (5, 5), 0)
    _, thresh = cv2.threshold(blurred, THRESH_VAL, 255, cv2.THRESH_BINARY)
    inv_thresh = cv2.bitwise_not(thresh)

    # Contour detection.
    contours, _ = cv2.findContours(inv_thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    valid_contours = [c for c in contours if MIN_AREA <= cv2.contourArea(c) <= MAX_AREA]
    if not valid_contours:
        label = "unknown"
        xmin = ymin = xmax = ymax = 0
    else:
        largest_contour = max(valid_contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(largest_contour)

        # Mask for the marble inside the crop.
        contour_mask = np.zeros(inv_thresh.shape, dtype=np.uint8)
        cv2.drawContours(contour_mask, [largest_contour], -1, 255, thickness=cv2.FILLED)
        roi = center_crop[y:y + h, x:x + w]
        roi_mask = contour_mask[y:y + h, x:x + w]
        label = classify_color(roi, roi_mask)

        # Convert crop-relative bbox to absolute image coordinates.
        xmin = max(0, start_x + x)
        ymin = max(0, start_y + y)
        xmax = min(width, start_x + x + w)
        ymax = min(height, start_y + y + h)

    return [
        os.path.basename(image_path),
        width,
        height,
        label,
        xmin,
        ymin,
        xmax,
        ymax,
    ]


def main():
    rows = []
    filenames = sorted(
        f for f in os.listdir(SOURCE_FOLDER)
        if f.lower().endswith((".png", ".jpg", ".jpeg"))
    )

    for filename in filenames:
        path = os.path.join(SOURCE_FOLDER, filename)
        row = process_image(path)
        if row is None:
            continue
        rows.append(row)
        print(f"{filename}: class={row[3]} bbox=({row[4]},{row[5]},{row[6]},{row[7]})")

    with open(CSV_FILENAME, mode="w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(CSV_HEADER)
        writer.writerows(rows)

    print(f"\nWrote {len(rows)} rows to {CSV_FILENAME}")


if __name__ == "__main__":
    main()
