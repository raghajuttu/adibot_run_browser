"""Double-click launcher for the Run Browser app (no console window).

Keep this file next to the run_browser/ folder.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from run_browser.app import main

main()
