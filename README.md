# Adibot Run Browser

A small desktop app that turns the robot-run CSV logs written by the adibot
inference client into one interactive dashboard page. Pick a folder (or
individual CSV files), press **Build dashboard**, and a self-contained HTML
page opens in your browser — every run, every joint, every signal, plus the
derived tables (tracking error, contact events, grasps, chunk profile).
The plots hold the raw samples: scroll to zoom into any moment — down to one
dot per control tick with its place-in-chunk underneath — drag to pan, hover
to read exact values, and click a contact or grasp in the tables to jump
straight to it. Every section can be collapsed, and runs you do not want in a
comparison can be hidden.

No server, no internet, no dependencies beyond Python + numpy + pandas.
The generated page is a single file you can copy anywhere or send to a
colleague — the data is embedded in it.

Two pages: **signals** (per-joint plots and per-run tables for one run, with an
optional second run overlaid) and the **run matrix** (one row per run —
configuration beside measured behaviour, with pass/fail verdicts — for deciding
which configuration wins).

## Install (Linux)

Tested on Ubuntu 22.04 / Debian 12 with Python 3.10+.

**1. Install the prerequisites.** `python3-tk` is what draws the app window —
without it the command-line mode still works but the window will not open.

```bash
sudo apt update && sudo apt install -y python3 python3-pip python3-tk git
```

**2. Get the code.** This creates a folder called `adibot_run_browser` inside
whatever directory you are standing in. The example puts it in your home
directory:

```bash
cd ~ && git clone https://github.com/raghajuttu/adibot_run_browser.git
```

You now have `~/adibot_run_browser`. **That folder is what the rest of this
README means by "the project folder".**

**3. Install the two Python packages it needs:**

```bash
cd ~/adibot_run_browser && pip3 install numpy pandas
```

On Ubuntu 23.04+ and Debian 12+, `pip3 install` may refuse with
`externally-managed-environment`. Either install the system packages instead
(`sudo apt install python3-numpy python3-pandas`) or use a virtual environment:

```bash
cd ~/adibot_run_browser && python3 -m venv .venv && . .venv/bin/activate && pip install numpy pandas
```

With a venv you must run `. ~/adibot_run_browser/.venv/bin/activate` once in
every new terminal before using the commands below.

## Run it (Linux)

**Every command below must be run from the project folder** — the one holding
the `run_browser/` directory. That is what `python3 -m run_browser` needs in
order to find the code. Check you are in the right place:

```bash
cd ~/adibot_run_browser && ls
```

You should see `run_browser`, `docs`, `README.md`. If instead you get
`No module named run_browser` when you run the app, you are in the wrong
directory — `cd ~/adibot_run_browser` and try again.

### With the window (pick folders by clicking)

```bash
cd ~/adibot_run_browser && python3 -m run_browser
```

A small window opens. Press **Choose folder…** and select the directory holding
your run CSVs (for example `~/adibot_logs`), or **Choose CSV file(s)…** to pick
individual runs. It lists what it found; press **Build dashboard**. When the
progress bar finishes, the dashboard opens in your browser automatically.

> Running over SSH? The window needs a graphical display. Either connect with
> `ssh -X user@robot` (X11 forwarding) or skip the window and use the
> command-line form below — which is usually the better choice on a robot.

### Without a window (SSH-friendly)

Give it a folder of CSVs, or individual files, and where to write the page:

```bash
cd ~/adibot_run_browser && python3 -m run_browser ~/adibot_logs -o ~/run-browser.html
```

It prints one line per file as it goes, names any file it had to skip, and ends
with `wrote /home/you/run-browser.html`. Open that file in any browser:

```bash
xdg-open ~/run-browser.html
```

More forms:

```bash
# a single run
python3 -m run_browser ~/adibot_logs/E014_c25k.csv -o ~/one-run.html

# several specific runs in one page
python3 -m run_browser ~/adibot_logs/E004_c25k.csv ~/adibot_logs/E008_c25k.csv -o ~/two-runs.html

# leave out -o: the page is written next to the data, as run-browser.html
python3 -m run_browser ~/adibot_logs
```

Exit codes for scripting: `0` success, `1` nothing could be built, `2` bad
arguments.

### Analysing logs that live on the robot

The dashboard is a single self-contained file, so build it wherever the CSVs
are and copy the result:

```bash
# on the robot
python3 -m run_browser ~/adibot_logs -o ~/run-browser.html
# from your laptop
scp user@robot:~/run-browser.html . && xdg-open run-browser.html
```

Or copy the logs to your laptop and build there — either works, the page is the
same.

## Run it (Windows)

Double-click **`RunBrowser.bat`** in the project folder. If Windows asks which
app to open `RunBrowser.pyw` with, use the `.bat` instead — it calls
`pythonw.exe` directly.

The command-line forms are identical, using `python` instead of `python3`:

```bash
python -m run_browser C:\my_logs -o C:\my_logs\run-browser.html
```

## Requirements

Python 3.10 or newer, `numpy`, `pandas`. Tkinter (`python3-tk`) is needed only
for the window, not for the command-line mode. No internet connection is used
at any point, and nothing is uploaded anywhere.

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
Those come from the deployment client
[v0.5.0+](https://github.com/raghajuttu/groot_deployment).

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
