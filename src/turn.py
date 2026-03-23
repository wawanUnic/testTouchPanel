import RPi.GPIO as GPIO
import sys
import time

GPIO.setmode(GPIO.BCM)

PIN1 = 18
PIN2 = 23

GPIO.setup(PIN1, GPIO.OUT)
GPIO.setup(PIN2, GPIO.OUT)

if len(sys.argv) != 2:
    print("Usage: python3 turn.py on|off")
    GPIO.cleanup()
    sys.exit(1)

command = sys.argv[1].lower()

if command == "off":
    print("Turning PIN1 and PIN2 ON")
    GPIO.output(PIN1, GPIO.HIGH)
    GPIO.output(PIN2, GPIO.HIGH)
elif command == "on":
    print("Turning PIN1 and PIN2 OFF")
    GPIO.output(PIN1, GPIO.LOW)
    GPIO.output(PIN2, GPIO.LOW)
else:
    print("Unknown command. Use: on or off")
    GPIO.cleanup()
    sys.exit(1)

print("Running... Press Ctrl+C to exit")

try:
    while True:
        time.sleep(1)

except KeyboardInterrupt:
    print("\nStopping and resetting pins...")
    GPIO.output(PIN1, GPIO.LOW)
    GPIO.output(PIN2, GPIO.LOW)
    GPIO.cleanup()
    print("GPIO cleaned up. Exiting.")
