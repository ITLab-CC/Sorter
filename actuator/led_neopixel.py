import board
import neopixel
import time

class NeoPixelController:
    """A class to control a NeoPixel LED strip or ring."""
    
    def __init__(self, pin=board.D18, count: int = 24, brightness: float = 0.5):
        self.pin = pin
        self.count = count
        
        # Initialize the hardware
        self.pixels = neopixel.NeoPixel(
            self.pin, 
            self.count, 
            brightness=brightness, 
            auto_write=False
        )

    @property
    def brightness(self) -> float:
        """Gets the current brightness."""
        return self.pixels.brightness

    @brightness.setter
    def brightness(self, value: float) -> None:
        """Sets the brightness and updates the LEDs immediately."""
        self.pixels.brightness = value
        self.pixels.show()

    def set_color(self, color: tuple, brightness: float = None) -> None:
        """Fills the entire strip with a specific RGB color.

        Args:
            color: RGB tuple to fill the strip with.
            brightness: Optional brightness (0.0-1.0). Overrides current brightness.
        """
        if brightness is not None:
            self.pixels.brightness = brightness
            
        self.pixels.fill(color)
        self.pixels.show()

    def turn_off(self) -> None:
        """Clears all LEDs (turns them off)."""
        self.set_color((0, 0, 0))

if __name__ == "__main__":
    # Instantiate the controller
    led_ring = NeoPixelController()
    
    try:
        print("NeoPixel test started...")
        
        # 1. Turn on with default brightness
        led_ring.set_color((255, 255, 255), 0.1)
        time.sleep(1)

        print("Testing runtime brightness changes...")
        
        # 2. Change brightness at runtime using the new property!
        # Fade down
        for b in [0.4, 0.3, 0.2, 0.1, 0.05]:
            led_ring.brightness = b
            time.sleep(0.5)
            
        # Fade up
        for b in [0.1, 0.3, 0.4, 0.5]:
            led_ring.brightness = b
            time.sleep(0.5)

    except KeyboardInterrupt:
        print("\nTest cancelled by user")

    finally:
        # Cleanup so the LEDs turn off when the script ends
        led_ring.turn_off()
        print("NeoPixel test finished")