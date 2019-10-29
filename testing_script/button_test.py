import RPi.GPIO as GPIO
import time
#https://sourceforge.net/p/raspberry-gpio-python/wiki/Inputs/

#Using Callback Functions
'''
def button_callback(channel):
    print("Button was pushed")

GPIO.setmode(GPIO.BOARD)
GPIO.setup(10, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

GPIO.add_event_detect(10, GPIO.RISING, callback=button_callback)

message = input("Press enter to quit program\n")

GPIO.cleanup()
'''

#Using event_detection instead of callback function
GPIO.setmode(GPIO.BOARD)
GPIO.setup(10,GPIO.IN,pull_up_down=GPIO.PUD_DOWN)
GPIO.add_event_detect(10,GPIO.RISING)
while True:
    if GPIO.event_detected(10):
        print("Button is pressed")
        time.sleep(6)
    else:
        print("No button pressed")
        time.sleep(6)

