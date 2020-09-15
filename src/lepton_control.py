from import_clr import *
clr.AddReference("ManagedIR16Filters")
from Lepton import CCI
from IR16Filters import IR16Capture, NewIR16FrameEvent, NewBytesFrameEvent
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
        # print(self.lep.oem.GetSoftwareVersion())
        # print("Camera Up Time: {}".format(self.lep.sys.GetCameraUpTime()))

        # Run a FFC. If this command executes successfully, the shutter on the lepton should close and open.
        self.lep.sys.RunFFCNormalization()

        # Get the current palette (**Pseudo-color** L*ook *Up Table)
        # lep.vid.GetPcolorLut()
        # lep.sys.SetGainMode(CCI.Sys.GainMode.LOW)
        # lep.vid.SetPcolorLut(3)
        # print(self.lep.sys.GetFpaTemperatureKelvin())

        try:
            self.lep.rad.SetTLinearEnableStateChecked(True)
            print("This lepton supports tlinear")
            self.tlinear = True
        except:
            print("This lepton does not support tlinear")
            self.tlinear = False

        # Start streaming
        self.capture = None
        # change maxlen to control the number of frames of history we want to keep
        self.incoming_frames = deque(maxlen=10)
        if self.capture is not None:
            # don't recreate capture if we already made one
            self.capture.RunGraph()
        else:
            self.capture = IR16Capture()
            self.capture.SetupGraphWithBytesCallback(NewBytesFrameEvent(self.__got_a_frame))
            self.capture.RunGraph()
        while len(self.incoming_frames) == 0:
            time.sleep(.1)

    def update_frame(self, rotate=0, flip=0, coef=0.05, offset=0.0):
        height, width, net_array = self.incoming_frames[-1]
        raw = self.short_array_to_numpy(height, width, net_array)

        if rotate == 0 and flip:
            raw = np.flip(raw, 1)
        elif rotate == 1 and not flip:
            raw = np.flip(np.transpose(raw, (1, 0)), 1)
        elif rotate == 1 and flip:
            raw = np.flip(np.flip(np.transpose(raw, (1, 0)), 0), 1)
        elif rotate == 2 and not flip:
            raw = np.flip(np.flip(raw, 0), 1)
        elif rotate == 2 and flip:
            raw = np.flip(raw, 0)
        elif rotate == 3 and not flip:
            raw = np.flip(np.transpose(raw, (1, 0)), 0)
        elif rotate == 3 and flip:
            raw = np.transpose(raw, (1, 0))

        # print("debug", coef, offset)
        if self.tlinear:
            # Lepton 3.5 (with radiometric accuracy)
            # raw is in centikelvin
            temp = (raw - 27315) / 100 + offset
        else:
            # Lepton 3.0 (without radiometric accuracy), need to calibrate the coefficient(COEF)
            # raw is in raw value
            # celsius = (raw_data - 8192) * coefficient / 100 + camera_temperature
            temp = (np.float64(raw) - 8192) * coef + offset + self.camera_temp()

        return raw, temp

    # return in celsius
    def camera_temp(self):
        # note self.lep.sys.GetFpaTemperatureKelvin() is in centi_kelvin
        # convert it in celsius by (value - 27315) / 100
        return (self.lep.sys.GetFpaTemperatureKelvin() - 27315) / 100

    def run_ffc(self):
        self.lep.sys.RunFFCNormalization()

    def stop_streaming(self):
        print("Stop streaming")
        self.capture.StopGraph()
        self.capture.Dispose()

    def __got_a_frame(self, short_array, width, height):
        self.incoming_frames.append((height, width, short_array))

    @staticmethod
    def short_array_to_numpy(height, width, frame):
        return np.fromiter(frame, dtype="uint16").reshape(height, width)
