"""
tasks.py — thin launcher so users can run:  python tasks.py <command>
"""

import sys
from task_manager.cli import main

if __name__ == "__main__":
    sys.exit(main())
