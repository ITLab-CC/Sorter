import board
import neopixel
import time

class NeoPixelController:
    """A class to control a NeoPixel LED strip or ring."""
    
    def __init__(self, pin=board.D18, count: int = 24, brightness: float = 0.5):
        self.pin = pin
        self.count = count
        self.brightness = brightness
        
        # Initialize the hardware within the object
        self.pixels = neopixel.NeoPixel(
            self.pin, 
            self.count, 
            brightness=self.brightness, 
            auto_write=False
        )

    def set_color(self, color: tuple) -> None:
        """Fills the entire strip with a specific RGB color."""
        self.pixels.fill(color)
        self.pixels.show()

    def turn_off(self) -> None:
        """Clears all LEDs (turns them off)."""
        self.set_color((0, 0, 0))

if __name__ == "__main__":
    # 1. Instantiate the controller (uses the default values defined in __init__)
    led_ring = NeoPixelController()
    
    """Runs a test sequence, turning LEDs white for a set duration."""
    duration = 5  # Duration in seconds for the test
    try:
        print("NeoPixel test started...")
        time.sleep(1)

        print(f"Turning NeoPixel rings on for {duration} seconds")
        led_ring.set_color((255, 255, 255))

        # Replaced the commented-out loop with a simple sleep 
        # for the specified duration
        time.sleep(duration)

    except KeyboardInterrupt:
        print("\nTest cancelled by user")

    finally:
        # Uncommented the cleanup so the LEDs turn off when the script ends
        led_ring.turn_off()
        print("NeoPixel test finished")