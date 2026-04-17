from gpiozero import MCP3008
import time
from datetime import datetime

sensor = MCP3008(channel=0)

def light_beam_test() -> None:
    print("Light beam test started...")
    time.sleep(1)

    safe_log_file = open("safe_detection_log.txt", "w")
    unsafe_log_file = open("unsafe_detection_log.txt", "w")
    start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    safe_log_file.write(f"--- New test started at {start_time} ---\n")
    unsafe_log_file.write(f"--- New test started at {start_time} ---\n")

    lower_threshold = 0.550
    upper_threshold = 0.625

    detection_limit = 5

    unsafe_detections_below = 0
    unsafe_detections_above = 0

    safe_detections_below = 0
    safe_detections_above = 0

    object_is_below = False
    object_is_above = False

    try:
        while True:
            sensor_value = sensor.value
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]

            if sensor_value < lower_threshold:
                unsafe_detections_below += 1

                message = f"[{timestamp}] Sensor value: {sensor_value:.3f} - Unsafe below: {unsafe_detections_below}"
                unsafe_log_file.write(message + "\n")
                unsafe_log_file.flush()

                if unsafe_detections_below >= detection_limit:
                    safe_detections_below += 1
                    unsafe_detections_below = 0
                    safe_message = f"[{timestamp}] Sensor value: {sensor_value:.3f} - Unsafe below: {unsafe_detections_below} - Safe below: {safe_detections_below}x"
                    print(safe_message)
                    safe_log_file.write(safe_message + "\n")
                    safe_log_file.flush()

            elif sensor_value > upper_threshold:
                unsafe_detections_above += 1

                message = f"[{timestamp}] Sensor value: {sensor_value:.3f} - Unsafe above: {unsafe_detections_above}"
                unsafe_log_file.write(message + "\n")
                unsafe_log_file.flush()

                if unsafe_detections_above >= detection_limit:
                    safe_detections_above += 1
                    unsafe_detections_above = 0

                    safe_message = f"[{timestamp}] Sensor value: {sensor_value:.3f} - Unsafe above: {unsafe_detections_above} - Safe above: {safe_detections_above}x"
                    print(safe_message)
                    safe_log_file.write(safe_message + "\n")
                    safe_log_file.flush()

            else:
                unsafe_detections_below = 0
                unsafe_detections_above = 0

                message = f"[{timestamp}] Sensor value: {sensor_value:.3f} - NONE - Unsafe below: {unsafe_detections_below} - Safe below: {safe_detections_below}x - Unsafe above: {unsafe_detections_above} - Safe above: {safe_detections_above}x"
                print(message)

            time.sleep(0.001)

    except KeyboardInterrupt:
        abort_time = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(f"\n[{abort_time}] Test cancelled by user.")

    finally:
        safe_log_file.write("--- Test finished ---\n")
        safe_log_file.close()
        unsafe_log_file.write("--- Test finished ---\n")
        unsafe_log_file.close()
        print("Log files saved and closed successfully.")

if __name__ == "__main__":
    light_beam_test()
