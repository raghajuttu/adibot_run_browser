"""Pure computation: one robot-run CSV in, one plain dict of results out.

No UI, no HTML, no file writing besides reading the CSV. Add or change a
metric here and the page picks it up through builder.py. Every threshold
comes from config.Options — nothing numeric is hardcoded in this module.
"""

from pathlib import Path

import numpy as np
import pandas as pd

from .config import Options


# --------------------------------------------------------------------- helpers
def decimate(t: np.ndarray, y: np.ndarray, nd: int) -> tuple[list, list]:
    """Min/max decimation: per bucket keep the min and max sample, in time
    order, so spikes survive the size reduction. Non-finite samples are
    dropped first — JSON must never carry a NaN token."""
    ok = np.isfinite(y)
    if not ok.all():
        t, y = t[ok], y[ok]
    n = len(y)
    if n <= 2 * nd:
        return [round(float(a), 3) for a in t], [round(float(b), 4) for b in y]
    edges = np.linspace(0, n, nd + 1).astype(int)
    tt, yy = [], []
    for a, b in zip(edges[:-1], edges[1:]):
        if b <= a:
            continue
        seg_t, seg_y = t[a:b], y[a:b]
        i_min, i_max = int(np.argmin(seg_y)), int(np.argmax(seg_y))
        for i in sorted({i_min, i_max}):
            tt.append(round(float(seg_t[i]), 3))
            yy.append(round(float(seg_y[i]), 4))
    return tt, yy


def intervals(mask: np.ndarray, merge_gap: int, min_len: int = 1) -> list[tuple[int, int]]:
    """Contiguous True runs in mask, merging runs closer than merge_gap."""
    idx = np.where(mask)[0]
    if len(idx) == 0:
        return []
    out, start, prev = [], idx[0], idx[0]
    for i in idx[1:]:
        if i - prev > merge_gap:
            out.append((start, prev))
            start = i
        prev = i
    out.append((start, prev))
    return [(a, b) for a, b in out if b - a + 1 >= min_len]


def estimate_lag(cmd: np.ndarray, act: np.ndarray, max_lag: int) -> int:
    """Tick shift that best aligns command with actual; -1 if the joint barely
    moved (lag undefined on a static joint) or the data is unusable.

    nanmean, not mean: a single dropped feedback sample (NaN in actual) must
    not poison every candidate shift and silently report lag 0.
    """
    if len(cmd) < 2:
        return -1
    moving = np.abs(np.gradient(cmd)) > 1e-4
    if moving.sum() < 50:
        return -1
    best_k, best_e = -1, np.inf
    for k in range(max_lag + 1):
        with np.errstate(invalid="ignore"):
            e = (
                np.nanmean(np.abs(cmd - act)[moving])
                if k == 0
                else np.nanmean(np.abs(cmd[:-k] - act[k:])[moving[k:]])
            )
        if np.isfinite(e) and e < best_e:
            best_k, best_e = k, e
    return best_k


def _round_list(arr: np.ndarray, decimals: int) -> list:
    """Array -> JSON-ready list: rounded floats, NaN/inf -> None. Raw traces
    must never carry a bare NaN token into the page."""
    out = []
    for v in arr:
        v = float(v)
        out.append(round(v, decimals) if np.isfinite(v) else None)
    return out


def _mrad(value: float) -> float | None:
    """rad -> mrad rounded, mapping NaN to None so it reaches JSON as null,
    never as a bare NaN token."""
    v = float(value)
    return None if not np.isfinite(v) else round(v * 1000, 1)


def _opt_series(df: pd.DataFrame, name: str) -> pd.Series | None:
    """A column that may not exist (logger >= v0.4 only)."""
    return df[name] if name in df.columns else None


def _pct(x, q) -> float | None:
    x = np.asarray(x, dtype=float)
    x = x[np.isfinite(x)]
    if len(x) == 0:
        return None
    return round(float(np.percentile(x, q)), 1)


