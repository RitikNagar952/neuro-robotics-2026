# ══════════════════════════════════════════════════════
#  controller.py  —  Motor mapping, arm-state logic,
#                    and the background HTTP worker.
#
#  EOG → Motor mapping
#    1 Left   → m1 CW
#    2 Right  → m1 CCW
#    3 Up     → m2 CW
#    4 Down   → m2 CCW
#    5 Blink  → ignored
#    0        → no gesture, hold current state
#
#  Arm logic (driven by 1-second EMG mode)
#    MEDIUM | STRONG → armed   (EOG commands forwarded)
#    LOW    | IDLE   → disarmed (all motors stopped)
# ══════════════════════════════════════════════════════

import threading
import requests
import state
from config import ESP32_IP

# ── EOG → motor command lookup ────────────────────────
_EOG_TO_CMD: dict[int, str] = {
    1: "m1/clk",      # Left
    2: "m1/anticlk",  # Right
    3: "m2/clk",      # Up
    4: "m2/anticlk",  # Down
    # 5 (Blink) and 0 (none) are intentionally absent
}

_ALL_MOTORS = ["m1", "m2", "m4", "m5"]


# ── Low-level HTTP helpers ────────────────────────────

def _send(cmd: str) -> None:
    url = f"http://{ESP32_IP}/{cmd}"
    try:
        requests.get(url, timeout=1)
        print(f"[MOTOR] Sent: {cmd}")
    except Exception:
        print(f"[MOTOR] Connection failed: {cmd}")


def _stop_all() -> None:
    for m in _ALL_MOTORS:
        _send(f"{m}/stop")


# ── Background HTTP worker ────────────────────────────
# Drains state.motor_queue so slow network calls never
# block the signal-processing thread.

def _motor_worker() -> None:
    while True:
        cmd = state.motor_queue.get()
        if cmd == "__STOP_ALL__":
            _stop_all()
        else:
            _send(cmd)
        state.motor_queue.task_done()


_worker_thread = threading.Thread(target=_motor_worker, daemon=True)
_worker_thread.start()


# ── Public API ────────────────────────────────────────

def motor_control(eog_code: int, emg_mode: str) -> None:
    """
    Translate one EOG gesture + EMG arm-mode into motor commands.

    Called once per ~1-second EMG window from the reader thread.

    Parameters
    ----------
    eog_code : int  — latest latched EOG gesture (0–5)
    emg_mode : str  — modal EMG class for the window
    """
    # ── Update arm state ─────────────────────────────
    if emg_mode in ("MEDIUM", "STRONG"):
        if not state.armed:
            state.armed = True
            print("[CTRL] Armed ✅")
    else:
        if state.armed:
            state.armed = False
            print("[CTRL] Disarmed 🛑 — stopping all motors")
            state.motor_queue.put("__STOP_ALL__")
        return   # disarmed: ignore EOG entirely

    # ── Forward EOG gesture to motor ─────────────────
    if eog_code in _EOG_TO_CMD:
        cmd = _EOG_TO_CMD[eog_code]
        print(f"[CTRL] EOG {eog_code} → {cmd}")
        state.motor_queue.put(cmd)
    # eog_code 0 → no gesture, hold current motor state
    # eog_code 5 → blink, ignored
