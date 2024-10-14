import sys
import os
import numpy as np
import cv2
import PySpin
import time

def capture_flir_camera(mean, sliding_window):
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

    print("Initializing FLIR Camera")
    capture_flir_camera(mean, sliding_window)
