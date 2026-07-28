"""
tasks.py — Entry point.

Two ways to run:
  python tasks.py            →  interactive TUI menu (no arguments needed)
  python tasks.py <command>  →  one-shot CLI (e.g. python tasks.py list)
"""

import sys
import os

# Windows terminals may default to cp1252; force UTF-8 so box-drawing
# characters and accented letters render correctly.
if sys.stdout.encoding and sys.stdout.encoding.upper() != "UTF-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Make the package importable regardless of where the user runs the script
# (e.g. from a different working directory).
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from task_manager.cli import main
from task_manager.tui import run as tui_run

if __name__ == "__main__":
    # No sub-command supplied → drop into the interactive numbered menu.
    # Any argument triggers the standard argparse CLI instead.
    if len(sys.argv) == 1:
        sys.exit(tui_run())
    sys.exit(main())
