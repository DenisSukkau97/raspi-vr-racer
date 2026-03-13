# 03.06.26 // Oliver / Denis 
###########################################################################

# Steuerung Software mit Shutdown 
# und allen anderen enthaltenen 

###########################################################################

#!/usr/bin/env python3
"""
RC-Car Steuerung mit Raspberry Pi 5 und PS5 DualSense Controller
---------------------------------------------------------------
- Lenkung: Linker Analog-Stick X-Achse (ABS_X)
- Vorwärts: R2 (ABS_RZ)
- Rückwärts: L2 (ABS_Z)
- Not-Stop: Programmende setzt Motor und Servo auf 0

Hardware:
- Servo: GPIO 18 (PWM)
- L298N Motor-Treiber:
  - IN1: GPIO 17
  - IN2: GPIO 27
  - ENA (PWM): GPIO 12

Abhängigkeiten: gpiozero, lgpio, evdev
"""

import time
from gpiozero import Servo, PWMOutputDevice, OutputDevice
from gpiozero.pins.lgpio import LGPIOFactory
from evdev import InputDevice, ecodes, list_devices


# ────────────────────────────────────────────────
# KONSTANTEN & EINSTELLUNGEN
# ────────────────────────────────────────────────

MAX_STEER_ANGLE = 25.0      # Maximale Lenkwinkel pro Seite in Grad (±25°)
DEADZONE_STICK = 0.08       # Totzone für den Analog-Stick (verhindert Zittern)
DEADZONE_TRIGGER = 0.05     # Totzone für Trigger (verhindert minimales Kriechen)

# GPIO-Pins (Raspberry Pi 5 – lgpio Pin-Factory)
SERVO_PIN = 18
MOTOR_IN1 = 17
MOTOR_IN2 = 27
MOTOR_ENA = 12              # PWM-fähiger Pin
PWM_FREQUENCY = 1000        # 1 kHz – gut für L298N


# ────────────────────────────────────────────────
# GPIO INITIALISIERUNG
# ────────────────────────────────────────────────

factory = LGPIOFactory()

# Lenk-Servo (mit angepassten Pulsbreiten für bessere Mitte)
servo = Servo(
    SERVO_PIN,
    pin_factory=factory,
    min_pulse_width=0.0010,
    max_pulse_width=0.0020
)

# Motorsteuerung über L298N
IN1 = OutputDevice(MOTOR_IN1, pin_factory=factory)
IN2 = OutputDevice(MOTOR_IN2, pin_factory=factory)
ENA = PWMOutputDevice(MOTOR_ENA, pin_factory=factory, frequency=PWM_FREQUENCY)


# ────────────────────────────────────────────────
# HILFSFUNKTIONEN
# ────────────────────────────────────────────────

def set_servo(angle_deg: float) -> None:
    """
    Setzt den Lenkwinkel des Servos.
    Winkel wird auf ±MAX_STEER_ANGLE begrenzt.
    
    Args:
        angle_deg: Gewünschter Lenkwinkel (- = links, + = rechts)
    """
    clamped = max(-MAX_STEER_ANGLE, min(MAX_STEER_ANGLE, angle_deg))
    servo.value = clamped / MAX_STEER_ANGLE


def set_motor(speed: float) -> None:
    """
    Setzt die Motorgeschwindigkeit und Richtung über L298N.
    
    Args:
        speed: -1.0 (voll rückwärts) bis +1.0 (voll vorwärts)
    """
    if speed > 0:
        IN1.on()
        IN2.off()
        ENA.value = min(1.0, speed)
    elif speed < 0:
        IN1.off()
        IN2.on()
        ENA.value = min(1.0, -speed)
    else:
        IN1.off()
        IN2.off()
        ENA.value = 0.0


def emergency_stop() -> None:
    """ Sofortiger Not-Stop: Motor und Servo auf neutral """
    set_motor(0.0)
    set_servo(0.0)


def find_dualsense() -> InputDevice | None:
    """
    Sucht nach einem angeschlossenen DualSense-Controller.
    
    Returns:
        InputDevice oder None, wenn kein DualSense gefunden wurde
    """
    for path in list_devices():
        try:
            device = InputDevice(path)
            if "DualSense" in device.name:
                return device
        except Exception:
            pass
    return None


# ────────────────────────────────────────────────
# HAUPTPROGRAMM
# ────────────────────────────────────────────────

if __name__ == "__main__":

    print("=== RC-Car Steuerung – PS5 DualSense Edition ===")
    print(f"Lenkung: Linker Stick X (±{MAX_STEER_ANGLE}°)")
    print("Gas: R2 = Vorwärts, L2 = Rückwärts")
    print("------------------------------------------------")

    # Initialer Not-Stop
    emergency_stop()

    while True:
        # Suche nach DualSense
        gamepad = find_dualsense()

        if gamepad is None:
            print("Kein DualSense gefunden – warte 2 Sekunden...")
            emergency_stop()
            time.sleep(2)
            continue

        print(f"Verbunden mit: {gamepad.name}")
        print("Drücke Strg+C zum Beenden\n")

        r2 = 0.0
        l2 = 0.0

        try:
            for event in gamepad.read_loop():

                if event.type == ecodes.EV_ABS:

                    # Linker Stick X-Achse (Lenkung)
                    if event.code == ecodes.ABS_X:
                        # 0..255 → -1 .. +1 normalisieren
                        norm = (event.value - 128) / 128.0
                        if abs(norm) < DEADZONE_STICK:
                            norm = 0.0
                        set_servo(norm * MAX_STEER_ANGLE)

                    # L2 (linker Trigger)
                    elif event.code == ecodes.ABS_Z:
                        l2 = event.value / 255.0

                    # R2 (rechter Trigger)
                    elif event.code == ecodes.ABS_RZ:
                        r2 = event.value / 255.0

                    # Geschwindigkeit berechnen: R2 vorwärts, L2 rückwärts
                    speed = r2 - l2

                    # Totzone für Trigger
                    if abs(speed) < DEADZONE_TRIGGER:
                        speed = 0.0

                    set_motor(speed)

        except OSError:
            print("Controller-Verbindung verloren!")
            emergency_stop()
            time.sleep(1)
        except KeyboardInterrupt:
            print("\nProgramm beendet per Strg+C")
            emergency_stop()
            break
