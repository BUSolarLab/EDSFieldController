# EDSFieldController

> I will update this with more detail shortly.

Please follow these steps to set up a brand new Raspberry Pi 3 B+

1. Download and install Raspbian on the RPi
2. Download and run eds_setup.sh (click 'raw' then right-click 'Save As', then open terminal and use 'chmod +x eds_setup.sh' then 'sudo ./eds_setup.sh' (you will have to type 'y' as a prompt at some point during the installation)
3. Enable SPI and I2C, and set to boot into CLI (command line interface) instead of the desktop
4. Reboot system 'sudo reboot'
5. Open MasterManager.py and uncomment line 60, filling in the appropriate time variables for the eventual location of test unit (this initiates the RTC for a certain time that it will maintain)
6. Run MasterManager.py once to make sure everything works
7. Recomment line 60 so that it does not reset time again
8. Change config.json file to location and setup specifications
9. Add the following line above 'exit 0' in /etc/rc.local (must use root access to edit file 'sudo nano /etc/rc.local'):
> (sleep 15; sudo python3 /home/pi/EDSPython/MasterManager.py)&

*This is how the code will start automatically on boot. 'sleep 15' is there to create a window for entering the RPi desktop before the code executes.*

10. RPi is now ready for automated function. The code will begin automatically on boot. From now on, if you want to enter the desktop environment on this RPi you can type 'startx' in the command line during the 15 second pause before the MasterManager.py code is run.
