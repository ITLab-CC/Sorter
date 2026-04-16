from gpiozero import MCP3008
import time
from datetime import datetime

sensor = MCP3008(channel=0)

SCHWELLENWERT_AN = 0.610
SCHWELLENWERT_AUS = 0.580
BENOETIGTE_TREFFER = 2

def lichtschranken_test():
    print("Lichtschranken-Test gestartet... (Abbruch mit Strg+C)")
    print("Halte deine Hand vor den Sensor!")
    time.sleep(1)

    objekt_erkannt = False
    treffer_zaehler = 0

    log_datei = open("erkennungs_log.txt", "w")
    start_zeit = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_datei.write(f"--- Neuer Test gestartet am {start_zeit} ---\n")

    try:
        while True:
            messwert = sensor.value
            zeitstempel = datetime.now().strftime("%H:%M:%S.%f")[:-3]

            if messwert < SCHWELLENWERT_AUS:
                treffer_zaehler = 0

                if objekt_erkannt:
                    nachricht = f"[{zeitstempel}] Sensorwert: {messwert:.3f} Objekt verlassen"
                    print(nachricht)
                    log_datei.write(nachricht + "\n")
                    log_datei.flush()
                    objekt_erkannt = False

            elif messwert > SCHWELLENWERT_AN:
                treffer_zaehler += 1

                if treffer_zaehler >= BENOETIGTE_TREFFER and not objekt_erkannt:
                    nachricht = f"[{zeitstempel}] Sensorwert: {messwert:.3f} Echtes Objekt erkannt"
                    print(nachricht)
                    log_datei.write(nachricht + "\n")
                    log_datei.flush()
                    objekt_erkannt = True

            time.sleep(0.001)

    except KeyboardInterrupt:
        abbruch_zeit = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(f"\n[{abbruch_zeit}] Test durch Nutzer abgebrochen.")

    finally:
        log_datei.write("--- Test beendet ---\n")
        log_datei.close()
        print("Log-Datei erfolgreich gespeichert und geschlossen.")

if __name__ == "__main__":
    lichtschranken_test()
