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
- **Four signal views** — position (commanded + actual), error, velocity,
  effort. Raw data, full timeline; min/max decimation preserves spikes.
- **Joint filter** — all / left / right.
- **Click any panel to enlarge.**
- **Overlays** — chunk-boundary markers and grasp shading, each toggleable.
- **Compare mode** — overlay any second run dashed, with side-by-side
  tracking and chunk-profile tables (handles runs with different execution
  horizons).
- **Tables** — tracking stats (p50/p95/lag/mid/bnd), chunk profile,
  contact events, grasp spans. See
  [READING_THE_DASHBOARD.md](READING_THE_DASHBOARD.md) for how to read each.

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
