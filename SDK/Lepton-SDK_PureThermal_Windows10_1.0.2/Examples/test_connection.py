from import_clr import *
from Lepton import CCI

print("SDK Version", CCI.SDKVersion)

lep, = (dev.Open()
        for dev in CCI.GetDevices())

print("uptime", lep.sys.GetCameraUpTime())
software_version = lep.oem.GetSoftwareVersion()
print("software version", software_version)
print("gpp_major", software_version.gpp_major)
print("gpp_minor", software_version.gpp_minor)
print("gpp_build", software_version.gpp_build)