# ---------------------------------------------------------------- per-run work
def process_run(
    csv_path: Path,
    cfg: Options,
    run_meta: dict | None = None,
    chunk_data: dict | None = None,
) -> dict:
    """Everything the dashboard shows for one run, as one JSON-ready dict.

    run_meta is the parsed .meta.json sidecar (None for pre-v0.4 logs); it is
    both echoed into the result and used where a metric needs a configured
    value (e.g. which guards were enabled).
    """
    col = cfg.column_names
    df = pd.read_csv(csv_path)
    for required in (col["time"], col["horizon"], col["chunk"]):
        if required not in df.columns:
            raise ValueError(f"missing column '{required}'")
    names = [c[len(col["cmd_prefix"]):] for c in df.columns if c.startswith(col["cmd_prefix"])]
    if not names:
        raise ValueError(f"no '{col['cmd_prefix']}*' columns found")
    if len(df) == 0:
        raise ValueError("no data rows (header only)")

    t = df[col["time"]].values.astype(float)
    hi = df[col["horizon"]].values
    seq = df[col["chunk"]].values
    tick_ms = float(np.median(np.diff(t)) * 1000) if len(t) > 1 else 0.0
    lat = df[col["latency"]].dropna() if col["latency"] in df.columns else pd.Series(dtype=float)

    # A chunk boundary is where inference_seq changes — NOT horizon_idx == 0.
    # Prefetch skips the steps that elapsed in flight, so a chunk's first
    # executed horizon_idx is typically 7-12 and 0 may never occur.
    new_chunk = np.zeros(len(df), dtype=bool)
    if len(df):
        new_chunk[0] = True
        new_chunk[1:] = np.diff(seq) != 0

    dt_ms = np.diff(t) * 1000 if len(t) > 1 else np.array([])
    boundary_dt = dt_ms[new_chunk[1:]] if len(dt_ms) else np.array([])
    # Blocking-style run: boundaries carry a stall (the old play/freeze loop).
    # Only then does the tracking table's bnd column mean "after settle time".
    stalled_run = bool(
        len(boundary_dt) and np.median(boundary_dt) > cfg.stalled_run_min_boundary_ms
    )

    run: dict = {
        "joints": names,
        "meta": {
            "ticks": int(len(df)),
            "chunks": int(df[col["chunk"]].nunique()),
            "dur_s": round(float(t[-1] - t[0]), 1) if len(t) > 1 else 0.0,
            "tick_ms": round(tick_ms, 1),
            "lat_p50": round(float(lat.median()), 1) if len(lat) else None,
            "lat_p90": round(float(lat.quantile(0.9)), 1) if len(lat) else None,
            "lat_max": round(float(lat.max()), 1) if len(lat) else None,
            "stalled_run": stalled_run,
        },
        "cfg": run_meta or None,
        "bounds": [round(float(x), 3) for x in t[new_chunk]],
        "traces": {},
    }

    # Position within the executed part of the chunk (0 = first executed tick),
    # independent of the horizon_idx offset prefetch introduces.
    pos = np.zeros(len(df), dtype=int)
    if len(df):
        starts = np.where(new_chunk)[0]
        pos = np.arange(len(df)) - starts[np.searchsorted(starts, np.arange(len(df)), "right") - 1]
    mid_mask = pos >= 2
    bnd_mask = new_chunk

    def has(prefix, n):
        return f"{prefix}{n}" in df.columns

    stats = []
    for n in names:
        cmd = df[f"{col['cmd_prefix']}{n}"].values.astype(float)
        act = (
            df[f"{col['act_prefix']}{n}"].values.astype(float)
            if has(col["act_prefix"], n)
            else np.full_like(cmd, np.nan)
        )
        err = cmd - act
        abs_err = np.abs(err)
        k = estimate_lag(cmd, act, cfg.max_lag_ticks) if not np.isnan(act).all() else -1
        with np.errstate(invalid="ignore"):
            stats.append(
                {
                    "j": n,
                    "p50": _mrad(np.nanmedian(abs_err)) if not np.isnan(abs_err).all() else None,
                    "p95": _mrad(np.nanpercentile(abs_err, 95))
                    if not np.isnan(abs_err).all()
                    else None,
                    "lag": round(k * tick_ms) if k >= 0 else None,
                    "mid": _mrad(np.nanmedian(abs_err[mid_mask]))
                    if mid_mask.any() and not np.isnan(abs_err[mid_mask]).all()
                    else None,
                    # bnd is a settle diagnosis: it compares error after the
                    # boundary wait to mid-chunk error. Without a stall there
                    # is no wait, so the number would be meaningless.
                    "bnd": _mrad(np.nanmedian(abs_err[bnd_mask]))
                    if stalled_run
                    and bnd_mask.any()
                    and not np.isnan(abs_err[bnd_mask]).all()
                    else None,
                }
            )
        tr = {"cmd": decimate(t, cmd, cfg.buckets), "act": decimate(t, act, cfg.buckets),
              "err": decimate(t, err * 1000, cfg.buckets)}
        for key, prefix in (("vel", col["vel_prefix"]), ("eff", col["eff_prefix"])):
            if has(prefix, n):
                tr[key] = decimate(t, df[f"{prefix}{n}"].values.astype(float), cfg.buckets)
        run["traces"][n] = tr
    run["stats"] = stats

    # ---- raw arrays for semantic zoom -----------------------------------
    # The decimated traces above are the far view; zooming needs the real
    # samples. Position signals (cmd + actual) are stored raw; velocity and
    # effort stay decimated — they are read as envelopes. A run beyond the
    # size budget falls back to decimated-only, flagged, instead of producing
    # an unopenably large page.
    if len(df) * len(names) * 2 <= cfg.raw_max_points:
        raw: dict = {
            "t": [round(float(x), 3) for x in t],
            "hi": [int(x) for x in hi],
            "seq": [int(x) for x in seq],
            "j": {},
        }
        for n in names:
            cmd = df[f"{col['cmd_prefix']}{n}"].values.astype(float)
            aname = f"{col['act_prefix']}{n}"
            entry = {"cmd": _round_list(cmd, cfg.raw_decimals)}
            if aname in df.columns:
                entry["act"] = _round_list(
                    df[aname].values.astype(float), cfg.raw_decimals
                )
            raw["j"][n] = entry
        run["raw"] = raw
        # Per-tick command step (max over arm joints, mrad), full resolution —
        # the series behind the splice ratio, so the number can be *seen*.
        # dstep[i] spans t[i] -> t[i+1] and is plotted at t[i+1].
        arm_cols = [
            f"{col['cmd_prefix']}{n}" for n in names if cfg.finger_marker not in n
        ]
        if arm_cols and len(df) >= 2:
            with np.errstate(invalid="ignore"):
                d = np.abs(
                    np.diff(df[arm_cols].values.astype(float), axis=0)
                ).max(axis=1) * 1000
            run["dstep"] = _round_list(d, cfg.dstep_decimals)
    else:
        run["raw"] = None
        run["raw_omitted"] = True

    # seq id at each boundary, parallel to run["bounds"] — lets the page label
    # boundaries and jump to a chunk number from the tables.
    run["bound_seq"] = [int(x) for x in seq[new_chunk]]

    run["contacts"] = _contacts(df, names, t, cfg)
    run["grasps"] = _grasps(df, names, t, cfg)
    run["finger_status"] = _finger_status(df, names, cfg)
    run["profile"] = _chunk_profile(df, names, hi, new_chunk, cfg)
    run["schedule"] = _schedule(df, t, hi, seq, new_chunk, dt_ms, cfg)
    run["smooth"] = _smoothness(df, names, new_chunk, dt_ms, cfg)
    run["grasp_events"] = _grasp_attempts(df, names, t, hi, run_meta, cfg)
    run["violations"] = _violation_rates(df, run_meta, cfg)
    # Everything below that reads the chunk store must see a store that
    # provably belongs to THIS run — see _chunk_store_matches.
    if chunk_data is not None:
        why = _chunk_store_matches(chunk_data, df, names, hi, seq, cfg)
        if why:
            run["chunk_reject"] = why
            chunk_data = None

    run["overlap"] = _overlap(chunk_data, df, t, hi, seq, new_chunk, tick_ms, cfg)
    run["plans"] = _plan_store(chunk_data, names, t, hi, seq, new_chunk, tick_ms, cfg)
    run["pred"] = _prediction(chunk_data, names, cfg)
    return run


