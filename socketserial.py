import serial
import socket
import threading

# Serial-Port einrichten
ser = serial.Serial('/dev/serial/by-id/usb-Arduino__www.arduino.cc__0042_24238313635351910130-if00', 9600, timeout=1)

# Socket-Server einrichten
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(('localhost', 65432))
server_socket.listen()

def handle_client(client_socket):
    while True:
        # Lesen von seriellen Daten und an den Client weiterleiten
        if ser.in_waiting > 0:
            data = ser.readline().decode('utf-8').strip()
            client_socket.sendall(data.encode('utf-8'))
        # Daten vom Client empfangen und an die serielle Schnittstelle senden
        try:
            client_data = client_socket.recv(1024).decode('utf-8')
            ser.write(client_data.encode('utf-8'))
        except ConnectionResetError:
            break

print("Server läuft...")
while True:
    client_sock, addr = server_socket.accept()
    print(f"Verbindung mit {addr}")
    client_thread = threading.Thread(target=handle_client, args=(client_sock,))
    client_thread.start()
