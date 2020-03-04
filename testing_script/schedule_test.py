import busio
import adafruit_pcf8523
import time
from board import *

i2c_bus = busio.I2C(SCL, SDA)
rtc = adafruit_pcf8523.PCF8523(i2c_bus)

time = rtc.datetime