def _contacts(df, names, t, cfg: Options) -> list[dict]:
    """External-force events: effort spikes the rolling baseline can't explain."""
    col = cfg.column_names
    out = []
    for n in [x for x in names if cfg.finger_marker not in x]:
        cname = f"{col['eff_prefix']}{n}"
        if cname not in df.columns:
            continue
        eff = df[cname]
        r = (eff - eff.rolling(cfg.contact_window_ticks, center=True, min_periods=1).median()).values
        with np.errstate(invalid="ignore"):
            mad = np.nanmedian(np.abs(r - np.nanmedian(r)))
        if not np.isfinite(mad):
            mad = 0.0
        thr = max(cfg.contact_min_nm, cfg.contact_mad_k * 1.4826 * mad)
        for a, b in intervals(np.abs(r) > thr, cfg.merge_ticks):
            peak = r[a : b + 1][np.argmax(np.abs(r[a : b + 1]))]
            out.append(
                {
                    "t": round(float(t[a]), 1),
                    "dur": round(float((t[b] - t[a]) * 1000)),
                    "j": n,
                    "nm": round(float(peak), 2),
                }
            )
    return sorted(out, key=lambda e: e["t"])


def _finger_usable(cmd: np.ndarray, act: np.ndarray, cfg: Options) -> tuple[bool, str, float]:
    """Can "commanded shut but stopped short" mean anything for this finger?

    Two ways it cannot, both present in real logs:

    * the finger was never commanded to move (a parked or disabled side), so
      the range is ~0 and the blocked-threshold — a FRACTION of that range —
      collapses to sensor noise; and
    * the finger does not follow its command at all (unpowered / disabled
      gripper): actual sits wherever it sits, the gap to the command is
      permanent, and shading it as "holding an object" is simply wrong.

    Returns (usable, reason_if_not, range).
    """
    with np.errstate(invalid="ignore"):
        rng = float(np.nanpercentile(cmd, 95) - np.nanpercentile(cmd, 5))
    if not np.isfinite(rng) or rng < cfg.grasp_min_range:
        return False, "gripper parked (command never moves)", max(rng, 0.0)
    with np.errstate(invalid="ignore"):
        typical_gap = float(np.nanmedian(np.abs(act - cmd)))
    if not np.isfinite(typical_gap):
        return False, "no position feedback", rng
    if typical_gap > cfg.grasp_track_frac * rng:
        return False, "gripper does not follow its command (disabled?)", rng
    return True, "", rng


def _grasps(df, names, t, cfg: Options) -> dict:
    """Blocked-finger spans per finger joint: commanded shut, stopped short.

    Only for fingers that demonstrably track their command (see
    _finger_usable) — otherwise a permanently-ignored command would be shaded
    as a held object for the whole run.
    """
    col = cfg.column_names
    out = {}
    for n in [x for x in names if cfg.finger_marker in x]:
        aname = f"{col['act_prefix']}{n}"
        if aname not in df.columns:
            continue
        cmd = df[f"{col['cmd_prefix']}{n}"].values.astype(float)
        act = df[aname].values.astype(float)
        if len(cmd) == 0:
            out[n] = []
            continue
        usable, _, rng = _finger_usable(cmd, act, cfg)
        if not usable:
            out[n] = []
            continue
        spans = intervals(
            (act - cmd) > cfg.grasp_gap_frac * rng, cfg.merge_ticks, cfg.grasp_min_ticks
        )
        out[n] = [[round(float(t[a]), 1), round(float(t[b]), 1)] for a, b in spans]
    return out


def _finger_status(df, names, cfg: Options) -> dict:
    """Per finger: whether hold/grasp detection applies, and if not, why.

    The page shows this instead of silently drawing nothing, so an empty
    grasp list is never mistaken for "the gripper never grabbed anything".
    """
    col = cfg.column_names
    out = {}
    for n in [x for x in names if cfg.finger_marker in x]:
        aname = f"{col['act_prefix']}{n}"
        if aname not in df.columns:
            out[n] = "no position feedback"
            continue
        cmd = df[f"{col['cmd_prefix']}{n}"].values.astype(float)
        act = df[aname].values.astype(float)
        if len(cmd) == 0:
            out[n] = "no data"
            continue
        usable, reason, _ = _finger_usable(cmd, act, cfg)
        out[n] = "" if usable else reason
    return out


def _chunk_profile(df, names, hi, new_chunk, cfg: Options) -> dict:
    """Offset-corrected tracking error and command step size by observed
    horizon_idx (arm joints only). Adapts to any execution horizon and to the
    horizon_idx offset prefetch introduces (rows are indexed by the values
    that actually occur, which may start at 7-12 rather than 0).

    Chunk-switch ticks are EXCLUDED from the step-size medians: the command
    difference across a switch is the splice, which would contaminate
    whichever horizon_idx the switch happens to land on. The splice is
    reported separately by the smoothness block."""
    col = cfg.column_names
    arm = [
        n
        for n in names
        if cfg.finger_marker not in n and f"{col['act_prefix']}{n}" in df.columns
    ]
    prof = {"k": [], "err": [], "step": []}
    if not arm:
        return prof
    err_m = np.stack(
        [
            np.abs(
                (df[f"{col['cmd_prefix']}{n}"] - df[f"{col['act_prefix']}{n}"])
                - (df[f"{col['cmd_prefix']}{n}"] - df[f"{col['act_prefix']}{n}"]).median()
            ).values
            for n in arm
        ],
        axis=1,
    ).max(axis=1) * 1000
    step = np.abs(
        np.diff(df[[f"{col['cmd_prefix']}{n}" for n in arm]].values, axis=0)
    ).max(axis=1) * 1000
    # step[i] spans rows i -> i+1; it belongs to the splice when row i+1
    # starts a new chunk.
    step_ok = ~new_chunk[1:]
    for k in sorted(np.unique(hi)):
        m = hi == k
        sm = m[1:] & step_ok
        prof["k"].append(int(k))
        with np.errstate(invalid="ignore"):
            e = float(np.nanmedian(err_m[m])) if m.any() else float("nan")
            s = float(np.nanmedian(step[sm])) if sm.any() else float("nan")
        prof["err"].append(round(e, 1) if np.isfinite(e) else None)
        prof["step"].append(round(s, 1) if np.isfinite(s) else None)
    return prof


