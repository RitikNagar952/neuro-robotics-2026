# ══════════════════════════════════════════════════════
#  cursor_control.py  —  EOG-driven mouse cursor.
#
#  Active only when config.MODE == "cursor".
#
#  Gesture → action mapping:
#    Right EMG = MEDIUM + EOG Right  → cursor moves right
#    Right EMG = MEDIUM + EOG Left   → cursor moves left
#    Right EMG = MEDIUM + EOG Up     → cursor moves up
#    Right EMG = MEDIUM + EOG Down   → cursor moves down
#    Right EMG = MEDIUM + EOG Blink  → left click
#    Right EMG ≠ MEDIUM              → cursor stops
# ══════════════════════════════════════════════════════

import threading
import time
import pyautogui
import state
from classifiers import EOG, EMG
from config import CURSOR_STEP, CURSOR_TICK_MS

# Disable pyautogui's built-in failsafe (move to corner = crash).
# Comment this back in if you want that safety net.
pyautogui.FAILSAFE = False

# ── Cursor velocity state (written by apply_cursor, read by _move_loop) ──
_dx: int = 0   # pixels per tick on X axis
_dy: int = 0   # pixels per tick on Y axis
_vel_lock = threading.Lock()


def apply_cursor(eog_code: EOG, right_emg: EMG) -> None:
    """
    Called once per ~1-second EMG window from reader.py.
    Updates cursor velocity or fires a click based on
    the current EOG gesture and right-arm EMG level.

    Only right EMG is used for cursor mode.
    Left arm EMG is ignored here (reserved for manipulator).

    Parameters
    ----------
    eog_code  : EOG — latched gesture for this window
    right_emg : EMG — 1-second modal label for right arm
    """
    global _dx, _dy

    if right_emg != EMG.MEDIUM:
        # Arm not active → stop cursor
        with _vel_lock:
            _dx, _dy = 0, 0
        if state.armed:
            state.armed = False
            print("[CURSOR] Stopped 🛑")
        return

    # Right EMG is MEDIUM → arm is active
    if not state.armed:
        state.armed = True
        print("[CURSOR] Active ✅")

    # ── Map EOG gesture to velocity or action ──────────
    if eog_code == EOG.BLINK:
        print("[CURSOR] 👁 BLINK → click 🖱")
        pyautogui.click()
        with _vel_lock:
            _dx, _dy = 0, 0   # stop movement on click
        return

    new_dx, new_dy = 0, 0

    if eog_code == EOG.RIGHT:
        new_dx = -CURSOR_STEP
    elif eog_code == EOG.LEFT:
        new_dx = +CURSOR_STEP
    elif eog_code == EOG.UP:
        new_dy = -CURSOR_STEP   # screen Y is inverted
    elif eog_code == EOG.DOWN:
        new_dy = +CURSOR_STEP
    # EOG.NONE → no gesture, hold last velocity

    if eog_code != EOG.NONE:
        with _vel_lock:
            _dx, _dy = new_dx, new_dy
        print(f"[CURSOR] 👁 {eog_code.name} → velocity ({_dx:+d}, {_dy:+d})")


def _move_loop() -> None:
    """
    Background daemon — moves the cursor continuously at
    CURSOR_TICK_MS intervals using the current velocity.
    Runs independently of the 1-second EMG window.
    """
    interval = CURSOR_TICK_MS / 1000.0
    while True:
        with _vel_lock:
            dx, dy = _dx, _dy

        if dx != 0 or dy != 0:
            x, y = pyautogui.position()
            pyautogui.moveTo(x + dx, y + dy)

        time.sleep(interval)


def start() -> threading.Thread:
    """Launch the cursor movement loop as a daemon thread."""
    t = threading.Thread(target=_move_loop, daemon=True)
    t.start()
    print(f"[CURSOR] Movement loop started  (step={CURSOR_STEP}px, tick={CURSOR_TICK_MS}ms)")
    return t
