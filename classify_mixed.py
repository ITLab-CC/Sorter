"""Classify all images in dataset/mixed-not-labeled/ using the Coral Edge TPU.

Usage:
    sudo .venv-3.9/bin/python classify_mixed.py

Output format per image:
    filename: 97.3% - red
"""

import os
import sys
from pathlib import Path

from PIL import Image
from pycoral.adapters import common, detect
from pycoral.utils.edgetpu import make_interpreter

MODEL_PATH = "my-models/marbel_coral.tflite"
IMAGE_DIR = "dataset/mixed-not-labeled"
THRESHOLD = 0.4

LABELS = {
    0: "black",
    1: "green",
    2: "orange",
    3: "red",
}


def main():
    if not os.path.exists(MODEL_PATH):
        sys.exit(f"Modell nicht gefunden: {MODEL_PATH}")

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

    for img_path in image_files:
        image = Image.open(img_path).convert("RGB")
        image_resized = image.resize(input_size, Image.LANCZOS)
        common.set_input(interpreter, image_resized)
        interpreter.invoke()

        objs = detect.get_objects(interpreter, THRESHOLD)

        if objs:
            best = max(objs, key=lambda o: o.score)
            label = LABELS.get(best.id, f"unknown_{best.id}")
            pct = best.score * 100
            print(f"{img_path.name}: {pct:.1f}% - {label}")
        else:
            print(f"{img_path.name}: keine Erkennung")


if __name__ == "__main__":
    main()
