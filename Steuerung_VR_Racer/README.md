06.03.26 // Oliver / Denis 
##################################################################################################################
# Steuerung_VR_Racer
Steuerungs Software um über einen Playstation Controller über Bluetooth den Raspberry Pi anzusteuern und darüber die angeschlossenen Motor und Servo Lenkung zu bedienen 

##################################################################################################################

# Raspberry Pi RC-Car Steuerung mit PS5 DualSense

## Projektbeschreibung

Steuert ein Tamiya TT-02 RC-Car (oder ähnlich) über einen Raspberry Pi 5 mit einem **PS5 DualSense Controller** (Bluetooth oder USB).

**Funktionen:**
- Lenkung über **linker Analog-Stick X-Achse**
- Vorwärts über **R2** (rechter Trigger)
- Rückwärts über **L2** (linker Trigger)
- Totzonen für Stick und Trigger einstellbar
- Not-Stop bei Verbindungsverlust
- Automatische Controller-Suche im Loop
- Begrenzter Lenkwinkel (±25°) zum Schutz der Mechanik

## Hardware

- Raspberry Pi 5 (4–8 GB empfohlen)
- Tamiya TT-02 Chassis (oder kompatibel)
- Brushless-Setup (z. B. Hobbywing QuicRun 120A + 3652 4000KV)
- PS5 DualSense Controller
- Servo (Metal-Gear empfohlen, z. B. PowerHD 3001HB)
- 4S LiPo (5000–6000 mAh 100C+)
- L298N oder Brushless-ESC mit BEC

**GPIO-Belegung:**
- Servo Signal → GPIO 18
- Motor IN1 → GPIO 17
- Motor IN2 → GPIO 27
- Motor ENA (PWM) → GPIO 12

## Installation

1. **Virtuelle Umgebung erstellen & aktivieren**
   ```bash
   cd ~/rc-car
   python3 -m venv venv
   source venv/bin/activate
<img width="1460" height="1398" alt="image" src="https://github.com/user-attachments/assets/61904b6c-d5c7-4f99-a2e7-1b37a0e7b332" />
