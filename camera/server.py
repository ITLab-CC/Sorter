import socket
import threading
import cv2
import pickle
import struct
import time
from typing import List, Tuple

class Connection(threading.Thread):
    def __init__(self, conn: socket.socket, addr: Tuple[str, int], server: 'Server') -> None:
        threading.Thread.__init__(self)
        self.conn: socket.socket = conn
        self.addr: Tuple[str, int] = addr
        self.server: 'Server' = server
        self.active: bool = True

    def run(self) -> None:
        self.conn.settimeout(10)
        try:
            while self.active:
                time.sleep(1)
        except socket.timeout:
            print(f"Verbindung zu {self.addr} aufgrund von Timeout geschlossen.")
            self.close()
        except Exception as e:
            print(f"Verbindungsfehler mit {self.addr}: {e}")
            self.close()

    def send_image(self, image_data: bytes) -> None:
        try:
            # Länge der Daten senden, gefolgt von den Bilddaten
            self.conn.sendall(struct.pack(">L", len(image_data)) + image_data)
        except Exception as e:
            print(f"Fehler beim Senden an {self.addr}: {e}")
            self.close()

    def close(self) -> None:
        self.active = False
        self.conn.close()
        self.server.remove_connection(self)

class Server(threading.Thread):
    def __init__(self, host: str = '0.0.0.0', port: int = 9999) -> None:
        threading.Thread.__init__(self)
        self.host: str = host
        self.port: int = port
        self.connections: List[Connection] = []
        self.sock: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.running: bool = True
        self.lock = threading.Lock()

    def run(self) -> None:
        self.sock.bind((self.host, self.port))
        self.sock.listen(5)
        print("Server gestartet und wartet auf Verbindungen...")
        while self.running:
            try:
                conn, addr = self.sock.accept()
                print(f"Neue Verbindung von {addr}")
                connection = Connection(conn, addr, self)
                with self.lock:
                    self.connections.append(connection)
                connection.start()
            except Exception as e:
                print(f"Fehler beim Akzeptieren von Verbindungen: {e}")

    def send(self, image) -> None:
        data = pickle.dumps(image)
        with self.lock:
            for conn in self.connections.copy():
                if conn.active:
                    conn.send_image(data)

    def remove_connection(self, connection: Connection) -> None:
        with self.lock:
            if connection in self.connections:
                self.connections.remove(connection)
                print(f"Verbindung zu {connection.addr} entfernt.")

    def stop(self) -> None:
        self.running = False
        self.sock.close()
        with self.lock:
            for conn in self.connections:
                conn.close()
        print("Server gestoppt.")

if __name__ == "__main__":
    server = Server()
    server.start()
    try:
        while True:
            # Hier kannst du dein Bild laden oder generieren
            # Zum Beispiel ein Dummy-Bild erstellen
            img = cv2.imread('test.png')  # Ersetze 'dein_bild.jpg' durch deinen Bildpfad
            if img is not None:
                server.send(img)
                print("Bild gesendet.")
            else:
                print("Kein Bild gefunden.")
            time.sleep(1)  # Wartezeit zwischen den Sendungen
    except KeyboardInterrupt:
        server.stop()
