import os
import sys
import argparse
import time
import numpy as np
from PIL import Image
from pycoral.adapters import common
from pycoral.adapters import detect
from pycoral.utils.edgetpu import make_interpreter

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', help='Pfad zur .tflite Datei', default='marbel_coral.tflite')
    parser.add_argument('--labels', help='Pfad zur Label Datei', default='labels.txt')
    parser.add_argument('--image', help='Pfad zum Testbild', required=True)
    parser.add_argument('--threshold', type=float, default=0.4, help='Score Threshold')
    args = parser.parse_args()

    # Label Map laden
    labels = {}
    if os.path.exists(args.labels):
        with open(args.labels, 'r') as f:
            for line in f:
                pair = line.strip().split(maxsplit=1)
                if len(pair) == 2:
                    labels[int(pair[0])] = pair[1]

    print(f"--- Lade Modell: {args.model}")
    try:
        interpreter = make_interpreter(args.model)
        interpreter.allocate_tensors()
    except Exception as e:
        print(f"❌ Fehler: {e}")
        print("Stelle sicher, dass der Coral USB Accelerator eingesteckt ist und die Treiber installiert sind.")
        return

    # Bild laden
    image = Image.open(args.image).convert('RGB')
    
    # Automatische Skalierung (das Modell braucht 300x300 oder 320x320)
    # PyCoral's set_resized_input erledigt das intern
    size = common.input_size(interpreter)
    image = image.resize(size, Image.LANCZOS)
    common.set_input(interpreter, image)

    print(f"--- Starte Inference auf Edge TPU...")
    start_time = time.perf_counter()
    interpreter.invoke()
    inference_time = time.perf_counter() - start_time
    
    # Ergebnisse holen
    objs = detect.get_objects(interpreter, args.threshold)

    print(f"--- Fertig in {inference_time*1000:.2f}ms")
    print(f"--- Gefundene Objekte: {len(objs)}")
    print("-" * 30)

    for obj in objs:
        label = labels.get(obj.id, f"unknown_{obj.id}")
        print(f"  [{label}] Score: {obj.score:.2f} | BBox: {obj.bbox}")

if __name__ == '__main__':
    main()
