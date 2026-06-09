import re
import tensorflow as tf
import numpy as np
from pathlib import Path
from PIL import Image
import os

LABEL_MAP_PATH = "label_map.pbtxt"
THRESHOLD = 0.4 # Etwas niedrigerer Threshold für unbekannte Bilder


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


LABELS = parse_label_map(LABEL_MAP_PATH)

interpreter = tf.lite.Interpreter(
    model_path="/workspaces/zip_ai/models/ssd_mobilenet_v2_quant.tflite"
)
interpreter.allocate_tensors()

input_details  = interpreter.get_input_details()
output_details = interpreter.get_output_details()
output_map = {o['name']: o['index'] for o in output_details}

# Pfad zu den neuen Bildern
mixed_dir = Path("/workspaces/zip_ai/dataset/dataset/mixed-not-labeled")
image_files = list(mixed_dir.glob("*.jpg")) + list(mixed_dir.glob("*.png"))

print(f"🚀 Teste {len(image_files)} ungelabelte Bilder aus 'mixed-not-labeled'...\n")
print(f"{'Dateiname':<25} | {'Ergebnis':<15} | {'Score':<8}")
print("-" * 55)

for img_path in sorted(image_files):
    # Bild laden
    image = Image.open(img_path).convert("RGB").resize((300, 300))
    input_array = np.expand_dims(np.array(image, dtype=np.uint8), axis=0)

    # Inference
    interpreter.set_tensor(input_details[0]['index'], input_array)
    interpreter.invoke()

    # Outputs
    scores  = interpreter.get_tensor(output_map['StatefulPartitionedCall:1'])[0]
    classes = interpreter.get_tensor(output_map['StatefulPartitionedCall:2'])[0]
    count   = int(interpreter.get_tensor(output_map['StatefulPartitionedCall:0'])[0])

    found = False
    best_label = "Nichts"
    best_score = 0.0

    for i in range(count):
        if scores[i] >= THRESHOLD:
            class_id = int(classes[i])
            best_label = LABELS.get(class_id, f"ID {class_id}")
            best_score = scores[i]
            found = True
            break # Wir nehmen die Top-Detection

    print(f"{img_path.name:<25} | {best_label:<15} | {best_score:.2f}")

print("-" * 55)
print("Test abgeschlossen. Prüfe die Dateinamen gegen deine Bilder! 🦾")
