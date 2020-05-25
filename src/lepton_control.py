from import_clr import *
clr.AddReference("ManagedIR16Filters")
from Lepton import CCI
from IR16Filters import IR16Capture, NewIR16FrameEvent, NewBytesFrameEvent
# from matplotlib import pyplot as plt
# from matplotlib import cm
import numpy as np
import time
from collections import deque

class Lepton:

    def __init__(self):
        # Find device
        found_device = None
        for device in CCI.GetDevices():
            if device.Name.startswith("PureThermal"):
                print(device.Name)
                found_device = device
                break
        if not found_device:
            print("Couldn't find lepton device")
        else:
            self.lep = found_device.Open()

        # Get the current camera uptime
        print(self.lep.oem.GetSoftwareVersion())
        print("Camera Up Time: {}".format(self.lep.sys.GetCameraUpTime()))

        # Run a FFC. If this command executes successfully, the shutter on the lepton should close and open.
        self.lep.sys.RunFFCNormalization()

        # Get the current palette (P**seudo-color** L*ook *Up Table)
        # lep.vid.GetPcolorLut()
        # lep.sys.SetGainMode(CCI.Sys.GainMode.LOW)
        # lep.vid.SetPcolorLut(3)

        try:
            self.lep.rad.SetTLinearEnableStateChecked(True)
            print("This lepton supports tlinear")
        except:
            print("This lepton does not support tlinear")

        # Start streaming
        self.capture = None
        # change maxlen to control the number of frames of history we want to keep
        self.incoming_frames = deque(maxlen=10)
        if self.capture != None:
            # don't recreate capture if we already made one
            self.capture.RunGraph()
        else:
            self.capture = IR16Capture()
            self.capture.SetupGraphWithBytesCallback(NewBytesFrameEvent(self.__got_a_frame))
            self.capture.RunGraph()
        while len(self.incoming_frames) == 0:
            time.sleep(.1)

    def update_frame(self):
        height, width, net_array = self.incoming_frames[-1]
        arr = self.short_array_to_numpy(height, width, net_array)
        return arr

    def stop_streaming(self):
        print("Stop streaming")
        self.capture.StopGraph()
        self.capture.Dispose()

    def __got_a_frame(self, short_array, width, height):
        self.incoming_frames.append((height, width, short_array))


    @staticmethod
    def short_array_to_numpy(height, width, frame):
        return np.fromiter(frame, dtype="uint16").reshape(height, width)



# while True:


if __name__ == "__main__":
    pass