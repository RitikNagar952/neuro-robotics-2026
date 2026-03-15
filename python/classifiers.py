# ══════════════════════════════════════════════════════
#  classifiers.py  —  EOG gesture classifier,
#                     EMG level classifier,
#                     and their return-type enums.
# ══════════════════════════════════════════════════════

from enum import IntEnum, StrEnum

from config import (
    EOG_RPEAK, EOG_RDIP,
    EOG_LPEAK, EOG_LDIP,
    EOG_UPEAK, EOG_UDIP,
    EOG_DPEAK, EOG_DDIP,
    EOG_BPEAK, EOG_BDIP,
    DIP_PEAK_MAX_DURATION,
    EMG_STRONG_THRESHOLD,
    EMG_MEDIUM_THRESHOLD,
    EMG_LOW_THRESHOLD,
)

# ══════════════════════════════════════════════════════
#  Enums  (replaces magic numbers / raw strings)
# ══════════════════════════════════════════════════════

class EOG(IntEnum):
    """
    Return codes from eog_classifier().

    Being an IntEnum means every value IS an int, so
    existing code like `if code != 0` or dict keys like
    {EOG.LEFT: "m1/clk"} all work without any changes.
    """
    NONE  = 0   # no gesture detected / detection in progress
    LEFT  = 1
    RIGHT = 2
    UP    = 3
    DOWN  = 4
    BLINK = 5


class EMG(StrEnum):
    """
    Return labels from emg_classifier().

    Being a StrEnum means every value IS a str, so
    existing comparisons like `if label == "STRONG"`
    and set membership checks all work unchanged.
    """
    STRONG = "STRONG"
    MEDIUM = "MEDIUM"
    LOW    = "LOW"
    IDLE   = "IDLE"


# ══════════════════════════════════════════════════════
#  EOG Classifier
# ══════════════════════════════════════════════════════

_eog_state   = None   # "dip" | "peak" | None
_eog_channel = None   # 1 (horizontal) | 2 (vertical) | None
_eog_counter = 0
_eog_peak    = 0.0
_eog_dip     = 0.0


def reset_eog() -> None:
    """Reset EOG classifier to idle state (useful for testing)."""
    global _eog_state, _eog_channel, _eog_counter, _eog_peak, _eog_dip
    _eog_state = _eog_channel = None
    _eog_counter = 0
    _eog_peak = _eog_dip = 0.0


def eog_classifier(ch0_val: float, ch1_val: float) -> EOG:
    """
    Stateful EOG gesture detector.  Call once per sample.

    Parameters
    ----------
    ch0_val : dead-zone-gated horizontal EOG value
    ch1_val : dead-zone-gated vertical   EOG value

    Returns
    -------
    EOG  — gesture enum value (EOG.NONE while no gesture / in progress)
    """
    global _eog_state, _eog_channel, _eog_counter, _eog_peak, _eog_dip

    # ── Tracking phase ────────────────────────────────
    if _eog_state is not None:
        _eog_counter += 1

        if _eog_channel == 1:
            _eog_peak = max(_eog_peak, ch0_val)
            _eog_dip  = min(_eog_dip,  ch0_val)

            if _eog_state == "dip" and _eog_peak > EOG_RPEAK and ch0_val < _eog_peak - 100:
                reset_eog(); return EOG.LEFT

            if _eog_state == "peak" and _eog_dip < EOG_LDIP and ch0_val > _eog_dip + 100:
                reset_eog(); return EOG.RIGHT

        elif _eog_channel == 2:
            _eog_peak = max(_eog_peak, ch1_val)
            _eog_dip  = min(_eog_dip,  ch1_val)

            if _eog_state == "dip" and _eog_dip < EOG_BDIP and ch1_val > EOG_BPEAK:
                reset_eog(); return EOG.BLINK

            if _eog_state == "dip" and _eog_peak > EOG_UPEAK and ch1_val < _eog_peak - 100:
                reset_eog(); return EOG.UP

            if _eog_state == "peak" and _eog_dip < EOG_DDIP and ch1_val > _eog_dip + 100:
                reset_eog(); return EOG.DOWN

        if _eog_counter > DIP_PEAK_MAX_DURATION:
            reset_eog()

        return EOG.NONE

    # ── Detection phase ───────────────────────────────
    if ch0_val < EOG_RDIP:
        _eog_state = "dip";  _eog_channel = 1
        _eog_counter = 0;    _eog_peak = _eog_dip = ch0_val
        return EOG.NONE

    if ch0_val > EOG_LPEAK:
        _eog_state = "peak"; _eog_channel = 1
        _eog_counter = 0;    _eog_peak = _eog_dip = ch0_val
        return EOG.NONE

    if ch1_val < EOG_UDIP:
        _eog_state = "dip";  _eog_channel = 2
        _eog_counter = 0;    _eog_peak = _eog_dip = ch1_val
        return EOG.NONE

    if ch1_val > EOG_DPEAK:
        _eog_state = "peak"; _eog_channel = 2
        _eog_counter = 0;    _eog_peak = _eog_dip = ch1_val
        return EOG.NONE

    return EOG.NONE


# ══════════════════════════════════════════════════════
#  EMG Classifier
# ══════════════════════════════════════════════════════


def emg_classifier(avg_val: float) -> EMG:
    """
    Classify the current 0.2-second EMG rolling average.

    Returns
    -------
    EMG  — level enum value
    """

    
    if avg_val > EMG_MEDIUM_THRESHOLD:
        return EMG.STRONG
    if avg_val > EMG_LOW_THRESHOLD and avg_val < EMG_MEDIUM_THRESHOLD:
        return EMG.MEDIUM
    if avg_val < EMG_LOW_THRESHOLD:
        return EMG.LOW
    return EMG.IDLE
