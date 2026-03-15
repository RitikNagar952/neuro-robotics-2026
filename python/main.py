#!/usr/bin/env python3
# ══════════════════════════════════════════════════════
#  main.py  —  Entry point.
#
#  Run:   python main.py
#
#  Switch modes by editing config.py:
#    MODE = "cursor"       → EOG moves mouse, blink clicks
#    MODE = "manipulator"  → EOG + EMG drive motors
# ══════════════════════════════════════════════════════

from config import MODE
import reader
import visualiser


def main() -> None:
    print(f"[MAIN] Starting in {MODE.upper()} mode")

    if MODE == "cursor":
        import cursor_control
        cursor_control.start()   # cursor movement loop (daemon)

    elif MODE == "manipulator":
        import controller        # starts motor worker thread on import
        _ = controller

    reader.start()       # serial + classification (daemon thread)
    visualiser.show()    # live plot — blocks until window is closed


if __name__ == "__main__":
    main()
