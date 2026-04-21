import cv2
import PySpin  # type: ignore
import numpy as np
import time
import psutil
import os
from typing import Optional, List

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

    def capture_for_duration(self, duration_sec: int) -> List[np.ndarray]:
        """Captures raw frames as fast as possible for a set duration in seconds."""
        if not self.camera:
            print("Camera not initialized.")
            return []

        frames: List[np.ndarray] = []
        try:
            self.camera.BeginAcquisition()
            
            # Setup timers
            start_time = time.perf_counter()
            end_time = start_time + duration_sec
            
            # Loop until the time is up
            while time.perf_counter() < end_time:
                try:
                    # Grab image (1000ms timeout prevents infinite hangs if disconnected)
                    image_result = self.camera.GetNextImage(1000)

                    if not image_result.IsIncomplete():
                        # Get raw data. We MUST use .copy() here. 
                        # If we don't, releasing the PySpin image destroys the array data in RAM.
                        image_data = image_result.GetNDArray()
                        frames.append(image_data.copy())
                        
                    # Release the buffer immediately so the camera can capture the next frame
                    image_result.Release()
                    
                except PySpin.SpinnakerException as ex:
                    print(f"Spinnaker Exception during capture: {ex}")
                    break

        except Exception as e:
            print(f"Error capturing sequence: {e}")

        finally:
            self.camera.EndAcquisition()

        return frames

    def release_camera(self) -> None:
        """Releases the camera resources."""
        if self.camera:
            self.camera.DeInit()
            del self.camera 
            self.camera = None

        self.cam_list.Clear()
        self.release_system()

    def release_system(self) -> None:
        """Releases the PySpin system instance."""
        self.system.ReleaseInstance()

    def unlock_max_framerate(self) -> None:
        """Configures the camera to shoot as fast as possible."""
        if not self.camera:
            return

        try:
            # 1. Turn off Auto-Exposure
            if self.camera.ExposureAuto.GetAccessMode() == PySpin.RW:
                self.camera.ExposureAuto.SetValue(PySpin.ExposureAuto_Off)

            # 2. Set Exposure Time to 1000 microseconds (1 millisecond)
            # This guarantees we have enough time to hit 500+ FPS
            if self.camera.ExposureTime.GetAccessMode() == PySpin.RW:
                exposure_time = min(1000.0, self.camera.ExposureTime.GetMax())
                self.camera.ExposureTime.SetValue(exposure_time)

            # 3. Disable the Frame Rate limit
            if self.camera.AcquisitionFrameRateEnable.GetAccessMode() == PySpin.RW:
                self.camera.AcquisitionFrameRateEnable.SetValue(False)

            # 4. Maximize USB bandwidth limit
            try:
                throughput_node = self.camera.DeviceLinkThroughputLimit
                if throughput_node.GetAccessMode() == PySpin.RW:
                    max_bandwidth = throughput_node.GetMax()
                    throughput_node.SetValue(max_bandwidth)
                    print(f"USB Bandwidth limit maximized to {max_bandwidth} bytes/sec")
            except PySpin.SpinnakerException:
                print("Could not adjust Device Link Throughput.")

            print(f"Exposure set to {self.camera.ExposureTime.GetValue()} us. Framerate unlocked.")

        except PySpin.SpinnakerException as ex:
            print(f"Error unlocking framerate: {ex}")

    def print_camera_info(self) -> None:
        """Prints the model and serial number of the initialized camera."""
        if not self.camera:
            return

        try:
            nodemap_tldevice = self.camera.GetTLDeviceNodeMap()

            # Get vendor name
            vendor_node = PySpin.CStringPtr(nodemap_tldevice.GetNode("DeviceVendorName"))
            vendor = vendor_node.GetValue() if PySpin.IsReadable(vendor_node) else "Unknown Vendor"

            # Get model name
            model_node = PySpin.CStringPtr(nodemap_tldevice.GetNode("DeviceModelName"))
            model = model_node.GetValue() if PySpin.IsReadable(model_node) else "Unknown Model"

            print(f"Camera detected: {vendor} {model}")

        except PySpin.SpinnakerException as ex:
            print(f"Error reading camera info: {ex}")


if __name__ == "__main__":
    cam = Camera()
    cam.print_camera_info()
    cam.unlock_max_framerate()

    # --- CONFIGURATION ---
    test_duration = 5  # Change this to 10 for your 10-second test later
    # ---------------------

    print(f"Starting {test_duration}-second capture stress test...")
    
    # Get current memory usage before capture
    process = psutil.Process(os.getpid())
    mem_before = process.memory_info().rss / (1024 * 1024)  # Convert to MB

    # Run the capture
    start_time = time.perf_counter()
    video_frames = cam.capture_for_duration(test_duration)
    actual_duration = time.perf_counter() - start_time

    # Get memory usage after capture
    mem_after = process.memory_info().rss / (1024 * 1024)  # Convert to MB

    # --- CALCULATE RESULTS ---
    frame_count = len(video_frames)
    fps = frame_count / actual_duration if actual_duration > 0 else 0
    mem_used = mem_after - mem_before

    print("\n" + "="*30)
    print("        TEST RESULTS")
    print("="*30)
    print(f"Target Duration : {test_duration} seconds")
    print(f"Actual Duration : {actual_duration:.3f} seconds")
    print(f"Frames Captured : {frame_count} frames")
    print(f"Actual FPS      : {fps:.2f} FPS")
    print(f"Total RAM Used  : ~{mem_used:.2f} MB")
    
    if frame_count > 0:
        print(f"RAM per Frame   : {(mem_used / frame_count):.2f} MB")
    print("="*30 + "\n")

    cam.release_camera()