"""
display.py — Terminal rendering helpers.

Keeps every colour and layout decision in one place so cli.py and tui.py
stay focused on logic, not presentation.

Colour strategy
---------------
* ANSI escape codes are used on platforms that support them.
* On plain Windows (no TERM env-var) or when output is piped, colours are
  disabled automatically — the text remains readable, just unstyled.
* Setting the NO_COLOR environment variable (https://no-color.org/) also
  disables colours, which is a widely respected convention.
"""

from __future__ import annotations

import os
import shutil
from typing import Optional

from .models import Priority, Status, Task

# Enable colour only when the terminal is likely to support ANSI codes.
_COLOUR = os.name != "nt" or os.environ.get("TERM") == "xterm"
if os.environ.get("NO_COLOR"):
    _COLOUR = False


def _c(text: str, code: str) -> str:
    """Wrap text in an ANSI escape sequence, or return it unchanged."""
    if not _COLOUR:
        return text
    return f"\033[{code}m{text}\033[0m"


# Convenience wrappers — named functions are easier to read at the call site
# than raw escape codes scattered across the codebase.
def _bold(t: str)   -> str: return _c(t, "1")
def _green(t: str)  -> str: return _c(t, "32")
def _yellow(t: str) -> str: return _c(t, "33")
def _red(t: str)    -> str: return _c(t, "31")
def _cyan(t: str)   -> str: return _c(t, "36")
def _grey(t: str)   -> str: return _c(t, "90")


# Map each enum value to the colour that makes semantic sense at a glance:
#   priority  → red = urgent, yellow = normal, grey = low
#   status    → yellow = not started, cyan = in progress, green = done
_PRIORITY_COLOUR = {
    Priority.LOW:    _grey,
    Priority.MEDIUM: _yellow,
    Priority.HIGH:   _red,
}

_STATUS_COLOUR = {
    Status.PENDING:     _yellow,
    Status.IN_PROGRESS: _cyan,
    Status.DONE:        _green,
}


def _priority_str(p: Priority) -> str:
    return _PRIORITY_COLOUR[p](f"[{p}]")


def _status_str(s: Status) -> str:
    label = s.value.replace("_", " ")   # "in_progress" → "in progress"
    return _STATUS_COLOUR[s](label)


def task_row(task: Task, width: Optional[int] = None) -> str:
    """Single-line summary used in list views.

    Falls back to 100 columns if the terminal width cannot be detected
    (e.g. when output is piped).
    """
    width = width or shutil.get_terminal_size((100, 20)).columns  # noqa: F841
    tag_part = ("  " + _grey("#" + " #".join(task.tags))) if task.tags else ""
    due_part = _grey(f"  due:{task.due_date}") if task.due_date else ""
    return (
        f"  {_bold(task.id)}  {_priority_str(task.priority)}  "
        f"{_status_str(task.status).ljust(12)}  {task.title}{due_part}{tag_part}"
    )


def task_detail(task: Task) -> str:
    """Multi-line detailed view of a single task."""
    sep = _grey("-" * 50)
    lines = [
        sep,
        f"  {_bold('ID')}          {task.id}",
        f"  {_bold('Title')}       {task.title}",
        f"  {_bold('Description')} {task.description or _grey('(none)')}",
        f"  {_bold('Status')}      {_status_str(task.status)}",
        f"  {_bold('Priority')}    {_priority_str(task.priority)}",
        f"  {_bold('Due date')}    {task.due_date or _grey('(none)')}",
        f"  {_bold('Tags')}        {', '.join(task.tags) or _grey('(none)')}",
        f"  {_bold('Created')}     {_grey(task.created_at)}",
        f"  {_bold('Updated')}     {_grey(task.updated_at)}",
        sep,
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Message-level helpers  (used by cli.py and tui.py for feedback lines)
# ---------------------------------------------------------------------------

def header(text: str) -> str:
    """Bold cyan section heading with surrounding blank lines."""
    return _bold(_cyan(f"\n  {text}\n"))

def success(text: str) -> str:
    """Green confirmation message."""
    return _green(f"[OK]  {text}")

def error(text: str) -> str:
    """Red error message."""
    return _red(f"[!!]  {text}")

def info(text: str) -> str:
    """Muted grey informational message."""
    return _grey(f"   {text}")
