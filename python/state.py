# ══════════════════════════════════════════════════════
#  state.py  —  Shared mutable state & thread primitives.
#
#  All modules import from here — single source of truth
#  for every deque, lock, flag, and queue.
# ══════════════════════════════════════════════════════

import threading
import queue
from collections import deque
from config import BUFFER_SIZE, SAMPLE_RATE

# ── Plot Buffers (written by reader, read by visualiser) ──
ch0_buf = deque([0.0] * BUFFER_SIZE, maxlen=BUFFER_SIZE)  # EOG horizontal
ch1_buf = deque([0.0] * BUFFER_SIZE, maxlen=BUFFER_SIZE)  # EOG vertical
ch2_buf = deque([0.0] * BUFFER_SIZE, maxlen=BUFFER_SIZE)  # Right arm EMG (rectified)
ch3_buf = deque([0.0] * BUFFER_SIZE, maxlen=BUFFER_SIZE)  # Left  arm EMG (rectified)

# ── EMG Rolling Average Buffers (0.2-second window) ───────
_EMG_WIN = int(SAMPLE_RATE * 0.2)

emg_right_win_buf    = deque([0.0] * _EMG_WIN, maxlen=_EMG_WIN)
current_emg_avg      = 0.0   # right arm rolling avg — read by classifier & visualiser

emg_left_win_buf     = deque([0.0] * _EMG_WIN, maxlen=_EMG_WIN)
current_left_emg_avg = 0.0   # left  arm rolling avg — read by classifier & visualiser

# Legacy alias so older code still using emg_win_buf doesn't break
emg_win_buf = emg_right_win_buf

# ── Thread Lock (protects all buffers above) ──────────────
lock = threading.Lock()

# ── Motor Command Queue (written by mapping, drained by motor worker) ──
motor_queue: queue.Queue = queue.Queue()

# ── Armed Flag (written by mapping, read by visualiser) ───
armed: bool = False
