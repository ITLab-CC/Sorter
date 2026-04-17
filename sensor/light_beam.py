from gpiozero import MCP3008
import time
from datetime import datetime

sensor = MCP3008(channel=0)

THRESHOLD_ON = 0.610
THRESHOLD_OFF = 0.580
REQUIRED_HITS = 2

def light_beam_test():
    print("Light beam test started... (press Ctrl+C to stop)")
    print("Hold your hand in front of the sensor!")
    time.sleep(1)

    object_detected = False
    hit_count = 0

    log_file = open("detection_log.txt", "w")
    start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_file.write(f"--- New test started at {start_time} ---\n")

    try:
        while True:
            sensor_value = sensor.value
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]

            if sensor_value < THRESHOLD_OFF:
                hit_count = 0

                if object_detected:
                    message = f"[{timestamp}] Sensor value: {sensor_value:.3f} Object left"
                    print(message)
                    log_file.write(message + "\n")
                    log_file.flush()
                    object_detected = False

            elif sensor_value > THRESHOLD_ON:
                hit_count += 1

                if hit_count >= REQUIRED_HITS and not object_detected:
                    message = f"[{timestamp}] Sensor value: {sensor_value:.3f} Real object detected"
                    print(message)
                    log_file.write(message + "\n")
                    log_file.flush()
                    object_detected = True

            time.sleep(0.001)

    except KeyboardInterrupt:
        abort_time = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(f"\n[{abort_time}] Test cancelled by user.")

    finally:
        log_file.write("--- Test finished ---\n")
        log_file.close()
        print("Log file saved and closed successfully.")

if __name__ == "__main__":
    light_beam_test()