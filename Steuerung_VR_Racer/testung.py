# 03.06.26 // Oliver / Denis 

#####################################################################

# Testen der Steuerung 

#####################################################################
#!/usr/bin/env python3
import time
from gpiozero import Servo, PWMOutputDevice, OutputDevice
from gpiozero.pins.lgpio import LGPIOFactory
from approxeng.input.selectbinder import ControllerResource
from threading import Thread

# === Konfiguration ===
factory = LGPIOFactory()

# Servo (GPIO 18, Software-PWM)
servo = Servo(18, pin_factory=factory, min_pulse_width=0.0010, max_pulse_width=0.0020)

# Motor L298N
IN1 = OutputDevice(17, pin_factory=factory)
IN2 = OutputDevice(27, pin_factory=factory)
ENA = PWMOutputDevice(12, pin_factory=factory, frequency=1000)

running = True


def set_servo(angle_deg):
    """ Begrenzt auf ±25° (anpassbar) """
    clamped = max(-25.0, min(25.0, float(angle_deg)))
    value = clamped / 25.0
    servo.value = value


def set_motor(speed):
    """ Geschwindigkeit: -1.0 (Rückwärts) bis +1.0 (Vorwärts) """
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


def controller_thread():
    global running
    print("Controller-Suchmodus gestartet – läuft endlos bis Controller gefunden")

    while running:
        try:
            print("Suche nach Controller...")
            with ControllerResource(dead_zone=0.1, hot_zone=0.05) as joystick:
                print("→ Controller verbunden:", joystick.controls)
                print("=== Steuerung aktiv ===")
                print("Linker Stick X = Lenkung | Rechter Stick Y = Gas (vor = nach vorne schieben)")

                while joystick.connected and running:
                    # Lenkung: linker Stick X
                    lx = joystick.lx or 0.0
                    set_servo(lx * 25)          # ±25° max

                    # Gas: rechter Stick Y (ry)
                    #   ry ≈ -1.0 = voll nach vorne geschoben → vorwärts
                    #   ry ≈ +1.0 = voll nach hinten → rückwärts
                    ry = joystick.ry or 0.0
                    speed = -ry                 # negativ → vorwärts
                    # Totzone
                    if abs(speed) < 0.10:
                        speed = 0.0

                    set_motor(speed)

                    # Optional: Debug-Ausgabe (kann später entfernt werden)
                    # print(f"lx: {lx:.2f} | ry: {ry:.2f} → speed: {speed:.2f}")

                    time.sleep(0.02)

                print("Controller-Verbindung verloren – suche erneut...")

        except IOError:
            print("Kein Controller erkannt – warte 5 Sekunden...")
            time.sleep(5)
        except Exception as e:
            print(f"Unerwarteter Fehler: {type(e).__name__}: {e}")
            time.sleep(5)


if __name__ == "__main__":
    print("RC-Car Steuerung – Start...")
    print("Servo: GPIO 18 | Motor PWM: GPIO 12 @ 1000 Hz")
    print("Lenkung: linker Stick X | Gas: rechter Stick Y (vor = nach vorne)")
    print("----------------------------------------------------")

    set_motor(0.0)
    set_servo(0)

    # Kurzer Servo-Test beim Start (optional – kann entfernt werden)
    print("Servo-Test: Mitte → -25° → +25° → Mitte")
    set_servo(0); time.sleep(1)
    set_servo(-25); time.sleep(1.5)
    set_servo(25); time.sleep(1.5)
    set_servo(0)

    thread = Thread(target=controller_thread, daemon=True)
    thread.start()

    try:
        while running:
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nBeende...")
    finally:
        running = False
        set_motor(0.0)
        set_servo(0)
        ENA.off()
        print("Motoren gestoppt.")