def _schedule(df, t, hi, seq, new_chunk, dt_ms, cfg: Options) -> dict:
    """Scheduling facts: replan cycle, skip, executed depth, steps per chunk,
    stalls/starvation, effective rate. All timing from t_rel (wall_time is
    quantized by the logger and unusable for intervals)."""
    col = cfg.column_names
    out: dict = {}
    if len(df) < 2:
        return out
    starts = np.where(new_chunk)[0]
    # steps executed per chunk (chunks get truncated when a new one lands)
    per_chunk = np.diff(np.append(starts, len(df)))
    out["cycle_p50"] = _pct(per_chunk, 50)
    out["cycle_p95"] = _pct(per_chunk, 95)
    out["cycle_min"] = int(per_chunk.min())
    out["cycle_max"] = int(per_chunk.max())
    # measured skip / executed depth, from observed horizon_idx per chunk
    g = pd.Series(hi).groupby(pd.Series(seq))
    skips = g.min().values
    depths = g.max().values
    out["skip_p50"] = _pct(skips, 50)
    out["depth_p50"] = _pct(depths, 50)
    out["depth_p95"] = _pct(depths, 95)
    out["depth_max"] = int(depths.max())
    # stalls: any tick interval beyond the threshold. Expected in the old
    # blocking loop; starvation in a prefetch run.
    stall = dt_ms > cfg.stall_gap_ms
    out["stall_count"] = int(stall.sum())
    dur_ms = float(t[-1] - t[0]) * 1000
    # Time lost to stalls = the excess over what those ticks would have taken
    # anyway at the nominal rate, not the whole interval.
    nominal = float(np.median(dt_ms)) if len(dt_ms) else 0.0
    lost = float((dt_ms[stall] - nominal).sum())
    out["stalled_frac"] = round(lost / dur_ms, 4) if dur_ms > 0 else None
    out["effective_hz"] = round(len(df) / (dur_ms / 1000), 1) if dur_ms > 0 else None
    # logger >= v0.4 columns (None-safe when absent)
    cl = _opt_series(df, col["chunk_len"])
    if cl is not None and cl.notna().any():
        out["chunk_len_p50"] = _pct(cl.dropna().values, 50)
    sk = _opt_series(df, col["skip_steps"])
    if sk is not None and sk.notna().any():
        out["skip_logged_p50"] = _pct(sk.dropna().values, 50)
    # No RTC metric here. rtc_applied only ever recorded that the CLIENT sent
    # the previous chunk back; a stock Gr00tPolicy discards `options` and
    # rebuilds the observation from video/state/language alone, so the number
    # described the client's intent and never the server's behaviour. The RTC
    # metrics live on the feat/rtc-metrics branch, to come back if and when
    # the server actually applies them.
    buf = _opt_series(df, col["buffer_len"])
    if buf is not None and buf.notna().any():
        out["starved_ticks"] = int((buf.dropna().values.astype(float) == 0).sum())
    lat = df[col["latency"]].dropna() if col["latency"] in df.columns else pd.Series(dtype=float)
    out["lat_p95"] = _pct(lat.values, 95) if len(lat) else None
    return out


