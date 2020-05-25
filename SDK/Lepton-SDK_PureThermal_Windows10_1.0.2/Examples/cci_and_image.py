from import_clr import *

clr.AddReference("ManagedIR16Filters")

from Lepton import CCI
from IR16Filters import IR16Capture, NewIR16FrameEvent, NewBytesFrameEvent

from matplotlib import pyplot as plt
import numpy
import time

lep, = (dev.Open()
        for dev in CCI.GetDevices())

# uncomment the following if running in jupyter
#%matplotlib inline

print(lep.sys.GetCameraUpTime())

# frame callback function
# this will be called everytime a new frame comes in from the camera
numpyArr = None
def getFrameRaw(arr, width, height):
    global numpyArr
    numpyArr = numpy.fromiter(arr, dtype="uint16").reshape(height, width)

# Build an IR16 capture device
capture = IR16Capture()
capture.SetupGraphWithBytesCallback(NewBytesFrameEvent(getFrameRaw))

capture.RunGraph()

while numpyArr is None:
    time.sleep(.1)

try:
    plt.imshow(numpyArr)
    plt.waitforbuttonpress()

finally:
    capture.StopGraph()
    capture.Dispose()