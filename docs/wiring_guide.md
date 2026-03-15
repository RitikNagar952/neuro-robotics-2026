# Hardware Wiring Guide

## Electrode Placement (NPG Lite Beast)

| Channel | Signal | Electrode Location |
|---------|--------|-------------------|
| A0 (EOG H) | Horizontal eye movement | Left and right corners of eye (or temples) |
| A1 (EOG V) | Vertical eye movement | Above and below one eye |
| A2 (EMG R) | Right arm muscle | Right forearm — over the flexor muscle |
| A3 (EMG L) | Left arm muscle | Left forearm — over the flexor muscle |

**Reference electrode:** Behind the ear (mastoid) or earlobe.

---

## Arduino → NPG Lite Beast

| NPG Output | Arduino Pin |
|------------|-------------|
| EOG Horizontal | A0 |
| EOG Vertical   | A1 |
| EMG Right Arm  | A2 |
| EMG Left Arm   | A3 |
| GND            | GND |
| VCC (3.3V/5V)  | 3.3V or 5V (check NPG datasheet) |

---

## ESP32 → L298N Motor Driver (Actual Pin Mapping)

| Motor | Function | ESP32 GPIO A | ESP32 GPIO B |
|-------|----------|-------------|-------------|
| Motor 1 | Base rotation  | GPIO 26 | GPIO 27 |
| Motor 2 | Shoulder       | GPIO 25 | GPIO 33 |
| Motor 3 | Elbow          | GPIO 16 | GPIO 17 |
| Motor 4 | Wrist          | GPIO 18 | GPIO 19 |
| Motor 5 | Gripper        | GPIO 22 | GPIO 23 |

Connect each ESP32 GPIO pair to the corresponding L298N IN1/IN2 (or IN3/IN4) input pins.

> **Web UI:** Open a browser and go to `http://<ESP32_IP>/` to get the keyboard + touch button control panel. Keys 1–0 control motors CW/CCW. SPACE toggles hold mode.

---

## LM2596S Power Supply

- **Input:** 12V DC adapter (or battery)
- **Output:** Set to motor rated voltage (typically 6–9V for small DC motors)
- Connect LM2596S output → L298N 12V power input + GND

---

## Quick Checklist Before Running

- [ ] NPG Lite Beast connected to Arduino A0–A3
- [ ] Arduino connected to PC via USB
- [ ] ESP32 flashed with motor_server.ino (WiFi credentials set)
- [ ] ESP32 IP address copied into `python/config.py`
- [ ] Arduino COM port set in `python/config.py`
- [ ] LM2596S output voltage set and connected to L298N
- [ ] All motor wires connected to L298N output terminals
- [ ] `python main.py` running — check serial monitor for connection messages
