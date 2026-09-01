# Features

What the app does today, and where in the code each piece lives.

## The app window

- **Choose folder…** — scans the folder for `*.csv` (case-insensitive) and
  lists what it found.
- **Choose CSV file(s)…** — pick individual runs instead of a whole folder.
- **Build dashboard** — processes every file with a progress bar (the UI
  never freezes; the build runs on a worker thread).
- Remembers the last folder between sessions (`~/.run_browser_state.json`).
- Unreadable files are skipped, and a warning lists exactly which and why —
  a bad file never kills the build.
- **open in browser when done** — the finished page opens automatically.

## The command line

```bash
python -m run_browser                              # opens the window
python -m run_browser <dir|csv...> [-o out.html]   # headless build
```

Headless mode prints per-file progress and skipped-file reasons; exit codes
are clean (0 ok, 1 build failed, 2 bad arguments) so it can run over SSH or
in scripts.

## The generated page

One self-contained HTML file — data embedded, opens from disk anywhere,
nothing to install for the reader. Light and dark theme follow the system.

- **Run switcher** — every CSV becomes a run in the sidebar; one click swaps
  the entire page. Duplicate filenames from different folders are
  disambiguated, never silently merged.
- **Five signal views** — position (commanded + actual), error, velocity,
  effort, and **cmd step** (per-tick `|Δcmd|` max over arm joints — the series
  behind the splice ratio, with the within-chunk median as a reference line).
- **Semantic zoom** — the page embeds the raw cmd/actual samples (size-guarded
  in `config.py`; oversize runs fall back to decimated, flagged on the chip)
  and re-decimates at draw time. Scroll to zoom, drag to pan, double-click to
  reset; the window is shared across all panels so joints stay time-aligned.
  Levels of detail as you close in: chunk labels with splice sizes in mrad,
  then one dot per sample with its `horizon_idx` underneath. X is `t_rel`, so
  blocking-run stalls appear as real gaps.
- **Jump links** — contact rows, grasp attempts and the worst-splice entry in
  Run facts move the plots to that moment or chunk.
- **Joint filter** — all / left / right.
- **Click a panel's title to enlarge it** (the plot area itself zooms/pans);
  the enlarged view shares the same window and interactions.
- **Overlays** — chunk-boundary markers and grasp shading, each toggleable.
- **Compare mode** — overlay any second run dashed, with side-by-side
  tracking and chunk-profile tables (handles runs with different execution
  horizons).
- **Tables** — tracking stats (p50/p95/lag/mid/bnd), Run facts (scheduling,
  smoothness, safety), chunk profile, contact events, grasp spans and close
  attempts. See [READING_THE_DASHBOARD.md](READING_THE_DASHBOARD.md) for how
  to read each.
- **Chunk-profile plot** — error and command step vs `horizon_idx` as curves
  (compare run overlaid), so the knee where late steps degrade is visible at
  a glance; the exact numbers stay in the table below it.
- **Step distribution strip** — within-chunk vs at-splice `|Δcmd|` histograms,
  showing whether a splice ratio is a consistent offset or a few outliers.
- **Run matrix page** — one row per run: sidecar config beside measured
  behaviour (cycle, skip, depth p95, splice ratio, stalls, effective Hz,
  grasp success, latency, limit-guard rate) with pass/fail verdict chips,
  plus splice-vs-cycle and grasp-success-vs-depth scatter plots.

## Prefetch / RTC awareness (client v0.4+)

- Chunk boundaries come from `inference_seq` changes, so prefetch runs
  (where `horizon_idx` never hits 0) are read correctly alongside old
  blocking runs in the same folder.
- The `<run>.meta.json` sidecar is picked up automatically and shown in the
  chips, Run facts and the matrix; runs without one say "config unknown".
- The new per-chunk columns (`chunk_len`, `skip_steps`, `rtc_applied`,
  `buffer_len`) feed the scheduling metrics when present and degrade to "—"
  when not.
- The tracking table's `bnd` settle diagnosis is computed only for runs whose
  boundaries actually stalled; long tick gaps in a prefetch run are reported
  as starvation instead of expected boundaries.

## Robustness (all verified against crafted bad inputs)

- Missing velocity/effort columns → the run still builds; those views say
  "no data for this signal".
- Missing required columns, header-only files, garbage files → skipped with
  a clear reason.
- One-row files, dropped sensor samples (NaN cells) → handled; a NaN can
  never poison a statistic or reach the page as a bare `NaN`.
- Output path in a folder that doesn't exist yet → created up front, before
  any processing time is spent.

## Extending it

The split is the feature — each change has exactly one home:

| I want to… | edit |
|---|---|
| change a threshold, window, filename, or highlight level | `config.py` |
| add/adjust a metric or detector | `analysis.py` |
| change the page's look, layout, or interactions | `template.py` |
| change how files are found or runs are named | `builder.py` |
| change the window itself | `app.py` |

Conventions that keep it robust when extending:

- `analysis.py` outputs plain JSON-ready dicts; `None` (never NaN) means
  "not available", and the page renders it as "—".
- Joint names come from the CSV header; nothing assumes a joint count or a
  specific robot. Baselines (gravity, sag offsets) are measured from each
  run itself, not modeled — so the metrics transfer to other arms.
- The CSV schema is described in `config.py:column_names`; if the logger's
  column names ever change, that dict is the only place to update.
