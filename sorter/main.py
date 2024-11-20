from client import Client
import time
import cv2

def handle_image(image):
        # Beispiel: Speichere das Bild oder zeige es an
        filename = f"bild_{int(time.time())}.png"
        cv2.imwrite(filename, image)
        print(f"Bild gespeichert: {filename}")

def main() -> None:
    client = Client()
    client.register_callback(handle_image)
    client.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        client.stop()
        print("Client beendet.")

main()