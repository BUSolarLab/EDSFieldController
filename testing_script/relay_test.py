import RPi.GPIO as GPIO
import time

'''
Test 1
1. Switch to normally closed by setting GPIO ports to output (3.3V), which is considered as LOW logic to relay
2. Switch to normally open (LEDS off) by setting GPIO ports to input (~4V from the relay)
'''
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
# Change to 0,1 for low high
pinList = [4,17,6,19,26,27,25,23,15,20,16,12,8,7]

for i in pinList:
    GPIO.setup(i,GPIO.OUT)

try:
    #LED ON
    for i in pinList:
        GPIO.setup(i,GPIO.IN)
        time.sleep(0.5)
    #LED OFF
    for i in pinList:
        GPIO.setup(i,GPIO.OUT)
        time.sleep(0.5)
except KeyboardInterrupt:
    GPIO.cleanup()

'''
Test 2
Switch the relays to normally closed individually by adjusting logic from HIGH to LOW
Doesn't seem to work because relay needs 5V logic.
The threshold is around 3.8V which makes is normally open, anything below will switch it to normally closed
'''
'''
GPIO.setmode(GPIO.BCM)

pinList = [4,17,6,19,26,27,25,23,15,20,16,12,8,7]

#LED ON
for i in pinList:
    GPIO.setup(i,GPIO.OUT)

try:
    #EDS PANELS    
    GPIO.output(4,0)
    print("EDS1")
    time.sleep(2)
    GPIO.output(17,0)
    print("EDS2")
    time.sleep(2)
    GPIO.output(6,1)
    print("EDS3")
    time.sleep(2)
    GPIO.output(19,1)
    print("EDS4")
    time.sleep(2)
    GPIO.output(26,1)
    print("EDS5")
    time.sleep(2)
    #SCC/OCV
    GPIO.output(25,1)
    print("SCC/OCV")
    time.sleep(2)
    #EDSPV
    GPIO.output(23,0)
    print("EDSPV1")
    time.sleep(2)
    GPIO.output(15,0)
    print("EDSPV2")
    time.sleep(2)
    GPIO.output(20,0)
    print("EDSPV3")
    time.sleep(2)
    GPIO.output(16,0)
    print("EDSPV4")
    time.sleep(2)
    GPIO.output(12,0)
    print("EDSPV5")
    time.sleep(2)
    #CTRL PV
    GPIO.output(8,0)
    print("CTRL1")
    time.sleep(2)
    GPIO.output(7,0)
    print("CTRL2")
    time.sleep(2)
    GPIO.cleanup()
    
except KeyboardInterrupt:
    GPIO.cleanup()
'''