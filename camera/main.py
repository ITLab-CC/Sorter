from camera import Camera
import cv2

def main() -> None:
    cam = Camera()

    img = cam.capture_image()

    if img is not None:
        cv2.imwrite("img.jpg", img)
        print("Image saved as img.jpg")
    else:
        print("Failed to capture image.")

    cam.release_camera()





if __name__ == "__main__":
    main()