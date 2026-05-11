"""Build a marble detection/classification dataset as Label Studio JSON.

For each color subfolder under ``dataset/`` this script:
  1. Crops a 300x300 region around each image's center.
  2. Thresholds + finds contours to locate a marble.
  3. Uses the folder name as the ground-truth class label.
  4. Writes one Label Studio task per image to ``dataset/dataset-<color>.json``.
"""

import json
import os
import datetime
import re

import cv2
import numpy as np

DATASET_ROOT = "dataset"
LABEL_MAP_PATH = "label_map.pbtxt"
SKIP_FOLDERS = {"mixed-not-labeled", "out"}
CROP_SIZE_X = 300
CROP_SIZE_Y = 540
MIN_AREA = 2000
MAX_AREA = 100000
THRESH_VAL = 100

IMAGE_URL_TEMPLATE = "http://127.0.0.1:1000/{folder}/{filename}"


def parse_label_map(path):
    """Parse a label_map.pbtxt file and return a ``{name: id}`` dict."""
    text = open(path).read()
    label_map = {}
    for block in re.finditer(r'item\s*\{(.*?)\}', text, re.DOTALL):
        body = block.group(1)
        id_match = re.search(r'id:\s*(\d+)', body)
        name_match = re.search(r"name:\s*'([^']+)'", body)
        if id_match and name_match:
            label_map[name_match.group(1)] = int(id_match.group(1))
    return label_map


def classify_color(bgr_roi, mask=None):
    """Return one of: 'red', 'green', 'orange', 'black', 'white', 'unknown'."""
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
        return "orange"

    if v_med < 80:
        return "black"
    if s_med < 60:
        return "white"
    return "red" if (h_med < 20 or h_med > 150) else "unknown"


def process_image(image_path, forced_label=None):
    """Detect marble in ``image_path`` and return a result dict or None."""
    frame_bgr = cv2.imread(image_path)
    if frame_bgr is None:
        print(f"Warning: could not load {image_path}")
        return None

    height, width = frame_bgr.shape[:2]

    # Center crop.
    start_x = max(0, width // 2 - CROP_SIZE_X // 2)
    start_y = max(0, height // 2 - CROP_SIZE_Y // 2)
    center_crop = frame_bgr[start_y:start_y + CROP_SIZE_Y, start_x:start_x + CROP_SIZE_X]

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
        label = forced_label if forced_label is not None else classify_color(roi, roi_mask)

        # Convert crop-relative bbox to absolute image coordinates.
        xmin = max(0, start_x + x)
        ymin = max(0, start_y + y)
        xmax = min(width, start_x + x + w)
        ymax = min(height, start_y + y + h)

    return {
        "filename": os.path.basename(image_path),
        "width": width,
        "height": height,
        "class": label,
        "xmin": xmin,
        "ymin": ymin,
        "xmax": xmax,
        "ymax": ymax,
    }


def to_label_studio_task(result, folder_name, task_id):
    """Convert a ``process_image`` result dict into a valid Label Studio Import format."""
    img_width = float(result["width"])
    img_height = float(result["height"])
    xmin = float(result["xmin"])
    ymin = float(result["ymin"])
    xmax = float(result["xmax"])
    ymax = float(result["ymax"])

    # Convert absolute pixel coords to percentages for Label Studio.
    x = (xmin / img_width) * 100 if img_width else 0
    y = (ymin / img_height) * 100 if img_height else 0
    box_width = ((xmax - xmin) / img_width) * 100 if img_width else 0
    box_height = ((ymax - ymin) / img_height) * 100 if img_height else 0

    return {
        "id": task_id,
        "data": {
            "image": IMAGE_URL_TEMPLATE.format(
                folder=folder_name, filename=result["filename"]
            )
        },
        "annotations": [
            {
                "result": [
                    {
                        "from_name": "label",
                        "to_name": "image",
                        "type": "rectanglelabels",
                        "original_width": int(img_width),
                        "original_height": int(img_height),
                        "value": {
                            "x": x,
                            "y": y,
                            "width": box_width,
                            "height": box_height,
                            "rotation": 0,
                            "rectanglelabels": [result["class"]]
                        }
                    }
                ]
            }
        ]
    }


def process_folder(folder_path, label):
    """Process every image in ``folder_path`` and write a Label Studio JSON file."""
    filenames = sorted(
        f for f in os.listdir(folder_path)
        if f.lower().endswith((".png", ".jpg", ".jpeg"))
    )
    if not filenames:
        print(f"Skipping {folder_path}: no images found")
        return

    tasks = []
    folder_name = os.path.basename(folder_path.rstrip(os.sep))
    task_id = 1
    
    for filename in filenames:
        path = os.path.join(folder_path, filename)
        result = process_image(path, forced_label=label)
        if result is None:
            continue
            
        tasks.append(to_label_studio_task(result, folder_name, task_id))
        print(
            f"[{label}] {filename}: "
            f"bbox=({result['xmin']},{result['ymin']},{result['xmax']},{result['ymax']})"
        )
        task_id += 1

    json_path = os.path.join(DATASET_ROOT, f"dataset-{label}.json")
    with open(json_path, "w") as f:
        json.dump(tasks, f, indent=2)

    print(f"Wrote {len(tasks)} tasks to {json_path}\n")


def main():
    label_map = parse_label_map(LABEL_MAP_PATH)
    if not label_map:
        raise SystemExit(f"No labels found in {LABEL_MAP_PATH}. "
                         "Create a label_map.pbtxt first (see README).")

    print(f"Labels from {LABEL_MAP_PATH}: {list(label_map.keys())}")

    for name in sorted(label_map.keys()):
        folder = os.path.join(DATASET_ROOT, name)
        if not os.path.isdir(folder):
            print(f"Skipping label '{name}': folder {folder} not found")
            continue
        process_folder(folder, label=name)


if __name__ == "__main__":
    main()