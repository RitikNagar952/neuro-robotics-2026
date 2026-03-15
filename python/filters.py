# ══════════════════════════════════════════════════════
#  filters.py  —  Filter design & stateful sample-level
#                 processing for EOG and EMG channels.
# ══════════════════════════════════════════════════════

from scipy.signal import iirnotch, sosfilt, sosfilt_zi, tf2sos, butter
from config import SAMPLE_RATE, SPIKE_THRESHOLD, DEAD_ZONE

# ── Filter Design ─────────────────────────────────────
b_notch, a_notch = iirnotch(w0=50.0, Q=30.0, fs=SAMPLE_RATE)
sos_notch = tf2sos(b_notch, a_notch)

sos_eog_high = butter(2, 0.5,  btype='highpass', fs=SAMPLE_RATE, output='sos')
sos_eog_low  = butter(4, 10.0, btype='low',      fs=SAMPLE_RATE, output='sos')
sos_emg_high = butter(2, 20.0, btype='highpass', fs=SAMPLE_RATE, output='sos')

# ── Filter State (initial conditions) ─────────────────
_zi = {
    'notch0':         sosfilt_zi(sos_notch),
    'notch1':         sosfilt_zi(sos_notch),
    'eog_high0':      sosfilt_zi(sos_eog_high),
    'eog_high1':      sosfilt_zi(sos_eog_high),
    'eog_low0':       sosfilt_zi(sos_eog_low),
    'eog_low1':       sosfilt_zi(sos_eog_low),
    'emg_high_right': sosfilt_zi(sos_emg_high),   # right arm — independent state
    'emg_high_left':  sosfilt_zi(sos_emg_high),   # left  arm — independent state
}

# ── Spike rejection state ──────────────────────────────
_prev = [0.0, 0.0]   # [prev_ch0, prev_ch1]


def process_eog(raw0: float, raw1: float) -> tuple[float, float, float, float]:
    """
    Run one sample through the full EOG pipeline.

    Returns
    -------
    val0_final, val1_final : signed-squared scaled values (for plotting)
    det0, det1             : dead-zone gated values       (for classifier)
    """
    n0, _zi['notch0']    = sosfilt(sos_notch,    [raw0], zi=_zi['notch0'])
    n1, _zi['notch1']    = sosfilt(sos_notch,    [raw1], zi=_zi['notch1'])
    h0, _zi['eog_high0'] = sosfilt(sos_eog_high, [n0[0]], zi=_zi['eog_high0'])
    h1, _zi['eog_high1'] = sosfilt(sos_eog_high, [n1[0]], zi=_zi['eog_high1'])
    s0, _zi['eog_low0']  = sosfilt(sos_eog_low,  [h0[0]], zi=_zi['eog_low0'])
    s1, _zi['eog_low1']  = sosfilt(sos_eog_low,  [h1[0]], zi=_zi['eog_low1'])

    val0, val1 = float(s0[0]), float(s1[0])

    if abs(val0 - _prev[0]) > SPIKE_THRESHOLD: val0 = _prev[0]
    if abs(val1 - _prev[1]) > SPIKE_THRESHOLD: val1 = _prev[1]
    _prev[0], _prev[1] = val0, val1

    val0_final = (val0 * abs(val0)) / 100.0
    val1_final = (val1 * abs(val1)) / 100.0

    det0 = val0_final if abs(val0_final) > DEAD_ZONE else 0.0
    det1 = val1_final if abs(val1_final) > DEAD_ZONE else 0.0

    return val0_final, val1_final, det0, det1


def process_right_emg(raw: float) -> float:
    """Highpass + rectify one right-arm EMG sample."""
    h, _zi['emg_high_right'] = sosfilt(sos_emg_high, [raw], zi=_zi['emg_high_right'])
    return abs(float(h[0]))


def process_left_emg(raw: float) -> float:
    """Highpass + rectify one left-arm EMG sample."""
    h, _zi['emg_high_left'] = sosfilt(sos_emg_high, [raw], zi=_zi['emg_high_left'])
    return abs(float(h[0]))


# Keep old name as alias so any legacy callers don't break
process_emg = process_right_emg
