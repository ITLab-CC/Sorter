import RPi.GPIO as GPIO
import time

# Definiere den GPIO-Pin und die Frequenz
PWM_PIN = 19
FREQUENCY = 1000  # 1000 Hz

# Setup für GPIO
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)
GPIO.setup(PWM_PIN, GPIO.OUT)

# PWM-Instanz erstellen
pwm = GPIO.PWM(PWM_PIN, FREQUENCY)

# PWM starten, erst mal auf 0% Duty Cycle (0V)
pwm.start(0)

try:
    # 3.3V Ausgabe (100% Duty Cycle)
    print("Setze auf 3.3V (100% Duty Cycle)")
    pwm.ChangeDutyCycle(100)
    time.sleep(2)  # Für 2 Sekunden auf 3.3V halten

    # 0V Ausgabe (0% Duty Cycle)
    print("Setze auf 0V (0% Duty Cycle)")
    pwm.ChangeDutyCycle(0)
    time.sleep(2)  # Für 2 Sekunden auf 0V halten

finally:
    # PWM beenden und GPIO-Pin zurücksetzen
    pwm.stop()
    GPIO.cleanup()
