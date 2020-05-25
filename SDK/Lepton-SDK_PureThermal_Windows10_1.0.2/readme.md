# Lepton CCI SDK

Getting started with Python

1. Install the dependencies:

		pip install pythonnet numpy matplotlib

2. Connect a purethermal board to your PC
3. Make sure to unblock the SDK dlls:
    * Navigate to x64 or x86 depending on if you have 64 bit (x64) or 32 bit (x86) python
    * Right click on LeptonUVC.dll and select Properties
    * In the general tab there may be a section called "Security" at the bottom. If there is, check "Unblock" and hit apply. 
    * Repeat for ManagedIR16Filters.dll
4. Install the appropriate redistributable
    * 64 bit for 64 bit python, 32 bit for 32 bit Python
5. Run an example script

		python Examples\test_connection.py

	If the command executes successfully you'll see the camera's uptime and serial 
	number information.

6. Or snap a frame:

		python Examples\cci_and_image.py
