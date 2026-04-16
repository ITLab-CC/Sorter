from gpiozero import MCP3008
import time
from datetime import datetime

sensor = MCP3008(channel=0)

def lichtschranken_test():
    print("Lichtschranken-Test gestartet...")
    time.sleep(1)

    log_datei_sicher = open("sichere_erkennungs_log.txt", "w")
    log_datei_unsicher = open("unsichere_erkennungs_log.txt", "w")
    start_zeit = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_datei_sicher.write(f"--- Neuer Test gestartet am {start_zeit} ---\n")
    log_datei_unsicher.write(f"--- Neuer Test gestartet am {start_zeit} ---\n")

    grenzenwert_kleiner = 0.550
    grenzenwert_größer = 0.625

    limit_erkennungen = 5

    unsichere_erkennungen_kleiner = 0
    unsichere_erkennungen_größer = 0

    sichere_erkennungen_kleiner = 0
    sichere_erkennungen_größer = 0

    objekt_ist_kleiner = False
    objekt_ist_größer = False

    try:
        while True:
            messwert = sensor.value
            zeitstempel = datetime.now().strftime("%H:%M:%S.%f")[:-3]

            if messwert < grenzenwert_kleiner:
                unsichere_erkennungen_kleiner += 1

                nachricht = f"[{zeitstempel}] Sensorwert: {messwert:.3f} - Unsicher Kleiner: {unsichere_erkennungen_kleiner}"
                log_datei_unsicher.write(nachricht + "\n")
                log_datei_unsicher.flush()

                if unsichere_erkennungen_kleiner >= limit_erkennungen:
                    sichere_erkennungen_kleiner += 1
                    unsichere_erkennungen_kleiner = 0
                    nachricht_sicher = f"[{zeitstempel}] Sensorwert: {messwert:.3f} - Unsicher Kleiner: {unsichere_erkennungen_kleiner} - Sicher Kleiner: {sichere_erkennungen_kleiner}x"
                    print(nachricht_sicher)
                    log_datei_sicher.write(nachricht_sicher + "\n")
                    log_datei_sicher.flush()

            elif messwert > grenzenwert_größer:
                unsichere_erkennungen_größer += 1

                nachricht = f"[{zeitstempel}] Sensorwert: {messwert:.3f} - Unsicher Größer: {unsichere_erkennungen_größer}"
                log_datei_unsicher.write(nachricht + "\n")
                log_datei_unsicher.flush()

                if unsichere_erkennungen_größer >= limit_erkennungen:
                    sichere_erkennungen_größer += 1
                    unsichere_erkennungen_größer = 0

                    nachricht_sicher = f"[{zeitstempel}] Sensorwert: {messwert:.3f} - Unsicher Größer: {unsichere_erkennungen_größer} - Sicher Größer: {sichere_erkennungen_größer}x"
                    print(nachricht_sicher)
                    log_datei_sicher.write(nachricht_sicher + "\n")
                    log_datei_sicher.flush()

            else:
                unsichere_erkennungen_kleiner = 0
                unsichere_erkennungen_größer = 0

                nachricht = f"[{zeitstempel}] Sensorwert: {messwert:.3f} - NIX - Unsicher Kleiner: {unsichere_erkennungen_kleiner} - Sicher Kleiner: {sichere_erkennungen_kleiner}x - Unsicher Größer: {unsichere_erkennungen_größer} - Sicher Größer: {sichere_erkennungen_größer}x"
                print(nachricht)

            time.sleep(0.001)

    except KeyboardInterrupt:
        abbruch_zeit = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(f"\n[{abbruch_zeit}] Test durch Nutzer abgebrochen.")

    finally:
        log_datei_sicher.write("--- Test beendet ---\n")
        log_datei_sicher.close()
        log_datei_unsicher.write("--- Test beendet ---\n")
        log_datei_unsicher.close()
        print("Log-Dateien erfolgreich gespeichert und geschlossen.")

if __name__ == "__main__":
    lichtschranken_test()
