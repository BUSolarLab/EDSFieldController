import time
import board
import busio
import adafruit_am2320

#References
#https://github.com/adafruit/Adafruit_CircuitPython_AM2320
#https://learn.adafruit.com/am2315-encased-i2c-temperature-humidity-sensor/python-circuitpython

# create the I2C shared bus
i2c = busio.I2C(board.SCL, board.SDA)
am = adafruit_am2320.AM2320(i2c)

while True:
    print("Temperature: ", am.temperature)
    print("Humidity: ", am.relative_humidity)
    time.sleep(2)