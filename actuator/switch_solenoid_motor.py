from gpiozero import OutputDevice
from time import sleep

class SolenoidController:
    """A class to control a solenoid valve or actuator."""
    
    def __init__(self, pin: int = 16):
        self.pin = pin
        
        # Initialize the hardware within the object
        self.solenoid = OutputDevice(self.pin)

    def turn_on(self) -> None:
        """Activates the solenoid."""
        self.solenoid.on()

    def turn_off(self) -> None:
        """Deactivates the solenoid."""
        self.solenoid.off()

if __name__ == "__main__":
    # 1. Instantiate the controller (uses the default values defined in __init__)
    my_solenoid = SolenoidController()
    
    """Runs a test sequence, turning the solenoid on and off at set intervals."""
    # Test intervals in seconds
    intervals = [1.0, 1.0, 0.5, 0.5, 0.1, 0.1]

    try:
        print(f"Solenoid test started on GPIO pin {my_solenoid.pin}...")
        sleep(1)

        for duration in intervals:
            print(f"Solenoid ON ({duration}s)")
            my_solenoid.turn_on()
            sleep(duration)

            print("Solenoid OFF")
            my_solenoid.turn_off()
            sleep(duration)

    except KeyboardInterrupt:
        print("\nTest cancelled by user")
        
    finally:
        # Cleanup so the solenoid safely turns off when the script ends
        my_solenoid.turn_off()
        print("Solenoid test finished and pin safely disabled")