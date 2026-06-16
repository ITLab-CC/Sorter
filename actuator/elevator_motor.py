import RPi.GPIO as GPIO
import time

class ElevatorMotorController:
    """A class to control a stepper motor for an elevator."""
    
    def __init__(self, enable_pin: int = 17, dir_pin: int = 27, step_pin: int = 22):
        self.enable_pin = enable_pin
        self.dir_pin = dir_pin
        self.step_pin = step_pin
        
        # Initialize the hardware within the object
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        # Drive the pins to a safe, defined state immediately. Without an
        # explicit initial value RPi.GPIO leaves outputs LOW, which would pull
        # ENABLE LOW and energise the driver (holding current) the moment this
        # object is created. ENABLE is active-low, so start HIGH (= disabled).
        GPIO.setup(self.enable_pin, GPIO.OUT, initial=GPIO.HIGH)
        GPIO.setup(self.dir_pin, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(self.step_pin, GPIO.OUT, initial=GPIO.LOW)

    def enable(self) -> None:
        """Enables the motor by setting the ENABLE pin to LOW."""
        GPIO.output(self.enable_pin, GPIO.LOW)

    def disable(self) -> None:
        """Disables the motor by setting the ENABLE pin to HIGH."""
        GPIO.output(self.enable_pin, GPIO.HIGH)

    def rotate(self, steps: int, pause_seconds: float, direction_val: int = GPIO.LOW) -> None:
        """Sets the direction and rotates the motor a given number of steps."""
        GPIO.output(self.dir_pin, direction_val)
        
        for _ in range(steps):
            GPIO.output(self.step_pin, GPIO.HIGH)
            time.sleep(pause_seconds)
            GPIO.output(self.step_pin, GPIO.LOW)
            time.sleep(pause_seconds)

    def cleanup(self) -> None:
        """Leave the driver in a safe, defined state on shutdown.

        We deliberately do NOT call ``GPIO.cleanup()`` here: that resets the
        pins to floating inputs, which lets the ENABLE pin drift and the STEP
        pin pick up noise once the program exits, causing the motor to twitch.
        Instead we keep the pins driven: ENABLE HIGH (disabled), STEP/DIR LOW.
        """
        self.disable()
        GPIO.output(self.step_pin, GPIO.LOW)
        GPIO.output(self.dir_pin, GPIO.LOW)


if __name__ == '__main__':
    # 1. Instantiate the controller (uses the default values defined in __init__)
    motor = ElevatorMotorController()
    
    steps = 400
    pause_seconds = 0.002

    print("Motor test started...")
    time.sleep(1)
    print("Motor rotates one full 360° turn to the left")

    try:
        # Enable the hardware
        motor.enable()
        
        # Run the rotation sequence
        motor.rotate(steps=steps, pause_seconds=pause_seconds, direction_val=GPIO.LOW)

    except KeyboardInterrupt:
        print("\nTest cancelled by user")

    finally:
        # Ensure hardware turns off when the script ends or is interrupted
        print("Motor test finished")
        motor.cleanup()