asminfo = NET.addAssembly(pwd + "\..\x64\Release\LeptonUVC.dll");

%%

devs = Lepton.CCI.GetDevices();
lepton = devs.Item(0).Open();

%%

uptime = lepton.sys.GetCameraUpTime()

%%

softwareVersion = lepton.oem.GetSoftwareVersion()

%%

LUTGreenPixel = lepton.vid.GetUserLut.bin(1).green

%% 
% This is an example of how to create a value to pass
% into the SDK, note that since we're using inner classes
% (with the "+" in the name) we have to use 
% `System.Activator.CreateInstance` to create instances
% sorry that matlab makes this so complicated 

args = NET.createArray("System.Object", 4);

args(1) = uint8(0);   % reserved
args(2) = uint8(255); % red
args(3) = uint8(255); % green
args(4) = uint8(0);   % blue

t = asminfo.AssemblyHandle.GetType('Lepton.CCI+Vid+LutPixel');
System.Activator.CreateInstance(t, args)

%%
t = asminfo.AssemblyHandle.GetType('Lepton.CCI+Sys+FfcShutterMode');

MANUAL = t.GetEnumValues().Get(0);
AUTO = t.GetEnumValues().Get(1);
EXTERNAL = t.GetEnumValues().Get(2);

shutterObj = lepton.sys.GetFfcShutterModeObj;
shutterObj.shutterMode = MANUAL;
lepton.sys.SetFfcShutterModeObj(shutterObj);
lepton.sys.GetFfcShutterModeObj
