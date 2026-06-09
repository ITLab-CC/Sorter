"""Classify all images in dataset/mixed-not-labeled/ using the Coral Edge TPU.

Usage:
    sudo .venv-3.10/bin/python classify_mixed.py

Output format per image:
    filename: 97.3% - red
"""

import os
import re
import sys
import time
from pathlib import Path

from PIL import Image
from pycoral.adapters import common, detect
from pycoral.utils.edgetpu import make_interpreter

MODEL_PATH = "my-models/marbel_coral.tflite"
LABEL_MAP_PATH = "label_map.pbtxt"
IMAGE_DIR = "dataset/mixed-not-labeled"
THRESHOLD = 0.4


def parse_label_map(path):
    """Parse a label_map.pbtxt file and return a ``{id: name}`` dict (0-indexed for TFLite)."""
    text = open(path).read()
    label_map = {}
    for block in re.finditer(r'item\s*\{(.*?)\}', text, re.DOTALL):
        body = block.group(1)
        id_match = re.search(r'id:\s*(\d+)', body)
        name_match = re.search(r"name:\s*'([^']+)'", body)
        if id_match and name_match:
            label_map[int(id_match.group(1)) - 1] = name_match.group(1)
    return label_map


def main():
    if not os.path.exists(MODEL_PATH):
        sys.exit(f"Modell nicht gefunden: {MODEL_PATH}")

    labels = parse_label_map(LABEL_MAP_PATH)
    if not labels:
        sys.exit(f"No labels found in {LABEL_MAP_PATH}")

    image_dir = Path(IMAGE_DIR)
    if not image_dir.is_dir():
        sys.exit(f"Bildverzeichnis nicht gefunden: {IMAGE_DIR}")

    image_files = sorted(
        p for p in image_dir.iterdir()
        if p.suffix.lower() in (".png", ".jpg", ".jpeg", ".bmp")
    )
    if not image_files:
        sys.exit(f"Keine Bilder in {IMAGE_DIR} gefunden.")

    print(f"Lade Modell: {MODEL_PATH}")
    try:
        interpreter = make_interpreter(MODEL_PATH)
        interpreter.allocate_tensors()
    except Exception as e:
        sys.exit(
            f"Fehler beim Laden des Modells: {e}\n"
            "Stelle sicher, dass der Coral USB Accelerator eingesteckt ist "
            "und die Treiber installiert sind."
        )

    input_size = common.input_size(interpreter)
    print(f"Modell geladen. Input-Groesse: {input_size}")
    print(f"Verarbeite {len(image_files)} Bilder aus {IMAGE_DIR} ...\n")

    inference_times = []

    for img_path in image_files:
        image = Image.open(img_path).convert("RGB")
        image_resized = image.resize(input_size, Image.LANCZOS)
        common.set_input(interpreter, image_resized)

        t_start = time.perf_counter()
        interpreter.invoke()
        objs = detect.get_objects(interpreter, THRESHOLD)
        t_end = time.perf_counter()

        elapsed_ms = (t_end - t_start) * 1000
        inference_times.append(elapsed_ms)

        if objs:
            best = max(objs, key=lambda o: o.score)
            label = labels.get(best.id, f"unknown_{best.id}")
            pct = best.score * 100
            print(f"{img_path.name}: {pct:.1f}% - {label}  ({elapsed_ms:.2f} ms)")
        else:
            print(f"{img_path.name}: keine Erkennung  ({elapsed_ms:.2f} ms)")

    avg_ms = sum(inference_times) / len(inference_times)
    print(f"\n--- Durchschnittliche Inferenzzeit: {avg_ms:.2f} ms "
          f"(ueber {len(inference_times)} Bilder) ---")


if __name__ == "__main__":
    main()
