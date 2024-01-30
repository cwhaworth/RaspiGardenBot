import RPi.GPIO as GPIO
import time

#for testing
import keyboard

pin = 27
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)

def startPump():
	GPIO.setup(pin, GPIO.OUT)
#	GPIO.output(pin, 1)
	print("The pump has started. Press any key to stop...\n")
#	While True:
#		if keyboard.is_pressed():
#			GPIO.output(23, False)
#			break
	time.sleep(2)
	GPIO.cleanup(pin)
	print("The pump has stopped")


def main():

#	While True:
#		print("Press any key to start pump, or x to exit...\n")
#		if keyboard.read_key() == "x":
#			break
#		startPump()

	x =  input("Press any key to start pump, or x to exit...")
	x.strip()
	x.lower()
	if x == "x": print("You pressed x")
	else: startPump()

if __name__ == '__main__':
	main()
