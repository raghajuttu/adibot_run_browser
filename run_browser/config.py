"""All tunable options in one place. Edit values here, nothing else.

Every number the analysis or the page uses comes from this file, so changing a
threshold or a color never means hunting through the other modules.
"""

from dataclasses import dataclass, field


@dataclass
class Options:
    # ------------------------------------------------------------ data / build
    output_name: str = "run-browser.html"
    """Filename of the generated dashboard (written next to the chosen data)."""

    buckets: int = 400
    """Trace decimation: buckets per signal. Min and max of each bucket are kept,
    so spikes survive. More buckets = smoother curves, bigger file."""

    open_browser: bool = True
    """Open the generated page in the default browser when the build finishes."""

    # ------------------------------------------------------- lag estimation
    max_lag_ticks: int = 12
    """Search window (in control ticks) for the command-to-actual lag estimate."""

    # ------------------------------------------------------ contact detection
    contact_window_ticks: int = 31
    """Rolling-median window (~1 s at 30 Hz) that models slow gravity/load
    change; what remains after subtracting it is treated as external force."""

    contact_min_nm: float = 0.5
    """Floor for the spike threshold so sensor noise on unloaded joints never
    triggers an event."""

    contact_mad_k: float = 6.0
    """Threshold = max(floor, this * robust std of the residual)."""

    merge_ticks: int = 5
    """Events closer together than this merge into one."""

    # -------------------------------------------------------- grasp detection
    grasp_gap_frac: float = 0.25
    """A finger counts as blocked when (actual - commanded) exceeds this
    fraction of the finger's command range."""

    grasp_min_ticks: int = 10
    """Blocked must persist at least this many ticks to count as a grasp."""

    # ----------------------------------------------------------- page display
    page_title: str = "Adibot Run Browser"

    hi_error_mrad: float = 100.0
    """Stats-table cells above this tracking error are highlighted."""

    hi_contact_nm: float = 1.5
    """Contact-table peaks above this are highlighted."""

    column_names: dict = field(
        default_factory=lambda: {
            "time": "t_rel",
            "horizon": "horizon_idx",
            "chunk": "inference_seq",
            "latency": "latency_ms",
            "cmd_prefix": "cmd_",
            "act_prefix": "actual_pos_",
            "vel_prefix": "actual_vel_",
            "eff_prefix": "actual_eff_",
        }
    )
    """CSV column layout. Change here if the logger's schema ever changes."""

    finger_marker: str = "finger"
    """Substring that marks a joint as a gripper finger."""


DEFAULTS = Options()
