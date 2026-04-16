import RPi.GPIO as GPIO
import time

ENABLE_PIN = 17
DIR_PIN = 27
STEP_PIN = 22

def setup_motor():
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)

    GPIO.setup(ENABLE_PIN, GPIO.OUT)
    GPIO.setup(DIR_PIN, GPIO.OUT)
    GPIO.setup(STEP_PIN, GPIO.OUT)

def motor_test(schritte, pause_sekunden):
    GPIO.output(ENABLE_PIN, GPIO.LOW)

    GPIO.output(DIR_PIN, GPIO.LOW)

    print("Motor Test gestartet...")
    time.sleep(1)
    print("Motor dreht 1x 360° nach links")

    try:
        for _ in range(schritte):
            GPIO.output(STEP_PIN, GPIO.HIGH)
            time.sleep(pause_sekunden)
            GPIO.output(STEP_PIN, GPIO.LOW)
            time.sleep(pause_sekunden)

    except KeyboardInterrupt:
        print("\nTest durch Nutzer abgebrochen")

    finally:
        print("Motor Test beendet")
        GPIO.output(ENABLE_PIN, GPIO.HIGH)
        GPIO.cleanup([STEP_PIN, DIR_PIN])

if __name__ == '__main__':
    setup_motor()

    motor_test(schritte=400, pause_sekunden=0.002)
