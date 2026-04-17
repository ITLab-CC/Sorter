from gpiozero import OutputDevice
from time import sleep

# Pin configuration
SOLENOID_PIN = 16
solenoid = OutputDevice(SOLENOID_PIN)

def solenoid_test() -> None:
    # Test intervals in seconds
    intervals = [1.0, 1.0, 0.5, 0.5, 0.1, 0.1]

    try:
        print(f"Solenoid test started on GPIO pin {SOLENOID_PIN}...")
        sleep(1)

        for duration in intervals:
            print(f"Solenoid ON ({duration}s)")
            solenoid.on()
            sleep(duration)

            solenoid.off()
            print("Solenoid OFF")
            sleep(duration)

    except KeyboardInterrupt:
        print("\nTest cancelled by user")
    finally:
        solenoid.off()
        print("Solenoid test finished and pin safely disabled")

if __name__ == "__main__":
    solenoid_test()