def _smoothness(df, names, new_chunk, dt_ms, cfg: Options) -> dict:
    """Command smoothness, arm joints only (grippers step sharply by design).

    Splits |Δcmd| into at-splice (row starts a new chunk) vs within-chunk
    pools. splice_ratio = median at-splice / median within — 1x is perfectly
    smooth. Also command jerk, direction reversals at the splice, and the
    velocity spike near splices when velocity was logged."""
    col = cfg.column_names
    arm = [n for n in names if cfg.finger_marker not in n]
    out: dict = {}
    if not arm or len(df) < 3:
        return out
    def _med(x) -> float | None:
        """nan-safe median -> rounded float or None (never NaN: a truncated
        final CSV row NaN-pads the cmd block, and NaN must not reach JSON)."""
        with np.errstate(invalid="ignore"):
            v = float(np.nanmedian(x)) if len(x) else float("nan")
        return round(v, 1) if np.isfinite(v) else None

    cmds = df[[f"{col['cmd_prefix']}{n}" for n in arm]].values.astype(float)
    d1 = np.diff(cmds, axis=0)  # step vectors, per joint
    with np.errstate(invalid="ignore"):
        mag = np.abs(d1).max(axis=1) * 1000  # mrad
    at = new_chunk[1:]
    within = ~at
    out["step_within_p50"] = _med(mag[within])
    out["step_splice_p50"] = _med(mag[at])
    if (
        out["step_within_p50"] is not None
        and out["step_splice_p50"] is not None
        and out["step_within_p50"] > 0
    ):
        out["splice_ratio"] = round(out["step_splice_p50"] / out["step_within_p50"], 2)
    out["splice_p95"] = _pct(mag[at], 95) if at.any() else None
    finite_at = at & np.isfinite(mag)
    if finite_at.any():
        seq = df[col["chunk"]].values[1:]
        worst = int(np.argmax(np.where(finite_at, mag, -np.inf)))
        out["splice_max"] = round(float(mag[worst]), 1)
        out["splice_max_seq"] = int(seq[worst])
    # Command jerk (second difference). d2[i] involves steps d1[i] and
    # d1[i+1]; it belongs to the splice pool when EITHER touches a chunk
    # switch — a one-sided mask would leak half of every splice into the
    # 'within' baseline.
    with np.errstate(invalid="ignore"):
        d2 = np.abs(np.diff(d1, axis=0)).max(axis=1) * 1000
    touches = new_chunk[1:-1] | new_chunk[2:]
    out["jerk_within_p50"] = _med(d2[~touches])
    out["jerk_splice_p50"] = _med(d2[touches]) if touches.any() else None
    # Direction reversals: mean number of arm joints whose command reverses
    # sign with meaningful magnitude on both sides, splice vs within. "Any
    # joint reversed" is nearly always true with 14 arm joints, so only the
    # excess over the within baseline means anything. Same two-sided pooling
    # as jerk.
    if at.any():
        eps = 1e-4
        prev = d1[:-1]
        cur = d1[1:]
        with np.errstate(invalid="ignore"):
            rev = ((prev * cur) < 0) & (np.abs(prev) > eps) & (np.abs(cur) > eps)
        rev_n = rev.sum(axis=1).astype(float)
        rev_n[~(np.isfinite(prev).all(axis=1) & np.isfinite(cur).all(axis=1))] = np.nan
        if touches.any():
            out["rev_joints_splice_p50"] = _med(rev_n[touches])
        out["rev_joints_within_p50"] = _med(rev_n[~touches])

    # Direction continuity (NVIDIA's "momentum shift"): cosine between the
    # command's velocity vector before and after a moment. +1 means the motion
    # carries straight on; 0 is a right-angle turn; negative means it reverses.
    # Human demonstrations sit near +0.97, so this is the most direct measure
    # of whether the policy's output is a trajectory or a zigzag.
    #
    # Two numbers, because they answer different questions:
    #   within  - both steps inside one chunk. Low here means the MODEL is
    #             noisy (jitter inside a chunk), which no scheduling strategy
    #             can fix.
    #   splice  - last step of the old chunk vs first step of the new one,
    #             skipping the crossing step itself, exactly as the deployment
    #             guide defines it. Low only here means a seam problem.
    with np.errstate(invalid="ignore", divide="ignore"):
        vp, vn = d1[:-1], d1[1:]
        denom = np.linalg.norm(vp, axis=1) * np.linalg.norm(vn, axis=1)
        cos = np.where(denom > 1e-12, (vp * vn).sum(axis=1) / np.maximum(denom, 1e-12), np.nan)
    # A pair sits wholly inside a chunk when neither of its two steps crosses
    # a switch, i.e. rows i+1 and i+2 both continue the current chunk.
    def _med3(x) -> float | None:
        """Median rounded to 3 dp — a cosine needs more resolution than the
        1 dp _med used for millirad quantities."""
        with np.errstate(invalid="ignore"):
            v = float(np.nanmedian(x)) if len(x) else float("nan")
        return round(v, 3) if np.isfinite(v) else None

    inside = ~(new_chunk[1:-1] | new_chunk[2:])
    if inside.any():
        out["dircos_within"] = _med3(cos[inside])
    # Momentum across a switch: for a chunk starting at row s, compare the old
    # chunk's last step (d1[s-2]) with the new chunk's first step (d1[s]).
    starts = np.where(new_chunk)[0]
    starts = starts[(starts >= 2) & (starts + 1 < len(cmds))]
    if len(starts):
        with np.errstate(invalid="ignore", divide="ignore"):
            a_, b_ = d1[starts - 2], d1[starts]
            den2 = np.linalg.norm(a_, axis=1) * np.linalg.norm(b_, axis=1)
            cos_b = np.where(den2 > 1e-12, (a_ * b_).sum(axis=1) / np.maximum(den2, 1e-12), np.nan)
        out["dircos_splice"] = _med3(cos_b)
    # Velocity spike near splices, apples to apples: the same windowed-max
    # statistic is taken at splices and everywhere, and the ratio of their
    # medians is reported (max-at-splice over global median would inflate).
    vel_cols = [f"{col['vel_prefix']}{n}" for n in arm if f"{col['vel_prefix']}{n}" in df.columns]
    if vel_cols and at.any():
        with np.errstate(invalid="ignore"):
            vmag = np.abs(df[vel_cols].values.astype(float)).max(axis=1)
        w = cfg.splice_window_ticks
        roll = pd.Series(vmag).rolling(2 * w + 1, center=True, min_periods=1).max().values
        base = _med(roll)
        idxs = np.where(new_chunk)[0]
        idxs = idxs[idxs > 0]
        spike = _med(roll[idxs]) if len(idxs) else None
        if base and spike is not None:
            out["vel_spike_ratio_p50"] = round(spike / base, 2)
    return out


def _grasp_attempts(df, names, t, hi, run_meta: dict | None, cfg: Options) -> dict:
    """Per finger: every close attempt, with the horizon depth it was issued
    at, its command rise time (10->90% of the drop) and whether it succeeded
    (the finger stopped short = held something)."""
    col = cfg.column_names
    out: dict = {}
    for n in [x for x in names if cfg.finger_marker in x]:
        cmd = df[f"{col['cmd_prefix']}{n}"].values.astype(float)
        aname = f"{col['act_prefix']}{n}"
        act = df[aname].values.astype(float) if aname in df.columns else None
        if len(cmd) < 3:
            out[n] = []
            continue
        lo_v, hi_v = float(np.percentile(cmd, 5)), float(np.percentile(cmd, 95))
        rng = hi_v - lo_v
        if rng < cfg.grasp_min_range:
            out[n] = []
            continue
        # Same usability gate as _grasps: a finger that ignores its command
        # cannot have its held/air outcome judged from the command gap.
        if act is not None and not _finger_usable(cmd, act, cfg)[0]:
            act = None
        close_level = lo_v + cfg.grasp_close_frac * rng
        closed = cmd < close_level
        f_lo, f_hi = cfg.grasp_rise_fracs
        lvl_hi = lo_v + f_hi * rng  # 10% into the drop (still nearly open)
        lvl_lo = lo_v + f_lo * rng  # 90% into the drop (nearly closed)
        events = []
        prev_b = -1
        for a, b in intervals(closed, cfg.merge_ticks, cfg.grasp_min_ticks):
            # Rise time: walk back to the last tick above lvl_hi, forward to
            # the first tick below lvl_lo. Both walks are BOUNDED to this
            # attempt — backward by the previous attempt's end, forward by
            # this closed span's end — and yield None when the command never
            # crosses the level inside those bounds (a partial close). An
            # unbounded walk would inherit a crossing from a different
            # attempt and report a rise of tens of seconds.
            s = a
            while s > prev_b + 1 and cmd[s] < lvl_hi:
                s -= 1
            e = a
            while e < b and cmd[e] > lvl_lo:
                e += 1
            rise_ms = (
                round(float(t[e] - t[s]) * 1000)
                if e > s and cmd[s] >= lvl_hi and cmd[e] <= lvl_lo
                else None
            )
            success = None
            if act is not None:
                blocked = (act[a : b + 1] - cmd[a : b + 1]) > cfg.grasp_gap_frac * rng
                # A grab late in the span still counts: the success threshold
                # is deliberately smaller than the span-detection threshold.
                success = bool(blocked.sum() >= cfg.grasp_success_min_ticks)
            ev = {
                "t": round(float(t[a]), 1),
                # anchored where the close ramp begins, not where it crosses
                "hi": int(hi[s]),
                "rise_ms": rise_ms,
                "success": success,
            }
            events.append(ev)
            prev_b = b
        out[n] = events
    return out


