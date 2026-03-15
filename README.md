# 🧠 Neuro-Robotics Control System
### 🏆 Winner — Neuro-Robotics Hackathon 2026 | The Neurotech Society, IIT Jodhpur

> Control a **PC cursor** and a **5-motor robotic arm** using only your **eyes (EOG)** and **muscles (EMG)** — no hands required.

---

## 📌 What This Project Does

This system captures biosignals from electrodes placed on the face and arms, processes them in real time, and translates them into control commands for two different actuators:

| Mode | Input | Output |
|------|-------|--------|
| **Cursor Control** | EOG (eye gaze) + EMG (right arm) | PC mouse cursor + left click |
| **Manipulator Control** | EOG (eye gaze) + Dual-arm EMG | 5-motor robotic arm via ESP32 WiFi |

Switch between modes by editing one line in `python/config.py`:
```python
MODE = "cursor"       # or "manipulator"
```

---

## 🗂️ Repository Structure

```
neuro-robotics-2026/
│
├── firmware/                        # Arduino firmware (staged development)
│   ├── Stage_1_EOG_only/            # Stage 1: 2-channel horizontal + vertical EOG
│   ├── Stage_2_EMG_EOG/             # Stage 2: EOG + single-arm EMG
│   ├── Stage_3_baseline_correction/ # Stage 3: Baseline calibration command ('c')
│   ├── Stage_4_chords/              # Stage 4: Chord-style gesture experiment
│   └── Final_4CH_EMG_EOG/           # ✅ FINAL: 4-channel (EOG H/V + dual-arm EMG)
│
├── python/                          # Main Python control system
│   ├── main.py                      # Entry point — run this
│   ├── config.py                    # ⚙️  All tunable parameters (PORT, MODE, thresholds)
│   ├── state.py                     # Shared buffers, locks, queues
│   ├── reader.py                    # Serial ingestion + classification loop
│   ├── filters.py                   # Butterworth + notch filters (SciPy)
│   ├── classifiers.py               # EOG gesture + EMG level classifiers
│   ├── controller.py                # Motor HTTP dispatch (manipulator mode)
│   ├── mapping.py                   # EOG + dual-EMG → motor command logic
│   ├── cursor_control.py            # EOG + EMG → pyautogui cursor/click
│   └── visualiser.py                # Live 4-panel Matplotlib signal viewer
│
├── esp32/
│   └── motor_server/
│       └── motor_server.ino         # ESP32 WiFi HTTP motor command server
│
├── extras/
│   └── atm_gui.py                   # Bonus: Flask ATM GUI demo (keypad-controlled)
│
├── docs/
│   └── wiring_guide.md              # Hardware wiring reference
│
├── requirements.txt                 # Python dependencies
├── .gitignore
└── README.md
```

---

## 🔧 Hardware Required

| Component | Purpose |
|-----------|---------|
| **Neuroplayground (NPG) Lite Beast** | Biosignal acquisition — 4-channel EOG + EMG |
| **Arduino (Uno / Nano / Mega)** | 512 Hz ADC sampling + on-chip signal filtering |
| **ESP32** | WiFi HTTP server for motor commands |
| **L298N 2A Dual Motor Driver** | H-bridge control for DC motors |
| **LM2596S DC-DC Buck Converter** | Regulated power supply for motors |
| **DIY 5-Motor Robotic Arm Kit** | The physical manipulator |
| **Electrodes** | Face (EOG: near eyes) + arms (EMG: forearm muscles) |

---

## 🚀 Quick Start

### 1. Clone the repo
```bash
git clone https://github.com/YOUR_USERNAME/neuro-robotics-2026.git
cd neuro-robotics-2026
```

### 2. Install Python dependencies
```bash
pip install -r requirements.txt
```

### 3. Flash Arduino firmware
- Open `firmware/Final_4CH_EMG_EOG/EMG_EOG_4CHL.ino` in Arduino IDE
- Select your board and COM port
- Upload

### 4. Flash ESP32 (for manipulator mode only)
- Open `esp32/motor_server/motor_server.ino` in Arduino IDE
- Set your WiFi SSID and password inside the file
- Upload to ESP32

### 5. Configure Python
Edit `python/config.py`:
```python
PORT     = 'COM11'        # ← your Arduino serial port (Linux: '/dev/ttyUSB0')
ESP32_IP = "192.168.x.x"  # ← your ESP32's IP address
MODE     = "cursor"        # ← "cursor" or "manipulator"
```

