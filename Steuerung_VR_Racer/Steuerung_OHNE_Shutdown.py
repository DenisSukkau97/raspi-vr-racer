# 06.03.26 /7 Oliver / Denis 

########################################################

# Alternativ Steuerungs Skript - OHNE SHUTDOWN

########################################################


#!/usr/bin/env python3
import time
from gpiozero import Servo, PWMOutputDevice, OutputDevice
from gpiozero.pins.lgpio import LGPIOFactory
from evdev import InputDevice, ecodes, list_devices

# ─────────────────────────────────────
# GPIO SETUP
# ─────────────────────────────────────
factory = LGPIOFactory()

servo = Servo(
    18,
    pin_factory=factory,
    min_pulse_width=0.0010,
    max_pulse_width=0.0020
)

IN1 = OutputDevice(17, pin_factory=factory)
IN2 = OutputDevice(27, pin_factory=factory)
ENA = PWMOutputDevice(12, pin_factory=factory, frequency=1000)

# ─────────────────────────────────────
# SETTINGS
# ─────────────────────────────────────
MAX_STEER_ANGLE = 25
DEADZONE_STICK = 0.08
DEADZONE_TRIGGER = 0.05

# ─────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────
def set_servo(angle_deg):
    clamped = max(-MAX_STEER_ANGLE, min(MAX_STEER_ANGLE, float(angle_deg)))
    servo.value = clamped / MAX_STEER_ANGLE


def set_motor(speed):
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


def emergency_stop():
    set_motor(0.0)
    set_servo(0)


def find_dualsense():
    for path in list_devices():
        device = InputDevice(path)
        if "DualSense" in device.name:
            return device
    return None


# ─────────────────────────────────────
# MAIN CONTROL LOOP
# ─────────────────────────────────────
if __name__ == "__main__":

    print("=== RC CAR – PS5 FINAL VERSION ===")
    emergency_stop()

    while True:

        gamepad = find_dualsense()

        if gamepad is None:
            print("Kein DualSense gefunden – warte...")
            emergency_stop()
            time.sleep(2)
            continue

        print("Verbunden mit:", gamepad.name)

        r2 = 0.0
        l2 = 0.0

        try:
            for event in gamepad.read_loop():

                if event.type == ecodes.EV_ABS:

                    # Linker Stick X (0–255 → -1 bis +1)
                    if event.code == ecodes.ABS_X:
                        norm = (event.value - 128) / 128
                        if abs(norm) < DEADZONE_STICK:
                            norm = 0.0
                        set_servo(norm * MAX_STEER_ANGLE)

                    # L2
                    elif event.code == ecodes.ABS_Z:
                        l2 = event.value / 255

                    # R2
                    elif event.code == ecodes.ABS_RZ:
                        r2 = event.value / 255

                    # Motorberechnung
                    speed = r2 - l2
                    if abs(speed) < DEADZONE_TRIGGER:
                        speed = 0.0

                    set_motor(speed)

        except OSError:
            print("Controller getrennt!")
            emergency_stop()
            time.sleep(1)