def _violation_rates(df, run_meta: dict | None, cfg: Options) -> dict:
    """Fraction of ticks where the safety guard held a side instead of
    commanding it. A high rate invalidates that run's smoothness numbers.

    A disabled side is omitted (the client evaluates the limit check even for
    a parked arm, so its flag is noise), and NaN cells (truncated final row)
    are dropped rather than poisoning the rate."""
    col = cfg.column_names
    out = {}
    for key, cname, enable in (
        ("left", col["left_violation"], "enable_left_arm"),
        ("right", col["right_violation"], "enable_right_arm"),
    ):
        if isinstance(run_meta, dict) and run_meta.get(enable) is False:
            continue
        s = _opt_series(df, cname)
        if s is not None:
            s = s.dropna()
            if len(s):
                out[key] = round(float(s.values.astype(float).mean()), 4)
    return out


# --------------------------------------------- does this store belong to this run
def _chunk_store_matches(chunk_data, df, names, hi, seq, cfg: Options) -> str | None:
    """None if the chunk store provably belongs to this run; else why it does not.

    A `.chunks.npz` is matched to a CSV by filename alone, which is not
    evidence. A store left behind by an earlier client, an aborted run, or a
    different experiment sits next to the CSV looking exactly like a good one,
    and every metric derived from it — the plan's direction continuity, its
    acceleration, the usable horizon window, the overlap disagreement — comes
    out confident and wrong. That is worse than no store at all, because "no
    store" shows as an em dash and a wrong store shows as a number.

    The proof is already in the log, written twice by different code in the
    client. Each executed tick records the command as cmd_<joint> on its CSV
    row; the store records the same value as chunks[seq][horizon_idx]. If they
    agree across many chunks then the column order, the sequence indexing and
    the horizon indexing are all right, and the store is this run's. If they
    disagree, nothing else about the store can be trusted either.

    Deliberately a rejection, not a warning. The whole point is that these
    numbers look plausible when they are wrong, so a note nobody reads is not
    a guard.
    """
    col = cfg.column_names
    chunks = chunk_data.get("chunks") if isinstance(chunk_data, dict) else None
    if chunks is None or getattr(chunks, "ndim", 0) != 3 or chunks.shape[0] == 0:
        return "chunk store is empty or malformed"
    if chunks.shape[2] != len(names):
        return (f"chunk store is {chunks.shape[2]} joints wide but the CSV names "
                f"{len(names)} — it was written for a different robot or layout")

    cseq = np.asarray(chunk_data["seq"]).astype(int).ravel()
    by_seq = {int(s): k for k, s in enumerate(cseq)}
    logged = {int(s) for s in np.unique(seq) if np.isfinite(s)}
    shared = logged & set(by_seq)
    if not shared:
        return (f"chunk store holds sequences {cseq.min()}-{cseq.max()} but the run "
                f"executed {min(logged)}-{max(logged)} — no overlap at all")

    cmd = df[[f"{col['cmd_prefix']}{n}" for n in names]].values.astype(float)
    worst, worst_at, checked = 0.0, None, 0
    seen: set[int] = set()
    for i in range(len(df)):
        if not np.isfinite(seq[i]) or not np.isfinite(hi[i]):
            continue
        s = int(seq[i])
        if s not in by_seq:
            continue
        if s not in seen:
            if len(seen) >= cfg.chunk_align_chunks:
                continue
            seen.add(s)
        k = int(hi[i])
        c = chunks[by_seq[s]]
        if not 0 <= k < c.shape[0]:
            continue
        a, b = np.asarray(c[k], float), cmd[i]
        m = np.isfinite(a) & np.isfinite(b)
        if not m.any():
            continue
        e = float(np.max(np.abs(a[m] - b[m])))
        checked += 1
        if e > worst:
            worst, worst_at = e, (s, k, i)
    if not checked:
        return "chunk store shares sequence numbers with the run but no comparable step"
    if worst > cfg.chunk_align_tol_rad:
        s, k, i = worst_at
        a = np.asarray(chunks[by_seq[s]][k], float)
        with np.errstate(invalid="ignore"):
            j = int(np.nanargmax(np.abs(a - cmd[i])))
        return (f"chunk store disagrees with the commands this run actually sent: "
                f"chunk {s} step {k} has {names[j]} at {a[j]:.4f} rad where the log "
                f"commanded {cmd[i][j]:.4f} ({worst * 1000:.0f} mrad apart). "
                f"The file does not belong to this run — plan metrics withheld.")
    return None