### 6. Run
```bash
cd python
python main.py
```

---

## 🧠 How It Works

### Signal Pipeline
```
Electrodes
   │
   ▼
NPG Lite Beast  (analog biosignal amplification)
   │
   ▼
Arduino @ 512 Hz
   ├── 50 Hz IIR Notch Filter  (power-line rejection)
   ├── 12-sample sliding average (EOG smoothing)
   ├── 8-sample rectified average (EMG smoothing)
   └── Baseline calibration on 'c' command
   │
   ▼  USB Serial @ 115200 baud
   │  format: "eog_h, eog_v, emg_right, emg_left\n"
   │
   ▼
Python reader.py
   ├── filters.py   → Butterworth HPF/LPF + spike rejection + dead-zone gating
   ├── classifiers.py
   │     ├── EOG: 5 gestures (LEFT / RIGHT / UP / DOWN / BLINK)
   │     └── EMG: 4 levels  (STRONG / MEDIUM / LOW / IDLE)
   └── 15 Hz window + 5-sample majority vote → stable classification
   │
   ▼
   ├── [cursor mode]      → cursor_control.py → pyautogui
   └── [manipulator mode] → mapping.py → controller.py → HTTP → ESP32 → L298N → Motors
```

### EOG Gesture → Action Mapping (Manipulator Mode)

| Eye Gesture | Right Arm EMG | Action |
|-------------|--------------|--------|
| LEFT        | MEDIUM       | Motor 1 clockwise (base rotation) |
| RIGHT       | MEDIUM       | Motor 1 counter-clockwise |
| UP          | MEDIUM       | Motor 2 clockwise (shoulder) |
| DOWN        | MEDIUM       | Motor 2 counter-clockwise |
| BLINK       | any          | Toggle Motor 5 (gripper) for 2 seconds |
| LEFT        | MEDIUM (left arm) | Motor 4 clockwise |
| RIGHT       | MEDIUM (left arm) | Motor 4 counter-clockwise |
| any         | LOW / IDLE   | All motors stopped (disarmed) |

---

## ⚙️ Key Configuration Parameters (`python/config.py`)

```python
PORT      = 'COM11'          # Arduino serial port
BAUD_RATE = 115200
SAMPLE_RATE = 512            # Hz

# EOG classifier thresholds (tune per person)
EOG_RPEAK =  1000;  EOG_RDIP  =  -500
EOG_LPEAK =   400;  EOG_LDIP  =  -400
EOG_UPEAK =   800;  EOG_UDIP  =  -500
EOG_DPEAK =   500;  EOG_DDIP  = -1000
EOG_BPEAK =  1500;  EOG_BDIP  = -1500

# EMG classifier thresholds
EMG_STRONG_THRESHOLD = 700
EMG_MEDIUM_THRESHOLD = 90
EMG_LOW_THRESHOLD    = 13

MODE     = "manipulator"     # "cursor" or "manipulator"
ESP32_IP = "192.168.220.225"
```

---

## 📦 Dependencies

See `requirements.txt`. Main libraries:
- `pyserial` — Arduino serial communication
- `scipy` / `numpy` — digital signal processing
- `matplotlib` — live signal visualiser
- `pyautogui` — cursor + click control (cursor mode)
- `requests` — HTTP commands to ESP32 (manipulator mode)
- `flask` — ATM GUI demo (extras)

---

## 👥 Team

Built at **Neuro-Robotics Hackathon 2026** · The Neurotech Society · IIT Jodhpur 🏆

---

## 📄 License

MIT License — free to use, modify, and build on.

---

## 🔌 ESP32 Pin Reference (Actual Hardware)

| Motor | Function       | GPIO A | GPIO B |
|-------|---------------|--------|--------|
| M1    | Base rotation | 26     | 27     |
| M2    | Shoulder      | 25     | 33     |
| M3    | Elbow         | 16     | 17     |
| M4    | Wrist         | 18     | 19     |
| M5    | Gripper       | 22     | 23     |

The ESP32 also serves a **web control UI** at `http://<ESP32_IP>/` — open in any browser for keyboard + touchscreen motor control (useful for manual testing without Python).

Keys: `1`/`2` = M1 CW/CCW, `3`/`4` = M2, `5`/`6` = M3, `7`/`8` = M4, `9`/`0` = M5. `SPACE` = toggle hold mode.
