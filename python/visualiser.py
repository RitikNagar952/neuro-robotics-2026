# ══════════════════════════════════════════════════════
#  visualiser.py  —  Matplotlib live-plot for all 4
#                    signal channels + status HUD.
#
#  Panels:
#    0  CH0  Horizontal EOG (signed-squared)
#    1  CH1  Vertical   EOG (signed-squared)
#    2  CH2  Right arm  EMG (rectified)
#    3  CH3  Left  arm  EMG (rectified)
#
#  Call show() to display.  Blocks until window closed.
# ══════════════════════════════════════════════════════

import matplotlib.pyplot as plt
import matplotlib.animation as animation

import state
from config import BUFFER_SIZE, DISPLAY_SECS

_BG       = '#1a1a2e'
_PANEL_BG = '#16213e'
_GRID     = '#2a2a4a'
_SPINE    = '#444'

_CH_COLORS = ['#00BFFF', '#FF6B6B', '#00FF9C', '#FFD700']
_CH_TITLES = [
    "CH0  Horizontal EOG (signed-squared)",
    "CH1  Vertical EOG (signed-squared)",
    "CH2  Right Arm EMG (rectified)",
    "CH3  Left Arm EMG (rectified)",
]
_EOG_YLIM = (-1500, 1500)
_EMG_YLIM = (-20, 150)


def show() -> None:
    """Build the 4-panel figure and start the animation. Blocks until closed."""

    fig, axes = plt.subplots(4, 1, figsize=(12, 10))
    fig.patch.set_facecolor(_BG)
    fig.suptitle("NPG Lite  —  EOG + Dual-Arm EMG  |  Motor Control Active",
                 color='white', fontsize=13)

    x = list(range(BUFFER_SIZE))
    lines = []

    for i, (ax, title, color) in enumerate(zip(axes, _CH_TITLES, _CH_COLORS)):
        ax.set_facecolor(_PANEL_BG)
        ax.set_title(title, color='white', fontsize=10)
        ax.set_xlim(0, BUFFER_SIZE)
        ax.set_ylim(_EMG_YLIM if i >= 2 else _EOG_YLIM)
        ax.tick_params(colors='white')
        ax.grid(True, color=_GRID)
        for spine in ax.spines.values():
            spine.set_edgecolor(_SPINE)

        (ln,) = ax.plot(x, [0.0] * BUFFER_SIZE, color=color)
        lines.append(ln)

    axes[3].set_xlabel(f"← {DISPLAY_SECS} seconds", color='white')

    # ── HUD overlays ──────────────────────────────────
    # Right arm avg on CH2 panel
    hud_right = axes[2].text(
        0.02, 0.82,
        "Right Avg: 0.00  |  Armed: ❌",
        transform=axes[2].transAxes,
        color='white', fontsize=10, fontweight='bold',
        bbox=dict(facecolor=_BG, edgecolor='#00FF9C', alpha=0.75),
    )

    # Left arm avg on CH3 panel
    hud_left = axes[3].text(
        0.02, 0.82,
        "Left Avg: 0.00",
        transform=axes[3].transAxes,
        color='white', fontsize=10, fontweight='bold',
        bbox=dict(facecolor=_BG, edgecolor='#FFD700', alpha=0.75),
    )

    def _update(_frame):
        with state.lock:
            d0         = list(state.ch0_buf)
            d1         = list(state.ch1_buf)
            d2         = list(state.ch2_buf)
            d3         = list(state.ch3_buf)
            right_avg  = state.current_emg_avg
            left_avg   = state.current_left_emg_avg

        lines[0].set_ydata(d0)
        lines[1].set_ydata(d1)
        lines[2].set_ydata(d2)
        lines[3].set_ydata(d3)

        arm_icon = "✅" if state.armed else "❌"
        hud_right.set_text(f"Right Avg: {right_avg:.2f}  |  Armed: {arm_icon}")
        hud_left.set_text(f"Left Avg:  {left_avg:.2f}")

        return *lines, hud_right, hud_left

    _ani = animation.FuncAnimation(   # noqa: F841  (keep reference alive)
        fig, _update, interval=40, blit=True, cache_frame_data=False
    )

    plt.tight_layout()
    plt.show()