# ------------------------------------------------- full-chunk overlap metrics
def _overlap(chunk_data, df, t, hi, seq, new_chunk, tick_ms, cfg: Options) -> dict | None:
    """Metrics that need the UNEXECUTED part of each chunk (<run>.chunks.npz).

    Alignment needs no extra bookkeeping: the CSV anchors each chunk in time.
    From chunk c's first executed row (t_first, hi_first), its step i — executed
    or not — targets t_first + (i - hi_first) * tick. Two consecutive chunks
    therefore describe a shared stretch of instants, and their disagreement
    over that whole overlap is the true splice number the executed-only
    boundary step approximates.

    Returns None when no chunk file was recorded (pre-chunk-logging runs).
    """
    col = cfg.column_names
    if chunk_data is None or len(df) < 2 or tick_ms <= 0:
        return None
    names = [c[len(col["cmd_prefix"]):] for c in df.columns if c.startswith(col["cmd_prefix"])]
    arm_idx = [k for k, n in enumerate(names) if cfg.finger_marker not in n]
    chunks = chunk_data["chunks"]
    if not arm_idx or chunks.shape[2] < len(names):
        return None
    cseq = chunk_data["seq"].astype(int)
    by_seq = {int(sq): k for k, sq in enumerate(cseq)}

    # Anchor each executed chunk: time of step 0 = t_first - hi_first * tick.
    starts = np.where(new_chunk)[0]
    anchor = {}
    for si in starts:
        anchor[int(seq[si])] = float(t[si]) - float(hi[si]) * tick_ms / 1000.0

    tick_s = tick_ms / 1000.0
    pair_med, pair_seq = [], []
    # (No frozen-region check: RTC never reaches the server. See
    #  feat/rtc-metrics for that measurement.)

    exec_seqs = sorted(anchor)
    for a_sq, b_sq in zip(exec_seqs[:-1], exec_seqs[1:]):
        ka, kb = by_seq.get(a_sq), by_seq.get(b_sq)
        if ka is None or kb is None:
            continue
        ca, cb = chunks[ka], chunks[kb]
        # offset in steps between the two chunks' anchors
        off = (anchor[b_sq] - anchor[a_sq]) / tick_s
        o = int(round(off))
        if abs(off - o) > 0.35 or o <= 0:
            continue  # anchors don't align to the tick grid (stall wobble)
        n = min(ca.shape[0] - o, cb.shape[0])
        if n < 3:
            continue
        d = np.abs(ca[o : o + n][:, arm_idx] - cb[:n][:, arm_idx]) * 1000.0
        valid = np.isfinite(d).any(axis=1)
        if not valid.any():
            continue
        with np.errstate(invalid="ignore"):
            dmax = np.nanmax(d[valid], axis=1)
        dmax = dmax[np.isfinite(dmax)]
        if not len(dmax):
            continue
        pair_med.append(float(np.median(dmax)))
        pair_seq.append(int(b_sq))

    out: dict = {"pairs": len(pair_med)}
    if pair_med:
        arr = np.asarray(pair_med)
        out["disagree_p50"] = round(float(np.median(arr)), 1)
        out["disagree_p95"] = _pct(arr, 95)
        worst = int(np.argmax(arr))
        out["disagree_max"] = round(float(arr[worst]), 1)
        out["disagree_max_seq"] = pair_seq[worst]

    # Discarded-tail quality: unexecuted steps vs what was ACTUALLY commanded
    # at those instants (from the CSV), aggregated by horizon_idx.
    cmd_all = df[[f"{col['cmd_prefix']}{n}" for n in names]].values.astype(float)
    tail_err: dict[int, list] = {}
    # deepest executed horizon_idx per chunk (rows are in order, so the last
    # row of each chunk wins)
    exec_depth: dict[int, int] = {}
    for i in range(len(df)):
        exec_depth[int(seq[i])] = int(hi[i])
    for sq, kk in by_seq.items():
        if sq not in anchor:
            continue
        depth = exec_depth.get(sq, -1)
        ch = chunks[kk]
        for step in range(depth + 1, ch.shape[0]):
            ti = anchor[sq] + step * tick_s
            # map through real time (not row index) so stalls don't misalign
            j = np.searchsorted(t, ti)
            if j >= len(t):
                break
            if j > 0 and abs(t[j - 1] - ti) < abs(t[j] - ti):
                j -= 1
            if abs(float(t[j]) - ti) > 0.6 * tick_s:
                continue
            pred = ch[step][arm_idx]
            actual_cmd = cmd_all[j][arm_idx]
            with np.errstate(invalid="ignore"):
                e = np.nanmax(np.abs(pred - actual_cmd)) * 1000.0
            if np.isfinite(e):
                tail_err.setdefault(step, []).append(float(e))
    if tail_err:
        ks = sorted(tail_err)
        out["tail"] = {"k": ks,
                       "err": [round(float(np.median(tail_err[k])), 1) for k in ks]}
        allv = [v for vs in tail_err.values() for v in vs]
        out["tail_err_p50"] = round(float(np.median(allv)), 1)
    return out


def _chunk_anchors(t, hi, seq, new_chunk, tick_ms) -> dict:
    """Time of each executed chunk's step 0: t_first - hi_first * tick.

    Every step of a chunk — executed or not — is placed from this anchor, so
    two chunks land on a shared time axis without extra bookkeeping.
    """
    out = {}
    for si in np.where(new_chunk)[0]:
        out[int(seq[si])] = float(t[si]) - float(hi[si]) * tick_ms / 1000.0
    return out


