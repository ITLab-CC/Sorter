# utils/FLIR.py

import PySpin

class FlirBFS:
    def __init__(self, on_new_frame, display=False, frame_rate=30):
        self.on_new_frame = on_new_frame
        self.display = display
        self.frame_rate = frame_rate
        self.system = PySpin.System.GetInstance()
        self.cam_list = self.system.GetCameras()
        self.cam = self.cam_list[0] if self.cam_list.GetSize() > 0 else None

    def run_cam(self):
        if not self.cam:
            print("No FLIR camera detected.")
            return
        
        self.cam.Init()
        self.cam.AcquisitionMode.SetValue(PySpin.AcquisitionMode_Continuous)
        self.cam.BeginAcquisition()

        while True:
            try:
                image = self.cam.GetNextImage()
                if image.IsIncomplete():
                    print("Image incomplete with image status %d ..." % image.GetImageStatus())
                    continue
                
                frame = image.GetNDArray()
                self.on_new_frame(frame)
                
                if self.display:
                    cv2.imshow("FLIR Camera", frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
            except PySpin.SpinnakerException as ex:
                print("Error: %s" % ex)
                break

        self.cam.EndAcquisition()
        self.cam.DeInit()
        del self.cam
        self.cam_list.Clear()
        self.system.ReleaseInstance()
        cv2.destroyAllWindows()
