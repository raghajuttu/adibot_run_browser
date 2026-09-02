"""Double-click launcher for the Run Browser app (no console window).

Lives in launchers/windows/, so the project folder is two levels up — that is
what has to be on sys.path for `run_browser` to be importable.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from run_browser.app import main

main()