def _plan_store(chunk_data, names, t, hi, seq, new_chunk, tick_ms, cfg: Options) -> dict | None:
    """Per-chunk predicted trajectories for the plans view, plus the aggregate
    disagreement-vs-offset curve.

    Ships each chunk as: anchor time, skip applied, deepest executed step, and
    one array per joint. Regions (skipped head / executed /
    discarded tail) are derived on the page from these plus the run config, so
    changing a colour never means recomputing anything.
    """
    if chunk_data is None or tick_ms <= 0:
        return None
    chunks = chunk_data["chunks"]
    n_ch, H, D = chunks.shape
    if D < len(names) or n_ch == 0:
        return None
    if n_ch * H * len(names) > cfg.chunk_store_max_values:
        return {"omitted": True, "n_chunks": int(n_ch)}

    anchor = _chunk_anchors(t, hi, seq, new_chunk, tick_ms)
    depth: dict[int, int] = {}
    for i in range(len(t)):
        depth[int(seq[i])] = int(hi[i])

    cseq = chunk_data["seq"].astype(int)
    skips = chunk_data["skip"].astype(int) if "skip" in chunk_data else np.zeros(n_ch, int)
    keep = [k for k, sq in enumerate(cseq) if int(sq) in anchor]
    if not keep:
        return None

    store: dict = {
        "seq": [int(cseq[k]) for k in keep],
        "t0": [round(anchor[int(cseq[k])], 3) for k in keep],
        "skip": [int(skips[k]) for k in keep],
        "depth": [int(depth.get(int(cseq[k]), -1)) for k in keep],
        "H": int(H),
        "tick_s": round(tick_ms / 1000.0, 5),
        "j": {},
    }
    for ji, n in enumerate(names):
        col_vals = []
        for k in keep:
            v = chunks[k][:, ji]
            col_vals.append([None if not np.isfinite(x) else round(float(x), 4) for x in v])
        store["j"][n] = col_vals

    # Aggregate: |old plan - new plan| by steps since the switch, over every
    # consecutive pair, max across arm joints (same pooling as the metric).
    arm_idx = [i for i, n in enumerate(names) if cfg.finger_marker not in n]
    by_seq = {int(sq): k for k, sq in enumerate(cseq)}
    per_off: dict[int, list] = {}
    ex = sorted(anchor)
    tick_s = tick_ms / 1000.0
    for a_sq, b_sq in zip(ex[:-1], ex[1:]):
        ka, kb = by_seq.get(a_sq), by_seq.get(b_sq)
        if ka is None or kb is None:
            continue
        off = (anchor[b_sq] - anchor[a_sq]) / tick_s
        o = int(round(off))
        if abs(off - o) > 0.35 or o <= 0:
            continue
        n_ov = min(H - o, H)
        for k in range(n_ov):
            d = np.abs(chunks[ka][o + k, arm_idx] - chunks[kb][k, arm_idx]) * 1000.0
            if np.isfinite(d).any():
                with np.errstate(invalid="ignore"):
                    per_off.setdefault(k, []).append(float(np.nanmax(d)))
    if per_off:
        ks = sorted(per_off)
        store["agg"] = {
            "k": ks,
            "p50": [round(float(np.median(per_off[k])), 1) for k in ks],
            "p10": [round(float(np.percentile(per_off[k], 10)), 1) for k in ks],
            "p90": [round(float(np.percentile(per_off[k], 90)), 1) for k in ks],
            "n": [len(per_off[k]) for k in ks],
        }
    return store


# ------------------------------------------------ what the model itself emitted
def _nanmax_last(v: np.ndarray) -> np.ndarray:
    """Max over the last axis; NaN for an all-NaN row, and no warning for it.

    Chunks shorter than the horizon are NaN-padded, so plain np.nanmax would
    spend the run warning about all-NaN slices.
    """
    ok = np.isfinite(v).any(axis=-1)
    out = np.full(v.shape[:-1], np.nan)
    if ok.any():
        out[ok] = np.nanmax(v[ok], axis=-1)
    return out


def _prediction(chunk_data, names, cfg: Options) -> dict | None:
    """The quality of the model's raw output, before the client touches it.

    Every other smoothness number here is measured on the executed command —
    which is a stitched-together selection of steps from many chunks, shaped
    by the execution horizon, the prefetch skip and where the boundaries
    happened to fall. This one reads the 40-step chunks straight out of
    <run>.chunks.npz, one chunk at a time, so none of that can influence it.
    It is the difference between "what the robot was told" and "what the
    policy actually thinks the trajectory is".

    That distinction is the deployment guide's Case A test. If these numbers
    are bad, the problem is the policy or the training data, and no amount of
    scheduling, blending or chunk stitching will rescue the run.

    Two quantities per the guide, both inside a single chunk:
      dircos - cosine between consecutive step vectors. Human demonstrations
               sit near +0.97; 0 is a right-angle turn every tick; negative
               means the plan doubles back on itself.
      accel  - |x[k+1] - 2 x[k] + x[k-1]|, the intra-chunk acceleration, in
               mrad per tick squared.

    Both are also returned per horizon step, because a model that is smooth
    at k=0 and ragged at k=35 is telling you how far ahead it can be trusted
    — which is exactly the number you need to choose an execution horizon.

    Returns None when the run has no chunk file (nothing to measure).
    """
    if chunk_data is None:
        return None
    chunks = chunk_data.get("chunks")
    if chunks is None or chunks.ndim != 3 or chunks.shape[0] == 0 or chunks.shape[1] < 3:
        return None
    arm = [i for i, n in enumerate(names) if cfg.finger_marker not in n]
    if not arm or chunks.shape[2] < len(names):
        return None

    x = chunks[:, :, arm].astype(float)              # (n_chunks, H, arm joints)
    with np.errstate(invalid="ignore"):
        d1 = np.diff(x, axis=1)                      # step vectors, (n, H-1, A)
        a, b = d1[:, :-1, :], d1[:, 1:, :]           # consecutive pairs
        den = np.linalg.norm(a, axis=2) * np.linalg.norm(b, axis=2)
        cos = np.where(den > 1e-12, (a * b).sum(axis=2) / np.maximum(den, 1e-12), np.nan)
        acc = _nanmax_last(np.abs(b - a)) * 1000.0   # mrad/tick^2, (n, H-2)
        step = _nanmax_last(np.abs(d1)) * 1000.0     # mrad/tick,   (n, H-1)

    def med(v, dp=1):
        v = v[np.isfinite(v)]
        return round(float(np.median(v)), dp) if len(v) else None

    out: dict = {"n_chunks": int(chunks.shape[0]), "H": int(chunks.shape[1])}
    out["dircos_p50"] = med(cos, 3)
    out["accel_p50"] = med(acc)
    out["accel_p95"] = _pct(acc[np.isfinite(acc)], 95)
    out["step_p50"] = med(step)
    # Fraction of consecutive-step pairs that actually reverse direction. A
    # median cosine hides this: a plan can average near zero either by turning
    # a steady right angle or by alternating forwards and backwards.
    fin = cos[np.isfinite(cos)]
    if len(fin):
        out["reversal_frac"] = round(float((fin < 0).mean()), 3)
    # Per horizon step, so the depth-dependence is visible rather than pooled.
    out["k"] = list(range(cos.shape[1]))
    out["dircos_k"] = [med(cos[:, k], 3) for k in range(cos.shape[1])]
    out["accel_k"] = [med(acc[:, k]) for k in range(acc.shape[1])]
    out["step_k"] = [med(step[:, k]) for k in range(step.shape[1])]
    return out
