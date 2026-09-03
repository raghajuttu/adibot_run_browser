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
    so spikes survive. More buckets = smoother curves, bigger file. Used for
    velocity/effort (read as envelopes) and as the fallback when a run is too
    large to embed raw."""

    raw_max_points: int = 1_500_000
    """Semantic zoom stores the RAW command + actual-position arrays so the
    page can re-decimate at draw time (zooming reveals real samples, not
    bigger pixels). A run whose ticks x joints x 2 exceeds this budget falls
    back to decimated-only for that run — the page says so instead of becoming
    unopenably large. 1.5M points ~= a 45-minute run on 16 joints."""

    raw_decimals: int = 4
    """Rounding for raw position values (radians). 4 decimals = 0.1 mrad
    resolution, well below anything the arm can do, and about half the JSON
    of full doubles."""

    dstep_decimals: int = 1
    """Rounding for the per-tick command-step series (mrad)."""

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
            # Written by logger >= v0.4 (feat/run-metadata-logging). The first
            # three appear only on each chunk's first executed tick, blank
            # elsewhere (same convention as latency_ms); buffer_len is per
            # tick. All four are optional — older CSVs simply lack them.
            "chunk_len": "chunk_len",
            "skip_steps": "skip_steps",
            "rtc_applied": "rtc_applied",
            "buffer_len": "buffer_len",
            "cmd_prefix": "cmd_",
            "act_prefix": "actual_pos_",
            "vel_prefix": "actual_vel_",
            "eff_prefix": "actual_eff_",
            "left_violation": "left_limit_violation",
            "right_violation": "right_limit_violation",
        }
    )
    """CSV column layout. Change here if the logger's schema ever changes."""

    finger_marker: str = "finger"
    """Substring that marks a joint as a gripper finger."""

    # NOTE on timing columns: wall_time is quantized to ~10 s by the logger's
    # %.9g float format and must never be used for intervals — every duration
    # here derives from t_rel.

    meta_suffix: str = ".meta.json"
    """Sidecar filename: <run>.csv -> <run>.meta.json (logger >= v0.4). Holds
    the run's configuration; runs without one show 'config unknown'."""

    chunk_store_max_values: int = 900_000
    """Budget for embedding the raw chunk arrays (n_chunks x steps x joints)
    in the page, which the plans view needs. A run over budget ships its
    metrics but no plans, flagged on the page. 150 chunks x 40 x 16 = 96k."""

    plans_window_s: float = 8.0
    """The plans view draws full predictions only when the visible window is
    this short — a whole run's worth of overlaid chunks is an unreadable
    smear. Wider than this, it shows the executed command and asks you to
    zoom."""

    chunks_suffix: str = ".chunks.npz"
    """Full-chunk store: <run>.csv -> <run>.chunks.npz (logger with
    log_chunks, post-v0.5). Holds every action chunk including the unexecuted
    tail; enables the overlap metrics. Runs without one show '—'."""

    # -------------------------------------------------- scheduling / stalls
    stall_gap_ms: float = 100.0
    """A tick interval longer than this counts as a stall. In the old blocking
    loop a stall at every chunk boundary was EXPECTED (the ~240 ms round
    trip); with prefetch a stall of any kind means starvation — a bug."""

    stalled_run_min_boundary_ms: float = 100.0
    """A run is treated as blocking-style (so the tracking table's 'bnd'
    settle diagnosis applies) only when its median boundary tick interval
    exceeds this; otherwise boundaries carry no catch-up time and bnd is
    meaningless."""

    # ----------------------------------------------------------- smoothness
    splice_window_ticks: int = 3
    """Half-window around a chunk switch for the velocity-spike check."""

    dircos_reference: float = 0.97
    """Direction continuity of the training demonstrations, shown beside the
    measured value as the target. Cosine between consecutive command steps:
    +1 = motion carries straight on, 0 = right-angle turn, negative = the
    command reverses. Measured at 0.973 over 20 adibot episodes; re-measure
    on your own dataset if you change robots."""

    dircos_warn_below: float = 0.5
    """Direction continuity at or below this is flagged. A policy far below
    its demonstrations is emitting a zigzag rather than a trajectory, which
    is a model problem no scheduling strategy can fix."""

    dircos_usable_min: float = 0.8
    """A horizon step counts as 'usable' when the model's plan keeps at least
    this much direction continuity there. The longest run of usable steps is
    reported as the part of the horizon the policy plans coherently — the
    window an execution horizon should stay inside. Raise it to be stricter
    about what counts as a trajectory."""

    # ------------------------------------------------------- grasp attempts
    grasp_close_frac: float = 0.35
    """A finger counts as commanded-closed when its command drops below this
    fraction of its command range (~0.0 closed .. ~0.05 open)."""

    grasp_rise_fracs: tuple = (0.1, 0.9)
    """Fractions of the finger range bounding the close rise-time measurement
    (command falling from 90% open to 10% open). RTC ramping lengthens this —
    it is the 'is RTC smearing the grasp' test."""

    grasp_min_range: float = 0.005
    """A finger whose commanded range over the run is below this (rad) is
    treated as parked: hold/grasp detection is disabled for it. Prevents the
    blocked-threshold (a fraction of the range) collapsing to noise level."""

    grasp_track_frac: float = 0.25
    """A finger only gets hold/grasp detection if its median |actual - cmd|
    is below this fraction of its range — i.e. it demonstrably follows its
    command when free. A disabled or unpowered gripper ignores commands, and
    the resulting gap would otherwise be shaded as 'holding an object'."""

    grasp_success_min_ticks: int = 3
    """Blocked ticks inside a closed span needed to call the grasp a success.
    Smaller than grasp_min_ticks so an object grabbed late in the span still
    counts."""

    # -------------------------------------------------- verdicts / matrix
    verdict_splice_ratio_max: float = 2.0
    """Matrix verdict: a run's splice ratio at or above this fails 'smooth'."""

    verdict_depth_max_steps: int = 26
    """Matrix verdict: deepest-executed-step p95 at or beyond this fails
    'depth'. Empirical for the current checkpoint family — grasp attempts
    issued deeper than this tend to fail. Re-measure per checkpoint."""


DEFAULTS = Options()
