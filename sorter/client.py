import socket
import threading
import cv2
import pickle
import struct
import time
from typing import Any, Optional, Callable

class Client:
    def __init__(self, host: str = 'localhost', port: int = 9999) -> None:
        self.host: str = host
        self.port: int = port
        self.sock: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.callback: Optional[Callable[[Any], None]] = None
        self.running: bool = False

    def start(self) -> None:
        """
        Stellt die Verbindung zum Server her und startet den Empfang von Bildern.
        """
        self.sock.connect((self.host, self.port))
        print("Mit dem Server verbunden.")
        self.running = True
        threading.Thread(target=self.receive_images, daemon=True).start()

    def register_callback(self, callback_function: Callable[[Any], None]) -> None:
        """
        Registriert eine Funktion, die aufgerufen wird, wenn ein Bild empfangen wird.
        """
        self.callback = callback_function

    def receive_images(self) -> None:
        """
        Empfängt Bilder vom Server und ruft die registrierte Callback-Funktion auf.
        """
        data: bytes = b""
        payload_size: int = struct.calcsize(">L")

        while self.running:
            # Empfang des Nachrichten-Headers
            while len(data) < payload_size:
                packet: Optional[bytes] = self.sock.recv(4096)
                if not packet:
                    print("Verbindung zum Server verloren.")
                    self.running = False
                    return
                data += packet

            # Bestimme die Größe der Nachricht
            packed_msg_size: bytes = data[:payload_size]
            data = data[payload_size:]
            msg_size: int = struct.unpack(">L", packed_msg_size)[0]

            # Empfang der Bilddaten
            while len(data) < msg_size:
                data += self.sock.recv(4096)

            frame_data: bytes = data[:msg_size]
            data = data[msg_size:]

            # Entpacke das Bild
            frame = pickle.loads(frame_data)

            # Rufe die registrierte Callback-Funktion auf
            if self.callback:
                self.callback(frame)
            else:
                print("Keine Callback-Funktion registriert.")

    def stop(self) -> None:
        """
        Stoppt den Client.
        """
        self.running = False
        self.sock.close()
        print("Client gestoppt.")

if __name__ == "__main__":
    def handle_image(image):
        # Beispiel: Speichere das Bild oder zeige es an
        filename = f"bild_{int(time.time())}.png"
        cv2.imwrite(filename, image)
        print(f"Bild gespeichert: {filename}")

    client = Client()
    client.register_callback(handle_image)
    client.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        client.stop()
        print("Client beendet.")
