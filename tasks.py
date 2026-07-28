"""
tasks.py — CLI launcher.  Run from the project root:  python tasks.py <command>
"""

import sys
import os

# Ensure UTF-8 output on Windows terminals (Python 3.7+).
if sys.stdout.encoding and sys.stdout.encoding.upper() != "UTF-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Ensure the project root is on the path regardless of working directory.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from task_manager.cli import main
from task_manager.tui import run as tui_run

if __name__ == "__main__":
    # No sub-command → launch the interactive TUI menu.
    if len(sys.argv) == 1:
        sys.exit(tui_run())
    sys.exit(main())
