import serial
import threading
import time
import sys

# Serielle Verbindung konfigurieren (Passe die Portnummer und Baudrate an, falls notwendig)
try:
    ser = serial.Serial('/dev/serial/by-id/usb-Arduino__www.arduino.cc__0042_24238313635351910130-if00', 9600, timeout=1)  # '/dev/serial0' ist der Standardport für Raspberry Pi.
    time.sleep(2)  # Warte, bis die serielle Verbindung stabil ist.
except serial.SerialException as e:
    print(f"Fehler beim Öffnen der seriellen Verbindung: {e}")
    sys.exit(1)

# Funktion zum Lesen der seriellen Eingaben
def read_from_arduino():
    while True:
        if ser.in_waiting > 0:
            line = ser.readline().decode('utf-8').strip()
            if line:
                print(f"Antwort vom Arduino: {line}")

# Funktion zum Senden von Eingaben aus der Konsole an Arduino
def write_to_arduino():
    while True:
        user_input = input("Eingabe zum Senden an Arduino: ")
        ser.write(user_input.encode('utf-8'))
        print(f"Gesendeter Text: {user_input}")

# Starten des Lese-Threads
read_thread = threading.Thread(target=read_from_arduino, daemon=True)
read_thread.start()

# Starte die Funktion zum Schreiben an Arduino im Hauptthread
try:
    write_to_arduino()
except KeyboardInterrupt:
    print("\nBeende das Programm.")
finally:
    ser.close()
