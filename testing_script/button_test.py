import RPi.GPIO as GPIO
import time
#https://sourceforge.net/p/raspberry-gpio-python/wiki/Inputs/

#Using Callback Functions To Detect Button Being Pressed
'''
def button_callback(channel):
    print("Button was pushed")

GPIO.setmode(GPIO.BOARD)
GPIO.setup(10, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

GPIO.add_event_detect(10, GPIO.RISING, callback=button_callback)

message = input("Press enter to quit program\n")

GPIO.cleanup()
'''
#button wired to pin 22
#Using event_detection (current method for the FTU code)
GPIO.setmode(GPIO.BCM)
GPIO.setup(22, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

while True:
    time.sleep(0.2)
    input_state  = GPIO.input(22)
    if input_state == True:
        print('Button pressed')
