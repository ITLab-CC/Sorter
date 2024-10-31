import sys
import os
import numpy as np
import cv2
import PySpin
import time
from rpi_ws281x import PixelStrip, Color
import socket

# NeoPixel-Setup für zwei Streifen
LED_COUNT_1 = 24        # Anzahl der NeoPixel für den ersten Streifen
LED_COUNT_2 = 24        # Anzahl der NeoPixel für den zweiten Streifen
LED_PIN_1 = 18         # GPIO Pin für den ersten Streifen (GPIO 18 - Kanal 0)
LED_PIN_2 = 13          # GPIO Pin für den zweiten Streifen (GPIO 13 - Kanal 1)
LED_FREQ_HZ = 800000    # LED Signalfrequenz in Hz
LED_DMA = 10            # DMA-Kanal für die Ausgabe
LED_BRIGHTNESS = 255    # Helligkeit der LEDs (0-255)
LED_INVERT = False      # Invertiere das Signal bei True
LED_CHANNEL_1 = 0       # Kanal für den ersten Streifen
LED_CHANNEL_2 = 1       # Kanal für den zweiten Streifen

#Socket Verbindung

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect(('localhost', 65432))

# Daten an Server senden (z. B. an Arduino senden)
client_socket.sendall(b'Hello Arduino')

# Daten vom Server empfangen (z. B. von Arduino empfangen)
while True:
    response = client_socket.recv(1024).decode('utf-8')
    print(f"Received from Arduino: {response}")

# Funktion zum Setzen der NeoPixel-Farben für beide Streifen
def set_neopixel_color(strip, color):
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, color)
    strip.show()

def init_neopixel(pin, led_count, channel):
    strip = PixelStrip(led_count, pin, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, channel)
    strip.begin()
    return strip

def capture_flir_camera(mean, sliding_window, strip1, strip2):
    system = PySpin.System.GetInstance()
    cam_list = system.GetCameras()

    if cam_list.GetSize() == 0:
        print("No cameras detected.")
        system.ReleaseInstance()
        return

    camera = cam_list.GetByIndex(0)
    camera.Init()

    try:
        # Setze die Bildrate
        camera.AcquisitionFrameRateEnable.SetValue(True)
        camera.AcquisitionFrameRate.SetValue(30.0)  # Setzen Sie die Framerate auf 30 fps

        # Setze das Pixelformat auf BayerRG8 (falls RGB8 nicht funktioniert)
        supported_formats = get_supported_pixel_formats(camera)
        if 'BayerRG8' in supported_formats:
            pixel_format_enum = PySpin.CEnumerationPtr(camera.GetNodeMap().GetNode("PixelFormat"))
            pixel_format_bayerrg8 = pixel_format_enum.GetEntryByName("BayerRG8")
            if pixel_format_bayerrg8 is not None and PySpin.IsAvailable(pixel_format_bayerrg8) and PySpin.IsWritable(pixel_format_bayerrg8):
                pixel_format_enum.SetIntValue(pixel_format_bayerrg8.GetValue())
                print("Pixelformat auf BayerRG8 gesetzt.")
            else:
                print("BayerRG8 format not writable, using default format.")
        else:
            print("BayerRG8 format not supported, using default format.")

        # Überprüfe das aktuelle Bildformat
        current_pixel_format = PySpin.CEnumerationPtr(camera.GetNodeMap().GetNode("PixelFormat")).GetCurrentEntry()
        print("Aktuelles Bildformat:", current_pixel_format.GetSymbolic())

        camera.AcquisitionMode.SetValue(PySpin.AcquisitionMode_Continuous)
        camera.BeginAcquisition()

        # Setze die NeoPixel auf weiß (beide Streifen)
        print("Setting NeoPixels to white.")
        set_neopixel_color(strip1, Color(255, 255, 255))
        set_neopixel_color(strip2, Color(255, 255, 255))

        while True:
            try:
                image_result = camera.GetNextImage()
                if image_result.IsIncomplete():
                    print("Image incomplete.")
                    continue

                if image_result.IsValid():
                    # Manuelle Konvertierung des Bayer-Bildes zu RGB mit OpenCV
                    print("Konvertiere BayerRG8 zu RGB mit OpenCV")
                    image_data = image_result.GetNDArray()

                    # BayerRG8 -> RGB konvertieren
                    image_rgb = cv2.cvtColor(image_data, cv2.COLOR_BAYER_RG2RGB)

                    # Speichern Sie das Bild mit Zeitstempel
                    timestamp = time.strftime("%Y%m%d-%H%M%S") + str(int(time.time() * 1000) % 1000)
                    filename = f"/tmp/current_image_{timestamp}.jpg"
                    cv2.imwrite(filename, image_rgb)

                    print(f"Bild gespeichert: {filename}")

                    image_result.Release()
                else:
                    print("Image result is not readable or available.")
                    break

            except Exception as ex:
                print("Error during image acquisition: %s" % ex)
                break

    finally:
        camera.EndAcquisition()
        camera.DeInit()
        cam_list.Clear()
        system.ReleaseInstance()

        # Schalte die NeoPixel-LEDs aus (beide Streifen)
        print("Turning off NeoPixels.")
        set_neopixel_color(strip1, Color(0, 0, 0))
        set_neopixel_color(strip2, Color(0, 0, 0))
        print("FLIR Camera deinitialized")

def get_supported_pixel_formats(camera):
    supported_formats = []
    try:
        node_pixel_format = PySpin.CEnumerationPtr(camera.GetNodeMap().GetNode("PixelFormat"))
        if node_pixel_format is not None and PySpin.IsAvailable(node_pixel_format) and PySpin.IsReadable(node_pixel_format):
            entries = node_pixel_format.GetEntries()
            for entry in entries:
                entry_symbolic = PySpin.CEnumEntryPtr(entry)
                if entry_symbolic is not None and PySpin.IsAvailable(entry_symbolic) and PySpin.IsReadable(entry_symbolic):
                    supported_formats.append(entry_symbolic.GetSymbolic())
    except Exception as e:
        print(f"Fehler beim Abrufen der unterstützten Pixelformate: {e}")
    
    return supported_formats

if __name__ == '__main__':
    mean = [None]
    sliding_window = []

    print("Initializing FLIR Camera and NeoPixels")
    # Initialisiere die beiden NeoPixel-Streifen
    strip1 = init_neopixel(LED_PIN_1, LED_COUNT_1, LED_CHANNEL_1)
    strip2 = init_neopixel(LED_PIN_2, LED_COUNT_2, LED_CHANNEL_2)

    capture_flir_camera(mean, sliding_window, strip1, strip2)
