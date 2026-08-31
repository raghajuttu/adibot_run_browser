"""Glue: collect CSVs, run the analysis, render the page, write the file.

Knows nothing about metrics (analysis.py) or looks (template.py).
"""

from datetime import date
from pathlib import Path
from typing import Callable

from .analysis import process_run
from .config import DEFAULTS, Options
from .template import render


def find_csvs(target: Path) -> list[Path]:
    """A directory yields every CSV inside it; a file yields itself.
    Suffix matching is case-insensitive on every platform."""
    if target.is_dir():
        return sorted(
            (p for p in target.iterdir() if p.is_file() and p.suffix.lower() == ".csv"),
            key=lambda p: p.name.lower(),
        )
    if target.is_file() and target.suffix.lower() == ".csv":
        return [target]
    return []


def _unique_key(stem: str, path: Path, taken: dict) -> str:
    """Run name for the sidebar: the file stem, disambiguated with the parent
    directory (then a counter) when two files share a name."""
    if stem not in taken:
        return stem
    candidate = f"{path.parent.name}/{stem}"
    n = 2
    while candidate in taken:
        candidate = f"{path.parent.name}/{stem} ({n})"
        n += 1
    return candidate


def build(
    targets: list[Path],
    out_path: Path | None = None,
    cfg: Options = DEFAULTS,
    progress: Callable[[str, int, int], None] | None = None,
) -> tuple[Path, list[str]]:
    """Build the dashboard from files and/or directories.

    Args:
        targets: CSV files and/or directories containing CSVs.
        out_path: where to write the page. Default: next to the first target.
        cfg: options (see config.py).
        progress: optional callback(name, i, total) called per file.

    Returns (path of the written HTML file, list of skipped-file messages).
    """
    csvs: list[Path] = []
    for tgt in targets:
        csvs.extend(find_csvs(Path(tgt)))
    # de-duplicate while keeping order
    seen = set()
    csvs = [c for c in csvs if not (c.resolve() in seen or seen.add(c.resolve()))]
    if not csvs:
        raise FileNotFoundError("No .csv files found in the chosen location(s).")

    # Fail on an unwritable destination BEFORE spending minutes processing.
    if out_path is None:
        base = Path(targets[0])
        out_path = (base if base.is_dir() else base.parent) / cfg.output_name
    out_path = Path(out_path)
    try:
        out_path.parent.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise RuntimeError(f"Cannot create output folder {out_path.parent}: {exc}") from exc

    runs, errors = {}, []
    for i, f in enumerate(csvs):
        if progress:
            progress(f.name, i + 1, len(csvs))
        try:
            runs[_unique_key(f.stem, f, runs)] = process_run(f, cfg)
        except Exception as exc:  # a bad file skips, never kills the build
            errors.append(f"{f.name}: {exc}")
    if not runs:
        raise RuntimeError("No file could be processed:\n" + "\n".join(errors))

    data = {"generated": str(date.today()), "runs": runs}
    out_path.write_text(render(data, cfg), encoding="utf-8")
    return out_path, errors
