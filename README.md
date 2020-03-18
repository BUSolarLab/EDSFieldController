# EDSFieldController

## Overview

To assess the effectiveness of the Field Test Unit (FTU), the setup needs to gather data from the EDS panels (panel with EDS film) and the CTRL panels (panel without EDS panels). This repository holds the main Python scripts which is run on the FTU's Raspberry Pi. In general, the FTU measures the following parameters:
- Voc (Open Circuit Voltage)
- Isc (Short Circuit Current)
- Pout (Output Power)
- 

## Flow Chart/Block Diagram



## Getting Started

1. Clone the github repository
```
git clone https://github.com/BUSolarLab/EDSFieldController
```
2. Install Dependancies
```
python -m pip install --upgrade pip
```
```
pip install -r requirements.txt
```
3. Run the desired script
For Windows:
```
python eds_analysis_windows.py
```
For Mac:
```
python eds_analysis_ios.py
```

## Instructions

> I will update this with more detail shortly.

Please follow these steps to set up a brand new Raspberry Pi 3 B+

1. Download and install Raspbian on the RPi
2. Download and run eds_setup.sh (click 'raw' then right-click 'Save As', then open terminal and use 'chmod +x eds_setup.sh' then 'sudo ./eds_setup.sh' (you will have to type 'y' as a prompt at some point during the installation)
3. Enable SPI and I2C, and set to boot into CLI (command line interface) instead of the desktop
4. Reboot system 'sudo reboot'
5. Run MasterManager.py once to make sure everything works
6. Change config.json file to location and setup specifications
> (sleep 15; sudo python3 /home/pi/EDSPython/MasterManager.py)&

*This is how the code will start automatically on boot. 'sleep 15' is there to create a window for entering the RPi desktop before the code executes.*

9. RPi is now ready for automated function. The code will begin automatically on boot. From now on, if you want to enter the desktop environment on this RPi you can type 'startx' in the command line during the 15 second pause before the MasterManager.py code is run.

## Notes