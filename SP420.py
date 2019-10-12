'''
=============================
Title: Pyranometer Module - EDS Field Control
Author: Aditya Wikara
Started: September 2019
=============================
'''

from serial import Serial,SerialException
from time import sleep
import struct

#Commands to the SP420 Sensor
GET_VOLT = bytes([0x55, 0x21])          #'\x55!'.encode()
READ_CALIBRATION = bytes([0x83, 0x21])  #'\x83!'.encode()
SET_CALIBRATION = bytes([0x84])         #'\x84%s%s!'
READ_SERIAL_NUM = bytes([0x87, 0x21])    #'\x87!'
GET_LOGGING_COUNT = bytes([0xf3, 0x21])  #'\xf3!'
GET_LOGGED_ENTRY = bytes([0xf2])        #'\xf2%s!'
ERASE_LOGGED_DATA = bytes([0xf4, 0x21])  #'\xf4!'

class Irradiance(object):
    
    def __init__(self):
        """Initializes class variables, and attempts to connect to device"""
        self.apogee = None
        self.offset = 0.0
        self.multiplier = 0.0
        self.connect_to_device()

    def connect_to_device(self):
        """This function creates a Serial connection with the defined comport and attempts to read the calibration values"""
        #Error checking the ports
        try:
            port = '/dev/ttyACM0' # you'll have to check your device manager and put the actual com port here
            self.apogee = Serial(port, 115200, timeout=0.5)
        
        except SerialException:
            if (port == '/dev/ttyACM0'):
                port = '/dev/tty.usbmodem14201' #NEW PORT NAME
                self.apogee = Serial(port, 115200, timeout=0.5)
            else:
                #No Pyranometer Found
                self.apogee = None

        #Get the constants involved for measuring irradiance
        try:
            self.apogee.write(READ_CALIBRATION)
            multiplier = self.apogee.read(5)[1:]
            offset = self.apogee.read(4)
            self.multiplier = struct.unpack('<f', multiplier)[0]
            self.offset = struct.unpack('<f', offset)[0]

        except IOError:
            print("ERROR")
            self.apogee = None
            
        except AttributeError:
            print("No Pyranometer Found!")
    
    def get_irradiance(self):
        """This function converts the voltage to irradiance"""
        if (self.apogee == None):
            return -1
        
        #Measure voltage from the pyranometer
        voltage = self.read_voltage()

        if voltage == 9999:
            # you could raise some sort of Exception here if you wanted to
            return -1

        irradiance = ((voltage *1000) - self.offset) * self.multiplier
        #print("Raw Voltage: " + str(voltage))
        #print("Offest: " + str(self.offset))
        #print("Multiplier: " + str(self.multiplier))
        #print(irradiance)

        #Error check, irradiance cannot be negative
        if irradiance < 0:
            irradiance = 0
        
        return round(irradiance,3)

    def read_voltage(self):
        """This function averages 5 readings over 1 second and returns the result."""
        if self.apogee == None:
            try:
                self.connect_to_device()
            except IOError:
                # you can raise some sort of exception here if you need to
                return None
        # store the responses to average
        response_list = []
        # change to average more or less samples over the given time period
        number_to_average = 10
        # change to shorten or extend the time duration for each measurement
        # be sure to leave as floating point to avoid truncation
        number_of_seconds = 1.0

        for i in range(number_to_average):
            try:
                self.apogee.write(GET_VOLT)
                response = self.apogee.read(5)[1:]
            except IOError:
                print("There is an input/output error")
                # exception here alternatively
                return 9999
            else:
                if not response:
                    continue
                # if the response is not 4 bytes long, this line will raise
                # an exception
                voltage = struct.unpack('<f', response)[0]
                response_list.append(voltage)
                sleep(number_of_seconds/number_to_average)

        #Calculate the average of the readings
        if response_list:
            return sum(response_list)/len(response_list)
        return 0.0

    def read_and_print_calibration(self):
        self.apogee.write(READ_CALIBRATION)
        multiplier = self.apogee.read(5)[1:]
        offset = self.apogee.read(4)
        self.multiplier = struct.unpack('<f', multiplier)[0]
        self.offset = struct.unpack('<f', offset)[0]
        bytestring = ''.join('%02x'%byte for byte in multiplier)
        print("Multiplier: " + str(self.multiplier) + '\n')
        print("Bytes of Multiplier: " + bytestring + '\n')
        bytestring = ''.join('%02x'%byte for byte in offset)
        print("Offset: " + str(self.offset) + '\n')
        print("Bytes of Offset: " + bytestring + '\n')
        sleep(2.0)
        print("------------------------------------------")

#sample = Irradiance()
#x = sample.get_irradiance()
#print("Irradiance: " + str(x) + " W/m2")
#while True:
    #sample.read_and_print_calibration()