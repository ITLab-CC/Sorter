from camera import Camera
from server import Server
import time

def main() -> None:
    cam = Camera()
    server = Server()
    server.start()
    while True: 
        try:
            time.sleep(1)
            img = cam.capture_image()
            if img is not None:
                server.send(img)
        except Exception as e:
            print(f"Error while sending to client: {e}")
        except KeyboardInterrupt:
            break
    server.stop()
    cam.release_camera()





if __name__ == "__main__":
    main()