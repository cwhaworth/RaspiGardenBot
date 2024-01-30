  
import RPi.GPIO as GPIO
pin = 17
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(pin, GPIO.OUT)
GPIO.cleanup(pin)
print("Pump off")
