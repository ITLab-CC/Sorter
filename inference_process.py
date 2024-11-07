import sys
import os
import time
import numpy as np
from PIL import Image
from pycoral.adapters import classify
from pycoral.utils.edgetpu import make_interpreter
import RPi.GPIO as GPIO
import socket

# Debugging
print("Python Executable:", sys.executable)
print("Python Path:", sys.path)

model_path = '../test.tflite'
SORT_PIN = 7

# Setup GPIO
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)
GPIO.setup(SORT_PIN, GPIO.OUT, initial=GPIO.LOW)

# Socket Verbindung
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect(('localhost', 65432))  # Verändere die IP und den Port entsprechend deinem Setup

# Angepasster Schwellenwert für die Dateigröße
MIN_FILE_SIZE = 5000  # Reduzierter Wert, um auch kleinere Bilder zu berücksichtigen

def load_and_infer_image():
    interpreter = make_interpreter(model_path)
    interpreter.allocate_tensors()

    # Get input and output tensor details
    input_details = interpreter.get_input_details()[0]
    output_details = interpreter.get_output_details()[0]

    input_index = input_details['index']
    output_index = output_details['index']

    input_dtype = input_details['dtype']
    input_scale, input_zero_point = input_details['quantization']
    input_shape = input_details['shape']

    while True:
        image_files = [f for f in os.listdir('/tmp') if f.startswith('current_image_') and f.endswith('.jpg')]
        if image_files:
            latest_image = max(image_files, key=lambda x: os.path.getctime(os.path.join('/tmp', x)))
            img_path = os.path.join('/tmp', latest_image)
            
            # Überprüfen der Dateigröße
            file_size = os.path.getsize(img_path)
            if file_size < MIN_FILE_SIZE:
                print(f"Überspringe Bild {latest_image}, da die Dateigröße zu klein ist ({file_size} Bytes).")
                os.remove(img_path)
                continue

            img_pil = Image.open(img_path)
            img_pil = img_pil.resize((224, 224))

            img_array = np.array(img_pil)
            img_array = np.expand_dims(img_array, axis=0)

            # Normalize and convert to the correct type if needed
            if input_dtype == np.uint8:
                img_array = np.array(img_pil, dtype=np.float32)
                img_array = (img_array / 255.0 - input_zero_point) / input_scale
                img_array = np.clip(img_array, 0, 255).astype(np.uint8)
            elif input_dtype == np.int8:
                img_array = np.array(img_pil, dtype=np.float32)
                img_array = (img_array - input_zero_point) / input_scale
                img_array = np.clip(img_array * 255, 0, 255).astype(np.int8)
            else:
                img_array = np.array(img_pil, dtype=np.float32)

            img_array = np.resize(img_array, input_shape)

            interpreter.set_tensor(input_index, img_array)
            interpreter.invoke()

            output_array = interpreter.get_tensor(output_index)
            classes = classify.get_classes(interpreter, top_k=1)

            print("Erkannte Klassen:", classes)

            if classes and classes[0].id == 0 and classes[0].score > 0.7:
                print("Objekt mit ausreichender Zuversicht erkannt. Sortierung aktivieren.")
                
                # Sende Nachricht über die Socket-Verbindung
                client_socket.sendall(b'S1')
                
                # Aktiviere den GPIO für die Sortierung
                GPIO.output(SORT_PIN, GPIO.HIGH)
                time.sleep(1)
                GPIO.output(SORT_PIN, GPIO.LOW)
            else:
                print("Kein Objekt erkannt oder geringe Zuversicht.")
                client_socket.sendall(b'S0')

            os.remove(img_path)

        time.sleep(1)

if __name__ == '__main__':
    try:
        load_and_infer_image()
    except KeyboardInterrupt:
        print("Programm wird beendet.")
    finally:
        client_socket.close()  # Socket-Verbindung bei Programmende schließen
        GPIO.cleanup()  # GPIO-Pins freigeben
