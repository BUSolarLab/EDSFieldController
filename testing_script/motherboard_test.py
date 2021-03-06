import busio
import digitalio
import board
import adafruit_mcp3xxx.mcp3008 as MCP
from adafruit_mcp3xxx.analog_in import AnalogIn
import RPi.GPIO as GPIO
import time

'''Normally Open (relay LED off) is when GPIO.IN, normally closed (relay LED on) is when GPIO.OUT'''
#This script shows the accuracy of the motherboard's circuit for voc and isc measurements

# change this depending on the actual voltage and current values from the power supply
actual_voc = 3
actual_isc = 0.3

# run measurement 5 times, make power supply connected to EDS panel 1
for x in range(5):

    print("------------------------------")
    print("Trial " + str(x))
    print("------------------------------")
    # Reset ports
    GPIO.setup(7,GPIO.IN)
    GPIO.setup(25,GPIO.IN)

    # Set the ports, 
    GPIO.setup(7, GPIO.OUT)

    # Measure Isc
    GPIO.setup(25, GPIO.OUT)
    #create the spi bus
    spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)
    #create the cs (chip select)
    cs = digitalio.DigitalInOut(board.D18)
    #create the mcp object
    mcp = MCP.MCP3008(spi,cs)
    #create an analog input channel on pin 0
    chan = AnalogIn(mcp, MCP.P0)
    #correction constant
    correction_isc = 1.5927#1.5674(M1), 1.5927(M2)
    print("Isc")
    print('Raw ADC Value: ', chan.value)
    print('ADC Voltage: ' + str(chan.voltage) + 'V')
    print('Isc Ampere: ' + str(chan.voltage*correction_isc) + 'A')

    #Delay
    time.sleep(5)

    # Measure Voc
    GPIO.setup(25, GPIO.IN)
    #create the spi bus
    spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)
    #create the cs (chip select)
    cs = digitalio.DigitalInOut(board.D18)
    #create the mcp object
    mcp = MCP.MCP3008(spi,cs)
    #create an analog input channel on pin 0
    chan = AnalogIn(mcp, MCP.P0)
    #correction constant
    correction_voc = 1.7369#1.0520(M1), 1.7369(M2)

    print("Voc")
    print('Raw ADC Value: ', chan.value)
    print('ADC Voltage: ' + str(chan.voltage) + 'V')
    print('Voc Voltage: ' + str(chan.voltage*11*correction_voc) + 'V')

    time.sleep(5) 

    #Reset port
    GPIO.setup(7, GPIO.IN)
    GPIO.setup(25, GPIO.IN)