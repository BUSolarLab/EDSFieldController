import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)
GPIO.setup(5,GPIO.OUT)
GPIO.setup(13,GPIO.OUT)

#Green LED
def blink_green()
    GPIO.output(5, 1)
    time.sleep(1)
    GPIO.output(5, 0)

#Red LED
def blink_red()
    GPIO.output(5, 1)
    time.sleep(1)
    GPIO.output(5, 0)

while True:
    blink_green()
    blink_red()