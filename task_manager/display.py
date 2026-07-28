"""
display.py — Terminal rendering helpers.

Keeps all colour/formatting logic in one place so the CLI stays readable.
Falls back gracefully if the terminal does not support ANSI codes.
"""

from __future__ import annotations

import os
import shutil
from typing import Optional

from .models import Priority, Status, Task

# Detect colour support: disable on Windows without ANSI, or when piped.
_COLOUR = os.name != "nt" or os.environ.get("TERM") == "xterm"
if os.environ.get("NO_COLOR"):
    _COLOUR = False


def _c(text: str, code: str) -> str:
    if not _COLOUR:
        return text
    return f"\033[{code}m{text}\033[0m"


def _bold(t: str) -> str:
    return _c(t, "1")


def _green(t: str) -> str:
    return _c(t, "32")


def _yellow(t: str) -> str:
    return _c(t, "33")


def _red(t: str) -> str:
    return _c(t, "31")


def _cyan(t: str) -> str:
    return _c(t, "36")


def _grey(t: str) -> str:
    return _c(t, "90")


_PRIORITY_COLOUR = {
    Priority.LOW: _grey,
    Priority.MEDIUM: _yellow,
    Priority.HIGH: _red,
}

_STATUS_COLOUR = {
    Status.PENDING: _yellow,
    Status.IN_PROGRESS: _cyan,
    Status.DONE: _green,
}


def _priority_str(p: Priority) -> str:
    return _PRIORITY_COLOUR[p](f"[{p}]")


def _status_str(s: Status) -> str:
    label = s.value.replace("_", " ")
    return _STATUS_COLOUR[s](label)


def task_row(task: Task, width: Optional[int] = None) -> str:
    """Single-line summary of a task, for list views."""
    width = width or shutil.get_terminal_size((100, 20)).columns
    tag_part = ("  " + _grey("#" + " #".join(task.tags))) if task.tags else ""
    due_part = (_grey(f"  due:{task.due_date}")) if task.due_date else ""
    line = (
        f"  {_bold(task.id)}  {_priority_str(task.priority)}  "
        f"{_status_str(task.status).ljust(12)}  {task.title}{due_part}{tag_part}"
    )
    return line


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
        f"  {_bold('Tags')}        {(', '.join(task.tags)) or _grey('(none)')}",
        f"  {_bold('Created')}     {_grey(task.created_at)}",
        f"  {_bold('Updated')}     {_grey(task.updated_at)}",
        sep,
    ]
    return "\n".join(lines)


def header(text: str) -> str:
    return _bold(_cyan(f"\n  {text}\n"))


def success(text: str) -> str:
    return _green(f"[OK]  {text}")


def error(text: str) -> str:
    return _red(f"[!!]  {text}")


def info(text: str) -> str:
    return _grey(f"   {text}")
