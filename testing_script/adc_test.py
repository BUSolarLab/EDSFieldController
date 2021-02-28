import busio
import digitalio
import board
import adafruit_mcp3xxx.mcp3008 as MCP
from adafruit_mcp3xxx.analog_in import AnalogIn
import RPi.GPIO as GPIO
import time

# Note: To switch the relay ports, we need to vary GPIO.IN and GPIO.OUT.
# GPIO.IN will switch the relay off, GPIO.OUT will switch the relay on.

# Setup the board
GPIO.setmode(GPIO.BCM)

# Reset Ports to Off. GPIO
GPIO.setup(7,GPIO.IN)
GPIO.setup(25,GPIO.IN)

# Set the ports, this will measure PV1 
GPIO.setup(7, GPIO.OUT)

# Measure Isc, since adc relay port is pin 25
GPIO.setup(25, GPIO.OUT)
time.sleep(3)
#create the spi bus
spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)
#create the cs (chip select)
cs = digitalio.DigitalInOut(board.D18)
#create the mcp object
mcp = MCP.MCP3008(spi,cs)
#create an analog input channel on pin 0
chan = AnalogIn(mcp, MCP.P0)
time.sleep(3)
print("Isc")
print('Raw ADC Value: ', chan.value)
print('ADC Voltage: ' + str(chan.voltage) + 'V')
print('Isc Ampere: ' + str(chan.voltage*1.4517) + 'A')

#Delay
time.sleep(3)

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
time.sleep(3)
print("Voc")
print('Raw ADC Value: ', chan.value)
print('ADC Voltage: ' + str(chan.voltage) + 'V')
print('Voc Voltage: ' + str(chan.voltage*6.6* 1.247213) + 'V')

#Reset Ports
GPIO.setup(7, GPIO.IN)
GPIO.setup(25, GPIO.IN)