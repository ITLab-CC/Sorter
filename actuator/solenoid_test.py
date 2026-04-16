from gpiozero import OutputDevice
from time import sleep

# Pin-Konfiguration
SOLENOID_PIN = 16
solenoid = OutputDevice(SOLENOID_PIN)

def solenoid_test():
    # Test-Intervalle in Sekunden
    intervalle = [1.0, 1.0, 0.5, 0.5, 0.1, 0.1]
    
    try:
        print(f"Solenoid Test an GPIO-Pin {SOLENOID_PIN} gestartet...")
        sleep(1)

        for dauer in intervalle:
            print(f"Solenoid AN ({dauer}s)")
            solenoid.on()
            sleep(dauer)
            
            solenoid.off()
            print("Solenoid AUS")
            sleep(dauer)

    except KeyboardInterrupt:
        print("\nTest durch Nutzer abgebrochen")
    finally:
        solenoid.off()
        print("Solenoid Test beendet und Pin sicher deaktiviert")

if __name__ == "__main__":
    solenoid_test()
