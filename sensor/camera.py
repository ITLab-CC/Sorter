import cv2
import PySpin  # type: ignore
import numpy as np
import time
import psutil
import os
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

    def flush_image_queue(self, timeout_ms: int = 1, max_images: int = 256) -> int:
        """Discard all currently buffered images from the active acquisition stream."""
        if not self.camera:
            return 0

        flushed_count = 0

        while flushed_count < max_images:
            try:
                image_result = self.camera.GetNextImage(timeout_ms)
            except PySpin.SpinnakerException:
                break

            image_result.Release()
            flushed_count += 1

        return flushed_count

    def stream_while_running(self, should_continue):
        """Yields raw frames as fast as possible while *should_continue* is True.

        Args:
            should_continue: A zero-argument callable returning ``True`` while
                streaming should continue and ``False`` to stop. Checked once
                per frame.
        """
        if not self.camera:
            print("Camera not initialized.")
            return

        try:
            # Only keep the most recent frame; the SDK drops older buffered
            # images automatically. This prevents processing stale frames of a
            # marble that has already been classified.
            s_node_map = self.camera.GetTLStreamNodeMap()
            handling_mode = PySpin.CEnumerationPtr(
                s_node_map.GetNode("StreamBufferHandlingMode")
            )
            if PySpin.IsAvailable(handling_mode) and PySpin.IsWritable(handling_mode):
                newest_only = handling_mode.GetEntryByName("NewestOnly")
                handling_mode.SetIntValue(newest_only.GetValue())

            self.camera.BeginAcquisition()

            while should_continue():
                try:
                    # Grab image
                    image_result = self.camera.GetNextImage(1000)

                    if not image_result.IsIncomplete():
                        # Yield the reference directly to save memory.
                        # The caller MUST process it or copy it before the loop continues.
                        yield image_result.GetNDArray()

                    # Release the buffer immediately so the camera can capture the next frame
                    image_result.Release()

                except PySpin.SpinnakerException as ex:
                    print(f"Spinnaker Exception during capture: {ex}")
                    break

        except Exception as e:
            print(f"Error capturing sequence: {e}")

        finally:
            self.camera.EndAcquisition()

    def stream_for_duration(self, duration_sec: int):
        """Yields raw frames sequentially as fast as possible for a set duration."""
        if not self.camera:
            print("Camera not initialized.")
            return

        try:
            # Only keep the most recent frame; the SDK drops older buffered
            # images automatically. This prevents processing stale frames of a
            # marble that has already been classified.
            s_node_map = self.camera.GetTLStreamNodeMap()
            handling_mode = PySpin.CEnumerationPtr(
                s_node_map.GetNode("StreamBufferHandlingMode")
            )
            if PySpin.IsAvailable(handling_mode) and PySpin.IsWritable(handling_mode):
                newest_only = handling_mode.GetEntryByName("NewestOnly")
                handling_mode.SetIntValue(newest_only.GetValue())

            self.camera.BeginAcquisition()

            start_time = time.perf_counter()
            end_time = start_time + duration_sec

            while time.perf_counter() < end_time:
                try:
                    # Grab image
                    image_result = self.camera.GetNextImage(1000)

                    if not image_result.IsIncomplete():
                        # Yield the reference directly to save memory.
                        # The caller MUST process it or copy it before the loop continues.
                        yield image_result.GetNDArray()

                    # Release the buffer immediately so the camera can capture the next frame
                    image_result.Release()

                except PySpin.SpinnakerException as ex:
                    print(f"Spinnaker Exception during capture: {ex}")
                    break

        except Exception as e:
            print(f"Error capturing sequence: {e}")

        finally:
            self.camera.EndAcquisition()

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
            if self.camera.ExposureAuto.GetAccessMode() == PySpin.RW:
                self.camera.ExposureAuto.SetValue(PySpin.ExposureAuto_Off)

            if self.camera.ExposureTime.GetAccessMode() == PySpin.RW:
                exposure_time = min(1000.0, self.camera.ExposureTime.GetMax())
                self.camera.ExposureTime.SetValue(exposure_time)

            if self.camera.AcquisitionFrameRateEnable.GetAccessMode() == PySpin.RW:
                self.camera.AcquisitionFrameRateEnable.SetValue(False)

            try:
                throughput_node = self.camera.DeviceLinkThroughputLimit
                if throughput_node.GetAccessMode() == PySpin.RW:
                    max_bandwidth = throughput_node.GetMax()
                    throughput_node.SetValue(max_bandwidth)
            except PySpin.SpinnakerException:
                pass

            print(f"Exposure set to {self.camera.ExposureTime.GetValue()} us. Framerate unlocked.")

        except PySpin.SpinnakerException as ex:
            print(f"Error unlocking framerate: {ex}")

    def print_camera_info(self) -> None:
        """Prints the model and serial number of the initialized camera."""
        if not self.camera:
            return

        try:
            nodemap_tldevice = self.camera.GetTLDeviceNodeMap()
            vendor_node = PySpin.CStringPtr(nodemap_tldevice.GetNode("DeviceVendorName"))
            vendor = vendor_node.GetValue() if PySpin.IsReadable(vendor_node) else "Unknown Vendor"
            model_node = PySpin.CStringPtr(nodemap_tldevice.GetNode("DeviceModelName"))
            model = model_node.GetValue() if PySpin.IsReadable(model_node) else "Unknown Model"
            print(f"Camera detected: {vendor} {model}")
        except PySpin.SpinnakerException as ex:
            print(f"Error reading camera info: {ex}")


if __name__ == "__main__":
    cam = Camera()
    cam.print_camera_info()
    cam.unlock_max_framerate()

    test_duration = 5

    print(f"Starting {test_duration}-second capture stress test...")
    process = psutil.Process(os.getpid())
    mem_before = process.memory_info().rss / (1024 * 1024)

    start_time = time.perf_counter()
    video_frames = []

    # Updated to consume the generator
    for frame in cam.stream_for_duration(test_duration):
        video_frames.append(frame.copy())

    actual_duration = time.perf_counter() - start_time
    mem_after = process.memory_info().rss / (1024 * 1024)

    frame_count = len(video_frames)
    fps = frame_count / actual_duration if actual_duration > 0 else 0
    mem_used = mem_after - mem_before

    print("\n" + "="*30)
    print("        TEST RESULTS")
    print("="*30)
    print(f"Actual Duration : {actual_duration:.3f} seconds")
    print(f"Frames Captured : {frame_count} frames")
    print(f"Actual FPS      : {fps:.2f} FPS")
    print(f"Total RAM Used  : ~{mem_used:.2f} MB")
    print("="*30 + "\n")

    if frame_count > 0:
        first_frame_rgb = cv2.cvtColor(video_frames[0], cv2.COLOR_BAYER_RG2RGB)
        last_frame_rgb = cv2.cvtColor(video_frames[-1], cv2.COLOR_BAYER_RG2RGB)
        cv2.imwrite("./out/first_frame.png", first_frame_rgb)
        cv2.imwrite("./out/last_frame.png", last_frame_rgb)

    cam.release_camera()