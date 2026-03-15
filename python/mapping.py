# ══════════════════════════════════════════════════════
#  mapping.py  —  Translates EOG gesture + dual-arm EMG
#                 labels into motor commands.
# ══════════════════════════════════════════════════════

import threading
import time
import state
from classifiers import EOG, EMG
from controller import _send, _stop_all

# ── Toggle state (flipped on every Right=STRONG) ──────
_toggle_on: bool = False

# ── Timed-run duration for Motor 4 & 5 ───────────────
M45_RUN_SECS = 2.0

# ── Lookup tables (EOG enum → motor command string) ───
_RIGHT_ARM_EOG: dict[EOG, str] = {
    EOG.RIGHT: "m1/clk",
    EOG.LEFT:  "m1/anticlk",
    EOG.UP:    "m2/clk",
    EOG.DOWN:  "m2/anticlk",
}

_LEFT_ARM_EOG: dict[EOG, str] = {
    EOG.RIGHT: "m4/clk",
    EOG.LEFT:  "m4/anticlk",
}

_ACTIVE = {EMG.MEDIUM, EMG.STRONG}


def _is_active(label: EMG) -> bool:
    return label in _ACTIVE


def _all_idle(right: EMG, left: EMG) -> bool:
    return not _is_active(right) and not _is_active(left)


def _run_then_stop(motor: str, direction: str, delay: float) -> None:
    """
    Start a motor, wait `delay` seconds in a background daemon
    thread, then send stop — never blocks the signal pipeline.
    """
    def _worker():
        _send(f"{motor}/{direction}")
        time.sleep(delay)
        _send(f"{motor}/stop")
        print(f"[MAP] {motor} auto-stopped after {delay}s")

    threading.Thread(target=_worker, daemon=True).start()


def apply_mapping(eog_code: EOG, right_emg: EMG, left_emg: EMG) -> None:
    """
    Evaluate the current gesture + EMG combination and
    dispatch the appropriate motor command.

    Parameters
    ----------
    eog_code  : EOG  — latched gesture for this window
    right_emg : EMG  — 1-second modal label for right arm
    left_emg  : EMG  — 1-second modal label for left arm
    """
    global _toggle_on

    # ── 1. Both arms idle / LOW → stop everything ─────
    if _all_idle(right_emg, left_emg):
        if state.armed:
            state.armed = False
            print("[MAP] Both arms idle — stopping all motors 🛑")
            _stop_all()
        return

    if not state.armed:
        state.armed = True
        print("[MAP] Armed ✅")

    # ── 2. Right STRONG → toggle Motor 4 + Motor 5 ────
    #   ON  → both spin CW  for 2s then auto-stop
    #   OFF → both spin CCW for 2s then auto-stop
    if eog_code == EOG.BLINK:
        _toggle_on = not _toggle_on
        direction  = "clk" if _toggle_on else "anticlk"
        label      = "ON 🟢" if _toggle_on else "OFF 🔴"

        print(f"[MAP] Right STRONG → Toggle {label}  ( m5 {direction} for {M45_RUN_SECS}s)")
        # _run_then_stop("m4", direction, M45_RUN_SECS)
        _run_then_stop("m5", direction, M45_RUN_SECS)
        return

    # ── 3. Right MEDIUM + EOG → Motor 1 / Motor 2 ─────
    if right_emg == EMG.MEDIUM and eog_code in _RIGHT_ARM_EOG:
        cmd = _RIGHT_ARM_EOG[eog_code]
        print(f"[MAP] Right MEDIUM + {eog_code.name} → {cmd}")
        _send(cmd)

    # ── 4. Left MEDIUM + EOG → Motor 3 ────────────────
    if left_emg == EMG.MEDIUM and eog_code in _LEFT_ARM_EOG:
        cmd = _LEFT_ARM_EOG[eog_code]
        print(f"[MAP] Left MEDIUM + {eog_code.name} → {cmd}")
        _send(cmd)

    # EOG.NONE  → no gesture, hold current motor states
    # EOG.BLINK → ignored per spec
    # EMG.LEFT STRONG → nothing extra per spec
