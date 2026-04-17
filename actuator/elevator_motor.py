import RPi.GPIO as GPIO
import time

ENABLE_PIN = 17
DIR_PIN = 27
STEP_PIN = 22

def setup_motor() -> None:
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)

    GPIO.setup(ENABLE_PIN, GPIO.OUT)
    GPIO.setup(DIR_PIN, GPIO.OUT)
    GPIO.setup(STEP_PIN, GPIO.OUT)

def motor_test(steps: int, pause_seconds: float) -> None:
    GPIO.output(ENABLE_PIN, GPIO.LOW)

    GPIO.output(DIR_PIN, GPIO.LOW)

    print("Motor test started...")
    time.sleep(1)
    print("Motor rotates one full 360° turn to the left")

    try:
        for _ in range(steps):
            GPIO.output(STEP_PIN, GPIO.HIGH)
            time.sleep(pause_seconds)
            GPIO.output(STEP_PIN, GPIO.LOW)
            time.sleep(pause_seconds)

    except KeyboardInterrupt:
        print("\nTest cancelled by user")

    finally:
        print("Motor test finished")
        GPIO.output(ENABLE_PIN, GPIO.HIGH)
        GPIO.cleanup([STEP_PIN, DIR_PIN])

if __name__ == '__main__':
    setup_motor()

    motor_test(steps=400, pause_seconds=0.002)
