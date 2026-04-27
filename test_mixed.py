import tensorflow as tf
import numpy as np
from pathlib import Path
from PIL import Image
import os

# Finales Mapping
LABELS = {0: "black", 1: "green", 2: "orange", 3: "red"}
THRESHOLD = 0.4 # Etwas niedrigerer Threshold für unbekannte Bilder

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
