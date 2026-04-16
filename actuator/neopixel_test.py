import board
import neopixel
import time

LED_PIN = board.D18
LED_COUNT = 24
LED_BRIGHTNESS = 0.5

pixels = neopixel.NeoPixel(LED_PIN, LED_COUNT, brightness=LED_BRIGHTNESS, auto_write=False)

def neopixel_test():
    try:
        print("NeoPixel Test gestartet...")
        time.sleep(1)

        print("Schalte NeoPixel Ringe für 10 Sekunden an")
        pixels.fill((255, 255, 255))
        pixels.show()

        for _ in range(100):
            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\nTest durch Nutzer abgebrochen")

    finally:
        pixels.fill((0, 0, 0))
        pixels.show()
        print("NeoPixel Test beendet")

if __name__ == "__main__":
    neopixel_test()
