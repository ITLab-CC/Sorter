import os
from PIL import Image
from pycoral.adapters import common, detect
from pycoral.utils.edgetpu import make_interpreter
import numpy as np

# Ordner, in dem die Bilder gespeichert sind
image_dir = '/tmp'

# Nur Bilder, die mit 'current_image' beginnen
image_files = [f for f in os.listdir(image_dir) if f.startswith('current_image') and f.endswith(('.jpg', '.png'))]

# Wenn es keine passenden Bilder gibt
if not image_files:
    raise FileNotFoundError("Keine Bilder gefunden, die mit 'current_image' beginnen.")

# Nimm das erste gefundene Bild (du kannst hier auch erweitern, um alle zu verarbeiten)
image_path = os.path.join(image_dir, image_files[0])
print(f'Verwende Bild: {image_path}')

# Lade das Bild
image = Image.open(image_path).convert('RGB')

# Lade das TensorFlow Lite Modell (Mobilenet SSD für Objekt-Erkennung)
model_path = '../best-object_int8.tflite'
interpreter = make_interpreter(model_path)
interpreter.allocate_tensors()

# Setze das Bild als Eingabe für das Modell
_, scale = common.set_resized_input(interpreter, image.size, lambda size: image.resize(size, Image.Resampling.LANCZOS))

# Führe die Vorhersage durch
interpreter.invoke()

# Ergebnisse aus dem Interpreter extrahieren
objects = detect.get_objects(interpreter, score_threshold=0.5, image_scale=scale)

# Labels für das COCO-Dataset
LABELS = {
    0: 'background', 1: 'person', 2: 'bicycle', 3: 'car', 17: 'cat', 18: 'dog'
}

# Ergebnisse anzeigen und Aktionen ausführen
for obj in objects:
    object_id = obj.id
    score = obj.score
    bbox = obj.bbox  # Begrenzungsrahmen (Bounding Box)

    print(f'Erkanntes Objekt: {LABELS.get(object_id, object_id)} mit {score:.2f} Konfidenz')

    if object_id == 1:  # Person erkannt
        print("Aktion: Person erkannt, starte Alarmsystem.")
    elif object_id == 17:  # Katze erkannt
        print("Aktion: Katze erkannt, starte Fütterungssystem.")
    elif object_id == 18:  # Hund erkannt
        print("Aktion: Hund erkannt, starte Türöffner.")
