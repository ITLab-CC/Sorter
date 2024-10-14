import sys
import os
import numpy as np
from PIL import Image
import cv2
import base64
from scipy import ndimage
from functools import partial
from pycoral.adapters import classify
from pycoral.utils.edgetpu import make_interpreter
import RPi.GPIO as GPIO
import asyncio
import threading
import argparse

# Import the Spinnaker Python module
import PySpin

# Debugging
print("Python Executable:", sys.executable)
print("Python Path:", sys.path)

# Path to edgetpu compatible model
model_path = '../model.tflite'

# Mode configuration
mode = "sort"
sendPin = 7
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)
GPIO.setup(sendPin, GPIO.OUT, initial=GPIO.LOW)
filter_type = 'zone'

# Define any required filters
class BiQuadFilter:
    # Define your filter parameters here
    def __init__(self, type, Fc, Q, peakGainDB):
        self.type = type
        self.Fc = Fc
        self.Q = Q
        self.peakGainDB = peakGainDB

    def process(self, value):
        # Implement your filter processing here
        return value  # Placeholder

bq = BiQuadFilter('band', 0.1, 0.707, 0.0)

def send_over_ws(msg, cam_sockets):
    for ws in cam_sockets:
        ws.write_message(msg)

def format_img_tm2(cv_mat):
    ret, buf = cv2.imencode('.jpg', cv_mat)
    encoded = base64.b64encode(buf)
    return encoded.decode('ascii')

def is_good_photo(img, width, height, mean, sliding_window):
    detection_zone_height = 20
    detection_zone_interval = 5
    threshold = 4.5

    if filter_type == 'zone':
        detection_zone_avg = np.mean(img[height // 2 : (height // 2) + detection_zone_height : detection_zone_interval, 0:-1:3])
    elif filter_type == 'biquad2d':
        detection_zone_avg = abs(bq.process(np.mean(img)))
    elif filter_type == 'biquad':
        detection_zone_avg = abs(bq.process(np.mean(img[height // 2: (height // 2) + detection_zone_height: detection_zone_interval, 0:-1:3])))
    elif filter_type == 'center_of_mass':
        center = ndimage.center_of_mass(img)
        detection_zone_avg = (center[0] + center[1]) / 2

    if len(sliding_window) > 30:
        mean[0] = np.mean(sliding_window)
        sliding_window.clear()
    else:
        sliding_window.append(detection_zone_avg)

    if mean[0] is not None and abs(detection_zone_avg - mean[0]) > threshold:
        print("Target Detected Taking Picture")
        return True

    return False

def on_new_frame(cv_mat, interpreter, mean, sliding_window, send_over_ws, cam_sockets):
    img_pil = Image.fromarray(cv_mat)
    width, height = img_pil.size
    is_good_frame = is_good_photo(cv_mat, width, height, mean, sliding_window)
    if is_good_frame:
        if (width, height) != (224, 224):
            img_pil = img_pil.resize((224, 224))

        if mode == 'train':
            message = {'image': format_img_tm2(cv_mat), 'shouldTakePicture': True}
            send_over_ws(message, cam_sockets)

        elif mode == 'sort':
            classify.set_input(interpreter, img_pil)
            interpreter.invoke()
            classes = classify.get_classes(interpreter, top_k=1)
            print(classes)
            if classes and classes[0].id == 0 and classes[0].score > 0.95:
                GPIO.output(sendPin, GPIO.HIGH)
            else:
                GPIO.output(sendPin, GPIO.LOW)

def capture_flir_camera(on_new_frame, interpreter, mean, sliding_window, send_over_ws, cam_sockets):
    system = PySpin.System.GetInstance()
    cam_list = system.GetCameras()
    
    if cam_list.GetSize() == 0:
        print("No cameras detected.")
        system.ReleaseInstance()
        return

    camera = cam_list.GetByIndex(0)
    camera.Init()
    
    try:
        camera.AcquisitionMode.SetValue(PySpin.AcquisitionMode_Continuous)
        camera.BeginAcquisition()
        
        while True:
            try:
                image_result = camera.GetNextImage()
                if image_result.IsIncomplete():
                    print("Image incomplete.")
                    continue
                
                image_data = image_result.GetNDArray()
                on_new_frame(image_data, interpreter, mean, sliding_window, send_over_ws, cam_sockets)
                image_result.Release()
                
            except Exception as ex:
                print("Error: %s" % ex)
                break
        
    finally:
        camera.EndAcquisition()
        camera.DeInit()
        cam_list.Clear()
        system.ReleaseInstance()
        print("FLIR Camera deinitialized")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    mode_parser = parser.add_mutually_exclusive_group(required=False)
    mode_parser.add_argument('--train', dest='will_sort', action='store_false')
    mode_parser.add_argument('--sort', dest='will_sort', action='store_true')

    filter_parse = parser.add_mutually_exclusive_group(required=False)
    filter_parse.add_argument('--zone-activation', dest='zone', action='store_true')
    filter_parse.add_argument('--biquad', dest='biquad', action='store_true')
    filter_parse.add_argument('--biquad2d', dest='biquad2d', action='store_true')
    filter_parse.add_argument('--center-of-mass', dest='center_of_mass', action='store_true')

    camera_parse = parser.add_mutually_exclusive_group(required=False)
    camera_parse.add_argument('--flir', dest='flir', action='store_true')
    camera_parse.add_argument('--opencv', dest='opencv', action='store_true')
    camera_parse.add_argument('--arducam', dest='arducam', action='store_true')

    parser.set_defaults(will_sort=True)
    args = parser.parse_args()

    cam_sockets = []
    new_loop = asyncio.new_event_loop()
    server_thread = threading.Thread(target=lambda: CameraWebsocketHandler.start_server(new_loop, cam_sockets))
    server_thread.start()

    interpreter = make_interpreter(model_path)
    interpreter.allocate_tensors()

    if args.will_sort:
        mode = "sort"
    else:
        mode = "train"

    if args.zone: filter_type = 'zone'
    elif args.biquad: filter_type = 'biquad'
    elif args.biquad2d: filter_type = 'biquad2d'
    elif args.center_of_mass: filter_type  = 'center_of_mass'

    mean = [None]
    sliding_window = []

    if args.flir:
        print("Initializing FLIR Camera")
        capture_flir_camera(on_new_frame, interpreter, mean, sliding_window, send_over_ws, cam_sockets)
    elif args.arducam:
        raise Exception("Arducam Support Coming")
    else:
        cap = cv2.VideoCapture(0)
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            cv2_im = frame
            pil_im = Image.fromarray(cv2_im)
            pil_im = pil_im.resize((224, 224))
            pil_im = pil_im.transpose(Image.FLIP_LEFT_RIGHT)
            cv2.imshow('frame', cv2_im)
            on_new_frame(cv2_im, interpreter, mean, sliding_window, send_over_ws, cam_sockets)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        cap.release()
        cv2.destroyAllWindows()
