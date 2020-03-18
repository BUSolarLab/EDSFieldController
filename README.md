# EDSFieldController

## Overview

To assess the effectiveness of the Field Test Unit (FTU), the setup needs to gather data from the EDS panels (panel with EDS film) and the CTRL panels (panel without EDS panels). This repository holds the main Python scripts which is run on the FTU's RasPi (Raspberry Pi). 

The FTU measures the following parameters:
- Temperature [C°]
- Humidity [%]
- Voc = Open Circuit Voltage [V] 
- Isc = Short Circuit Current [A]

Based on those parameters, the RasPi computes the following files and saves it on a USB drive:
- Pout = Output Power [W]
- GPOA = Global Plane of Array Irradiance [W/m2]
- PR = Performance Ratio [%]
- SR = Soiling Ratio [%]

## FTU Setup Schematic
<p float="left">
    <img src="https://user-images.githubusercontent.com/33497234/76996891-b553d580-6928-11ea-8ec8-de90fe6a72b1.jpg" width="300" height="300">
    <img src="https://user-images.githubusercontent.com/33497234/76996910-bdac1080-6928-11ea-9835-4e7ae0e19d08.jpg" width="500" height="300">
</p>

## Flow Chart

<p align="center">
  <img src="https://user-images.githubusercontent.com/33497234/76996930-c56bb500-6928-11ea-8f8e-161ea652110e.png">
</p>

## Getting Started

1. Clone the github repository
```
git clone https://github.com/BUSolarLab/EDSFieldController
```
2. Install Dependancies From Bash Script
```
chmod +x eds_setup.sh
sudo ./eds_setup
```
3. Setup systemctl so code will run on boot
```
Explanation coming soon
```

## Notes
- Instructions assume Raspbian is already downloaded and installed on the RasPi
- Enable SPI and I2C to use the sensors
- Enable VNC and SSH for ease in testing

## Authors
- Ben Constantine
- Brian Mahabir
- Aditya Wikara
