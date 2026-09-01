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
def process_run(csv_path: Path, cfg: Options, run_meta: dict | None = None) -> dict:
    """Everything the dashboard shows for one run, as one JSON-ready dict.

    run_meta is the parsed .meta.json sidecar (None for pre-v0.4 logs); it is
    both echoed into the result and used where a metric needs a configured
    value (e.g. the RTC overlap region).
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
    rtc = _opt_series(df, col["rtc_applied"])
    if rtc is not None and rtc.notna().any():
        v = rtc.dropna().values.astype(float)
        out["rtc_applied_frac"] = round(float(v.mean()), 3)
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
    at, its command rise time (10->90% of the drop — RTC ramping lengthens
    it), whether it fell inside the configured RTC overlap region, and
    whether it succeeded (the finger stopped short = held something)."""
    col = cfg.column_names
    out: dict = {}
    overlap = None
    if isinstance(run_meta, dict) and run_meta.get("rtc_enable"):
        overlap = run_meta.get("rtc_overlap_steps")
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
                # the closed threshold — the ramp start is what RTC blends
                "hi": int(hi[s]),
                "rise_ms": rise_ms,
                "success": success,
            }
            if overlap is not None:
                ev["in_overlap"] = bool(hi[s] < overlap)
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
