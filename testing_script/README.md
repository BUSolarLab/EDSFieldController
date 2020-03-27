## Field Test Unit Testing Scripts

### Overview

The following directory contains scripts which tests key features of the field test unit, which involve the following functionalities:

- Manual button test
- ADC measurement test
- RTC setup
- RTC durability test
- Motherboard test
- Relay board test
- Temperature humidity sensor test
- FTU LED test
- Solar noon test
- Systemd
- WPA wifi

### Detailed Notes

_Manual Button Test_

The script is called button_test.py. The script setups the GPIO board and pin for the RasPi. It then runs a while loop to see if the button is being pressed, if it is, then it will print a message on the command line.

_ADC Measurement Test_

The script is called adc_test.py. The script will measure the Isc (short circuit current) and Voc (open circuit voltage) of EDS panel 1. Please make sure the hardware connections are correct.

_RTC Setup_

The script is called rtc_test.py. The script allows you to reset the RTC time if a malfunction occurs, as well as getting the current time from the RTcC.

_RTC Durability Test_

The script is called durability_rtc_test.py. Since the RTC had random malfunctions with the FTU, we want to test its durability. This script does that.

_Motherboard Test_

The script is called motherboard_test.py. We realized that ADC measurements differ for each motherboard, so a correction coefficient is required for each motherboard during ADC measurement. This applies for voltage and current measurements. 5 tests are made for each motherboard and an average correction coefficient is calculated. So far, we have done this for 2 motherboards, and these are the results:

Voltage:
- 1.0520(M1)
- 1.7369(M2)

Current:
- 1.5674(M1)
- 1.5927(M2)

These correction coefficients are found in TestingManager.py in the main directory, specifically in the ADCMaster class.

_Relay Board Test_

The script is called relay_test.py. The script allows us to check if the relay board ports are able to switch by command. It will switch all the relay ports on and off sequentially, this is shown by each ports's LED indicator.

_Temperature Humidity Sensor Test_

The script is called temp_humid_test.py. This script is the same as AM2315.py from the main directory. It will communicate with the AM2315 sensor and measure the current temperature and humidity. If not, it will output 'Error', which indicate an hardware error.

_FTU LED Test_

The script is called led_test.py. The FTU electronic enclosure box has gree and red LEDs which are important indicators for the FTU's operation.

_Solar Noon Test_

The script is called noon_test.py. One of the functionalities of the FTU is to be able to take measurements during solar noon, which is the time during the day with the highest peak irradiance. This time varies based on the latitude of the location. This script tests whether the RasPi will do a desired action during solar noon time.

_Reset EDS Json File_

This script is called reset_eds_json.py. This script can be run after changing the FTU schedule. This is because to make sure there are no bugs, we need to set is_activated to all false, and set all the record_dt to the current rtc. This can be done by running this script.

_Systemd_

To allow scripts to run continuously when the RasPi boots, we need to create a systemd service file. There is more documentation on this. But, the file systemd_sample.txt is a sample format for the service file.

_WPA Wifi_

To allow the RasPi to connect to the BU wifi, we need to manually add a WPA supplicant. This is not crucial to the FTU, but is very useful to VNC remotely. The file wifi_setup_wpa.txt is a format for it.
