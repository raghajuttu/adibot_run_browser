"""Entry point.

    python -m run_browser                             -> opens the app window
    python -m run_browser <dir|csv...> [-o out.html]  -> headless build (no window)
"""

import sys
from pathlib import Path


def main():
    args = sys.argv[1:]
    if not args:
        from .app import main as app_main

        app_main()
        return

    out = None
    if "-o" in args:
        i = args.index("-o")
        if i + 1 >= len(args):
            print("error: -o needs a filename after it", file=sys.stderr)
            sys.exit(2)
        out = Path(args[i + 1])
        args = args[:i] + args[i + 2 :]
    if not args:
        print("error: give a folder or CSV file(s) to build from", file=sys.stderr)
        sys.exit(2)

    from .builder import build

    def progress(name, i, total):
        print(f"[{i}/{total}] {name}")

    try:
        path, skipped = build([Path(a) for a in args], out_path=out, progress=progress)
    except (FileNotFoundError, RuntimeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
    for msg in skipped:
        print(f"skipped: {msg}", file=sys.stderr)
    print(f"wrote {path}" + (f"  ({len(skipped)} file(s) skipped)" if skipped else ""))


if __name__ == "__main__":
    main()
