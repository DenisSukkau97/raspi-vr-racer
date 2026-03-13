#!/usr/bin/env python3

import time

from gpiozero import Servo, PWMOutputDevice, OutputDevice

from gpiozero.pins.lgpio import LGPIOFactory

from approxeng.input.selectbinder import ControllerResource

from threading import Thread

# === Konfiguration ===

factory = LGPIOFactory()

# Servo (GPIO 18, Software-PWM)

servo = Servo(18, pin_factory=factory, min_pulse_width=0.0005, max_pulse_width=0.0025)

# Motor L298N

IN1 = OutputDevice(17, pin_factory=factory)  # Richtung vorwärts

IN2 = OutputDevice(27, pin_factory=factory)  # Richtung rückwärts

ENA = PWMOutputDevice(12, pin_factory=factory, frequency=1000)

# Globale Variable für sauberes Beenden

running = True


def set_servo(angle_deg):
    """ Winkel von -90° bis +90° """

    value = max(-1.0, min(1.0, angle_deg / 90.0))

    servo.value = value


def set_motor(speed):
    """ Geschwindigkeit: -1.0 (voller Rückwärts) bis +1.0 (voller Vorwärts) """

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

    print("Controller-Suchmodus gestartet – läuft endlos bis ein Controller gefunden wird")

    while running:

        try:

            print("Suche nach Controller... (PS4/PS5: Share/Create + PS-Taste lange drücken zum Pairen)")

            print("Wartezeit: bis zu 60 Sekunden pro Versuch – Controller einschalten!")

            with ControllerResource(dead_zone=0.1, hot_zone=0.05) as joystick:

                print("→ Controller erfolgreich verbunden:", joystick.controls)

                print("=== RC-Car Steuerung aktiv! ===")

                # Innere Schleife: solange der Controller verbunden ist

                while joystick.connected and running:

                    # Lenkung: linker Stick X

                    lx = joystick.lx or 0.0

                    set_servo(lx * 90)

                    # Trigger-Werte holen – None wird zu 0.0 (neutral)

                    r2 = joystick.r2 or 0.0

                    l2 = joystick.l2 or 0.0

                    # Geschwindigkeit berechnen

                    speed = (r2 - l2) * 1.0

                    # Totzone

                    if abs(speed) < 0.08:
                        speed = 0.0

                    set_motor(speed)

                    time.sleep(0.02)  # ~50 Hz Update-Rate

                print("Controller-Verbindung verloren – suche erneut...")



        except IOError:

            print("Kein Controller erkannt – warte 5 Sekunden und versuche erneut...")

            time.sleep(5)



        except Exception as e:

            print(f"Unerwarteter Fehler im Controller-Thread: {type(e).__name__}: {e}")

            time.sleep(5)


if __name__ == "__main__":

    print("RC-Car Steuerung mit PS4/PS5 Controller – Starte...")

    print("Servo: GPIO 18 | Motor PWM: GPIO 12 (1000 Hz) | IN1:17 | IN2:27")

    print("----------------------------------------------------")

    # Motor und Servo initial stoppen

    set_motor(0.0)

    set_servo(0)

    # Controller-Such-Thread starten

    thread = Thread(target=controller_thread, daemon=True)

    thread.start()

    try:

        while running:
            time.sleep(0.1)

    except KeyboardInterrupt:

        print("\nBeende Programm...")

    finally:

        running = False

        set_motor(0.0)

        set_servo(0)

        ENA.off()

        print("Motoren gestoppt. Programm beendet.")