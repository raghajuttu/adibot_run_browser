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


def _mrad(value: float) -> float | None:
    """rad -> mrad rounded, mapping NaN to None so it reaches JSON as null,
    never as a bare NaN token."""
    v = float(value)
    return None if not np.isfinite(v) else round(v * 1000, 1)


# ---------------------------------------------------------------- per-run work
def process_run(csv_path: Path, cfg: Options) -> dict:
    """Everything the dashboard shows for one run, as one JSON-ready dict."""
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
    tick_ms = float(np.median(np.diff(t)) * 1000) if len(t) > 1 else 0.0
    lat = df[col["latency"]].dropna() if col["latency"] in df.columns else pd.Series(dtype=float)

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
        },
        "bounds": [round(float(x), 3) for x in t[hi == 0]],
        "traces": {},
    }

    h_max = int(hi.max()) if len(hi) else 0
    lo = max(1, round(h_max * 0.2))
    hi_cut = max(2, round(h_max * 0.8))
    mid_mask = (hi > lo) & (hi < hi_cut)
    bnd_mask = hi == 0

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
                    "bnd": _mrad(np.nanmedian(abs_err[bnd_mask]))
                    if bnd_mask.any() and not np.isnan(abs_err[bnd_mask]).all()
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

    run["contacts"] = _contacts(df, names, t, cfg)
    run["grasps"] = _grasps(df, names, t, cfg)
    run["profile"] = _chunk_profile(df, names, hi, cfg)
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


def _grasps(df, names, t, cfg: Options) -> dict:
    """Blocked-finger spans per finger joint: commanded shut, stopped short."""
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
        rng = max(float(np.percentile(cmd, 95) - np.percentile(cmd, 5)), 1e-4)
        spans = intervals(
            (act - cmd) > cfg.grasp_gap_frac * rng, cfg.merge_ticks, cfg.grasp_min_ticks
        )
        out[n] = [[round(float(t[a]), 1), round(float(t[b]), 1)] for a, b in spans]
    return out


def _chunk_profile(df, names, hi, cfg: Options) -> dict:
    """Offset-corrected tracking error and command step size by position within
    the chunk (arm joints only). Adapts to any execution horizon."""
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
    for k in sorted(np.unique(hi)):
        m = hi == k
        prof["k"].append(int(k))
        with np.errstate(invalid="ignore"):
            e = float(np.nanmedian(err_m[m])) if m.any() else float("nan")
            s = float(np.nanmedian(step[m[1:]])) if m[1:].any() else float("nan")
        prof["err"].append(round(e, 1) if np.isfinite(e) else None)
        prof["step"].append(round(s, 1) if np.isfinite(s) else None)
    return prof
