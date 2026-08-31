"""The small desktop app: pick a folder or CSV files, build, open in browser.

Tkinter only (ships with Python) — no extra installs on Windows or Linux.
All analysis lives in analysis.py, the page in template.py, options in
config.py; this file is only the window and the buttons.
"""

import json
import threading
import tkinter as tk
import webbrowser
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from .builder import build, find_csvs
from .config import DEFAULTS

STATE_FILE = Path.home() / ".run_browser_state.json"


class App:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title(DEFAULTS.page_title)
        self.root.geometry("560x460")
        self.root.minsize(480, 380)
        self.targets: list[Path] = []

        pad = {"padx": 10, "pady": 4}
        frm = ttk.Frame(self.root)
        frm.pack(fill="both", expand=True)

        row = ttk.Frame(frm)
        row.pack(fill="x", **pad)
        ttk.Button(row, text="Choose folder…", command=self.pick_folder).pack(side="left")
        ttk.Button(row, text="Choose CSV file(s)…", command=self.pick_files).pack(
            side="left", padx=6
        )
        self.count_var = tk.StringVar(value="nothing selected")
        ttk.Label(row, textvariable=self.count_var).pack(side="left", padx=8)

        self.listbox = tk.Listbox(frm, height=12, activestyle="none")
        self.listbox.pack(fill="both", expand=True, **pad)

        row2 = ttk.Frame(frm)
        row2.pack(fill="x", **pad)
        self.open_var = tk.BooleanVar(value=DEFAULTS.open_browser)
        ttk.Checkbutton(row2, text="open in browser when done", variable=self.open_var).pack(
            side="left"
        )
        self.build_btn = ttk.Button(row2, text="Build dashboard", command=self.start_build)
        self.build_btn.pack(side="right")

        self.progress = ttk.Progressbar(frm, mode="determinate")
        self.progress.pack(fill="x", **pad)
        self.status_var = tk.StringVar(value="")
        ttk.Label(frm, textvariable=self.status_var, foreground="#5A6B7A").pack(
            fill="x", padx=10, pady=(0, 10)
        )

        self._restore_last()

    # ------------------------------------------------------------- selection
    def _restore_last(self):
        try:
            last = json.loads(STATE_FILE.read_text()).get("last")
            if last and Path(last).exists():
                self.set_targets([Path(last)])
        except Exception:
            pass

    def _remember(self, target: Path):
        try:
            STATE_FILE.write_text(json.dumps({"last": str(target)}))
        except Exception:
            pass

    def pick_folder(self):
        d = filedialog.askdirectory(title="Folder with run CSVs")
        if d:
            self.set_targets([Path(d)])
            self._remember(Path(d))

    def pick_files(self):
        fs = filedialog.askopenfilenames(
            title="Run CSV files", filetypes=[("CSV files", "*.csv")]
        )
        if fs:
            self.set_targets([Path(f) for f in fs])
            self._remember(Path(fs[0]).parent)

    def set_targets(self, targets: list[Path]):
        self.targets = targets
        csvs = []
        for t in targets:
            csvs.extend(find_csvs(t))
        self.listbox.delete(0, "end")
        for c in csvs:
            self.listbox.insert("end", c.name)
        src = targets[0] if len(targets) == 1 else f"{len(targets)} files"
        self.count_var.set(f"{len(csvs)} csv · {src}")

    # ----------------------------------------------------------------- build
    def start_build(self):
        if not self.targets:
            messagebox.showinfo("Run Browser", "Choose a folder or CSV files first.")
            return
        self.build_btn.state(["disabled"])
        self.progress["value"] = 0
        threading.Thread(target=self._build_thread, daemon=True).start()

    def _ui(self, fn, *args):
        """Schedule a UI update from the worker thread; ignore it if the
        window was closed mid-build."""
        try:
            self.root.after(0, fn, *args)
        except (RuntimeError, tk.TclError):
            pass

    def _build_thread(self):
        def cb(name, i, total):
            self._ui(self._on_progress, name, i, total)

        try:
            out, skipped = build(self.targets, cfg=DEFAULTS, progress=cb)
            self._ui(self._on_done, out, skipped, None)
        except Exception as exc:
            self._ui(self._on_done, None, [], str(exc))

    def _on_progress(self, name, i, total):
        self.progress["maximum"] = total
        self.progress["value"] = i
        self.status_var.set(f"[{i}/{total}] {name}")

    def _on_done(self, out, skipped, error):
        self.build_btn.state(["!disabled"])
        if error:
            self.status_var.set("failed")
            messagebox.showerror("Run Browser", error)
            return
        note = f"  ({len(skipped)} file(s) skipped)" if skipped else ""
        self.status_var.set(f"done{note} → {out}")
        if skipped:
            messagebox.showwarning(
                "Run Browser",
                "Some files could not be read and were left out:\n\n" + "\n".join(skipped),
            )
        if self.open_var.get():
            webbrowser.open(out.resolve().as_uri())

    def run(self):
        self.root.mainloop()


def main():
    App().run()


if __name__ == "__main__":
    main()
