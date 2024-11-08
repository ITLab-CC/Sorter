import cv2
import PySpin  # type: ignore
import numpy as np
from typing import Optional


class Camera:
    def __init__(self, index: int = 0) -> None:
        self.system = PySpin.System.GetInstance()
        self.cam_list = self.system.GetCameras()
        self.camera: Optional[PySpin.CameraPtr] = None

        if self.cam_list.GetSize() == 0:
            print("No cameras detected.")
            self.release_system()
            return

        self.camera = self.cam_list.GetByIndex(index)
        self.camera.Init()
        self.camera.AcquisitionMode.SetValue(PySpin.AcquisitionMode_Continuous)

    def capture_image(self) -> Optional[np.ndarray]:
        """Captures an image from the camera and returns it as an RGB numpy array."""
        if not self.camera:
            print("Camera not initialized.")
            return None

        image_rgb = None
        try:
            self.camera.BeginAcquisition()
            image_result = self.camera.GetNextImage()

            if image_result.IsIncomplete():
                print("Image incomplete.")
            else:
                image_data = image_result.GetNDArray()
                image_rgb = cv2.cvtColor(image_data, cv2.COLOR_BAYER_RG2RGB)

            image_result.Release()

        except Exception as e:
            print(f"Error capturing image: {e}")

        finally:
            self.camera.EndAcquisition()

        return image_rgb

    def release_camera(self) -> None:
        """Releases the camera resources."""
        if self.camera:
            self.camera.DeInit()
        self.cam_list.Clear()
        self.release_system()

    def release_system(self) -> None:
        """Releases the PySpin system instance."""
        self.system.ReleaseInstance()


if __name__ == "__main__":
    cam = Camera()

    img = cam.capture_image()

    if img is not None:
        cv2.imwrite("img.jpg", img)
        print("Image saved as img.jpg")
    else:
        print("Failed to capture image.")

    cam.release_camera()
