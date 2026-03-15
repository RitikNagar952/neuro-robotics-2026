# ══════════════════════════════════════════════════════
#  reader.py  —  Serial ingestion, signal filtering,
#                classification, and mode-based dispatch.
#
#  Expected serial format (4 comma-separated values):
#    eog_h, eog_v, right_arm_emg, left_arm_emg
#
#  Dispatches to:
#    config.MODE == "cursor"      → cursor_control.apply_cursor()
#    config.MODE == "manipulator" → mapping.apply_mapping()
# ══════════════════════════════════════════════════════

import serial
import threading
import time
from collections import Counter, deque

import state
from config import PORT, BAUD_RATE, SAMPLE_RATE, MODE
from filters import process_eog, process_right_emg, process_left_emg
from classifiers import EOG, EMG, eog_classifier, emg_classifier

# ── Import the correct dispatcher based on MODE ───────
if MODE == "cursor":
    from cursor_control import apply_cursor as _dispatch

    def _call_dispatch(eog: EOG, right: EMG, left: EMG) -> None:
        _dispatch(eog, right)   # cursor only needs right arm + EOG

elif MODE == "manipulator":
    from mapping import apply_mapping as _dispatch

    def _call_dispatch(eog: EOG, right: EMG, left: EMG) -> None:
        _dispatch(eog, right, left)

else:
    raise ValueError(f"[READER] Unknown MODE '{MODE}' — must be 'cursor' or 'manipulator'")

# ── Left-arm rolling average buffer ───────────────────
_LEFT_WIN     = int(SAMPLE_RATE * 0.2)
_emg_left_buf = deque([0.0] * _LEFT_WIN, maxlen=_LEFT_WIN)


def _loop(ser: serial.Serial) -> None:
    last_classify_time       = time.time()
    emg_right_window: list[EMG] = []
    emg_left_window:  list[EMG] = []
    latest_eog: EOG              = EOG.NONE

    while True:
        try:
            line = ser.readline().decode('utf-8', errors='ignore').strip()
            if not line:
                continue

            parts = line.split(',')
            if len(parts) != 4:
                continue

            raw0      = float(parts[0])
            raw1      = float(parts[1])
            raw_right = float(parts[2])
            raw_left  = float(parts[3])

            # ── Signal processing ─────────────────────
            val0, val1, det0, det1 = process_eog(raw0, raw1)
            val_right              = process_right_emg(raw_right)
            val_left               = process_left_emg(raw_left)

            # ── Update shared plot buffers ────────────
            with state.lock:
                state.ch0_buf.append(val0)
                state.ch1_buf.append(val1)
                state.ch2_buf.append(val_right)
                state.ch3_buf.append(val_left)

                state.emg_right_win_buf.append(val_right)
                state.current_emg_avg = (
                    sum(state.emg_right_win_buf) / len(state.emg_right_win_buf)
                )
                state.emg_left_win_buf.append(val_left)
                state.current_left_emg_avg = (
                    sum(state.emg_left_win_buf) / len(state.emg_left_win_buf)
                )

            # ── EOG classifier (full sample rate) ─────
            gesture = eog_classifier(det0, det1)
            if gesture != EOG.NONE:
                latest_eog = gesture
                print(f"[EOG] 👁  {gesture.name}")

            # ── 15 Hz window → classify → dispatch ────
            now = time.time()
            if now - last_classify_time >= (1.0 / 15.0):
                last_classify_time = now

                right_label = emg_classifier(state.current_emg_avg)
                left_label  = emg_classifier(state.current_left_emg_avg)

                emg_right_window.append(right_label)
                emg_left_window.append(left_label)

                if len(emg_right_window) >= 5:
                    right_mode = Counter(emg_right_window).most_common(1)[0][0]
                    left_mode  = Counter(emg_left_window).most_common(1)[0][0]

                    print(f"[EMG] Right: {right_mode.value}  |  Left: {left_mode.value}")
                    emg_right_window.clear()
                    emg_left_window.clear()

                    _call_dispatch(latest_eog, right_mode, left_mode)
                    latest_eog = EOG.NONE   # consume latched gesture

        except Exception as exc:
            print(f"[READER] {exc}")


def start() -> threading.Thread:
    ser = serial.Serial(PORT, BAUD_RATE, timeout=2)
    time.sleep(1.5)
    ser.reset_input_buffer()
    print(f"[READER] Connected on {PORT} @ {BAUD_RATE} baud.")
    print(f"[READER] Mode: {MODE.upper()}")

    t = threading.Thread(target=_loop, args=(ser,), daemon=True)
    t.start()
    return t
