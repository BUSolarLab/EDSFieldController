import busio
import digitalio
import board
import adafruit_mcp3xxx.mcp3008 as MCP
from adafruit_mcp3xxx.analog_in import AnalogIn
import RPi.GPIO as GPIO
import time

#This script shows the accuracy of the motherboard's circuit for voc and isc measurements
actual_voc = 3
actual_isc = 0.3
for x in range(5):

    print("------------------------------")
    print("Trial " + str(x))
    print("------------------------------")
    # Reset ports
    GPIO.setup(8,GPIO.IN)
    GPIO.setup(15,GPIO.IN)

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
    print("Isc")
    print('Raw ADC Value: ', chan.value)
    print('ADC Voltage: ' + str(chan.voltage) + 'V')
    print('Isc Ampere: ' + str(chan.voltage) + 'A')

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
    print("Voc")
    print('Raw ADC Value: ', chan.value)
    print('ADC Voltage: ' + str(chan.voltage) + 'V')
    print('Voc Voltage: ' + str(chan.voltage*11) + 'V')

    time.sleep(5) 
    
    #Reset port
    GPIO.setup(7, GPIO.IN)
    GPIO.setup(25, GPIO.IN)