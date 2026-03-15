# ══════════════════════════════════════════════════════
#  config.py  —  All tunable parameters in one place.
#  Edit this file to change ports, thresholds, or IPs.
# ══════════════════════════════════════════════════════

# ── Serial ────────────────────────────────────────────
PORT      = 'COM11'
BAUD_RATE = 115200

# ── Signal ────────────────────────────────────────────
SAMPLE_RATE  = 512
DISPLAY_SECS = 10
BUFFER_SIZE  = SAMPLE_RATE * DISPLAY_SECS

SPIKE_THRESHOLD      = 40
DEAD_ZONE            = 80
DIP_PEAK_MAX_DURATION = 500

# ── EOG Classifier Thresholds ─────────────────────────
EOG_RPEAK =  1000;  EOG_RDIP  =  -500   # Right gaze
EOG_LPEAK =   400;  EOG_LDIP  =  -400   # Left  gaze
EOG_UPEAK =   800;  EOG_UDIP  =  -500   # Up    gaze
EOG_DPEAK =   500;  EOG_DDIP  = -1000   # Down  gaze
EOG_BPEAK =  1500;  EOG_BDIP  = -1500   # Blink

# ── EMG Classifier Thresholds ─────────────────────────
EMG_STRONG_THRESHOLD = 700    # above → STRONG
EMG_MEDIUM_THRESHOLD = 90    # above → MEDIUM  (below STRONG)
EMG_LOW_THRESHOLD    = 13    # below → LOW  (note: original used dip < 50)

# ── Motor / ESP32 ─────────────────────────────────────
ESP32_IP = "192.168.220.225"

# ── Mode Selection ────────────────────────────────────
# "cursor"      → EOG moves mouse, blink clicks
# "manipulator" → EOG + EMG drive motors via mapping.py
MODE = "manipulator"

# ── Cursor Settings ───────────────────────────────────
CURSOR_STEP      = 8      # pixels moved per loop tick
CURSOR_TICK_MS   = 10     # loop interval in milliseconds

