# Adibot Run Browser

A small desktop app that turns the robot-run CSV logs written by the adibot
inference client into one interactive dashboard page. Pick a folder (or
individual CSV files), press **Build dashboard**, and a self-contained HTML
page opens in your browser — every run, every joint, every signal, plus the
derived tables (tracking error, contact events, grasps, chunk profile).

No server, no internet, no dependencies beyond Python + numpy + pandas.
The generated page is a single file you can copy anywhere or send to a
colleague — the data is embedded in it.

Two pages: **signals** (per-joint plots and per-run tables for one run, with an
optional second run overlaid) and the **run matrix** (one row per run —
configuration beside measured behaviour, with pass/fail verdicts — for deciding
which configuration wins).

## Run it

**Windows** — double-click `RunBrowser.bat`.

**Linux / macOS** — from this folder:

```bash
python3 -m run_browser
```

**Headless / over SSH** (no window, just build the page):

```bash
python3 -m run_browser <folder-or-csv...> [-o out.html]
# e.g.
python3 -m run_browser ~/robot_logs/latency_test_24.08.26 -o run-browser.html
```

Requirements: Python 3.10+, `numpy`, `pandas`. Tkinter ships with Python on
Windows; on some Linux distros install it with `sudo apt install python3-tk`.

## What it expects

CSV logs written by the adibot GR00T client (one row per 30 Hz control tick):
`t_rel`, `inference_seq`, `horizon_idx`, `latency_ms`, and per joint
`cmd_<joint>`, `actual_pos_<joint>`, `actual_vel_<joint>`, `actual_eff_<joint>`.
Joint names are discovered from the header — nothing about the 16-joint
bimanual layout is hardcoded. Files with missing velocity/effort columns still
work; unreadable files are skipped and reported, never fatal.

**Blocking, prefetch and RTC runs are all read correctly, side by side in the
same folder.** Chunk boundaries are detected from `inference_seq` changes, so a
prefetch run — where `horizon_idx` starts at 7–12 instead of 0 because the steps
that expired in flight are skipped — is not misread. Client v0.4+ also writes
four extra columns (`chunk_len`, `skip_steps`, `rtc_applied`, `buffer_len`) and
a `<run>.meta.json` sidecar holding the run's configuration; both are picked up
automatically, and runs without them show "config unknown" rather than failing.

## Documentation

- [docs/READING_THE_DASHBOARD.md](docs/READING_THE_DASHBOARD.md) — what every
  plot and table means and how to read it, starting from what a *chunk* is.
- [docs/FEATURES.md](docs/FEATURES.md) — everything the app can do, and where
  in the code to change or extend it.

## Code layout

Deliberately split so each concern is edited in exactly one place:

| file | owns |
|---|---|
| `run_browser/config.py` | every tunable option and threshold |
| `run_browser/analysis.py` | the metrics: tracking, contacts, grasps, chunk profile |
| `run_browser/template.py` | the dashboard page: all HTML / CSS / JS |
| `run_browser/builder.py` | glue: files → analysis → page |
| `run_browser/app.py` | the desktop window (folder/file picker, progress) |
| `run_browser/__main__.py` | CLI entry point |
