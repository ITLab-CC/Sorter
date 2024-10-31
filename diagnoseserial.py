import serial
import sys
import argparse
import time

# Argumente parsen
parser = argparse.ArgumentParser(description="Sendet Text an Arduino über die serielle Schnittstelle.")
parser.add_argument("-t", "--text", type=str, required=True, help="Text, der an den Arduino gesendet werden soll.")
args = parser.parse_args()

# Serielle Verbindung konfigurieren (Passe die Portnummer und Baudrate an, falls notwendig)
try:
    ser = serial.Serial('/dev/serial0', 9600, timeout=1)  # '/dev/serial0' ist der Standardport für Raspberry Pi.
    time.sleep(2)  # Warte, bis die serielle Verbindung initialisiert ist.
except serial.SerialException as e:
    print(f"Fehler beim Öffnen der seriellen Verbindung: {e}")
    sys.exit(1)

# Text senden
try:
    text = args.text
    ser.write(text.encode('utf-8'))
    print(f"Gesendeter Text: {text}")

    # Warten und Antwort lesen
    time.sleep(1)
    if ser.in_waiting > 0: 
        response = ser.readline().decode('utf-8').strip()
        print(f"Antwort vom Arduino: {response}")
    else:
        print("Keine Antwort vom Arduino erhalten.")

finally:
    ser.close()
