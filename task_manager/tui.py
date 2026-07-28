"""
tui.py — Interactive numbered-menu TUI.

Launch with:  python tasks.py
(no sub-command arguments required)

Menu
----
  1 - List Tasks
  2 - Add Task
  3 - Edit Task          ← bonus
  4 - Mark Task as Completed
  5 - Filter by Status   ← bonus
  6 - Delete Task
  7 - Exit
"""

from __future__ import annotations

import os
import re

from .display import error, header, info, success, task_detail, task_row
from .models import Priority, Status, Task
from .storage import TaskStore

# ISO-8601 date pattern used for due-date validation
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

_PRIORITY_ORDER = {Priority.HIGH: 0, Priority.MEDIUM: 1, Priority.LOW: 2}


# ---------------------------------------------------------------------------
# Low-level I/O helpers
# ---------------------------------------------------------------------------

def _clear() -> None:
    os.system("cls" if os.name == "nt" else "clear")


def _prompt(text: str, default: str = "") -> str:
    """Prompt the user and return stripped input; returns *default* on empty enter."""
    try:
        val = input(f"  {text} ").strip()
    except (EOFError, KeyboardInterrupt):
        return default
    return val if val else default


def _pause() -> None:
    _prompt("Press Enter to continue...")


def _banner() -> None:
    print(header("Task Manager"))
    print("  1 - List Tasks")
    print("  2 - Add Task")
    print("  3 - Edit Task")
    print("  4 - Mark Task as Completed")
    print("  5 - Filter Tasks by Status")
    print("  6 - Delete Task")
    print("  7 - Exit")
    print()


# ---------------------------------------------------------------------------
# Validated input helpers
# ---------------------------------------------------------------------------

def _ask_priority(current: Priority | None = None) -> Priority:
    """Ask for priority; re-prompt until valid. Shows current value if editing."""
    hint = f"  (current: {current})" if current else ""
    while True:
        print(f"  Priority: 1=low  2=medium  3=high  (default: medium){hint}")
        raw = _prompt("Choice [1/2/3]:", "2")
        mapping = {"1": Priority.LOW, "2": Priority.MEDIUM, "3": Priority.HIGH}
        if raw in mapping:
            return mapping[raw]
        if raw == "" and current is not None:
            return current
        print(error("Enter 1, 2, or 3."))


def _ask_date(label: str = "Due date YYYY-MM-DD (optional, Enter to skip):") -> str | None:
    """Ask for a date string; re-prompt until format is correct or blank."""
    while True:
        raw = _prompt(label)
        if not raw:
            return None
        if _DATE_RE.match(raw):
            return raw
        print(error("Date must be in YYYY-MM-DD format (e.g. 2025-12-31). Try again."))


def _ask_status(current: Status | None = None) -> Status:
    """Ask for a status; re-prompt until valid."""
    options = {str(i + 1): s for i, s in enumerate(Status)}
    hint = f"  (current: {current})" if current else ""
    while True:
        print(f"  Status: 1=pending  2=in_progress  3=done{hint}")
        raw = _prompt("Choice [1/2/3]:", "")
        if raw == "" and current is not None:
            return current
        if raw in options:
            return options[raw]
        print(error("Enter 1, 2, or 3."))


def _resolve_task(store: TaskStore, prompt_text: str) -> Task | None:
    """Ask for a task ID; return the Task or print an error and return None."""
    task_id = _prompt(prompt_text)
    if not task_id:
        print(info("Cancelled."))
        return None
    task = store.get(task_id)
    if task is None:
        print(error(f"No task with ID '{task_id}' found."))
    return task


# ---------------------------------------------------------------------------
# Menu actions
# ---------------------------------------------------------------------------

def _action_list(store: TaskStore) -> None:
    _clear()
    tasks = store.all()
    if not tasks:
        print(info("No tasks yet."))
        _pause()
        return

    tasks.sort(key=lambda t: (_PRIORITY_ORDER[t.priority], t.created_at))
    print(header(f"All Tasks  —  {len(tasks)} found"))
    for task in tasks:
        print(task_row(task))
    print()
    _pause()


def _action_add(store: TaskStore) -> None:
    _clear()
    print(header("Add Task"))

    # --- title (required) ---
    while True:
        title = _prompt("Title (required):")
        if title:
            break
        print(error("Title cannot be empty. Please enter a title."))

    desc     = _prompt("Description (optional):")
    priority = _ask_priority()
    due      = _ask_date()
    tags_raw = _prompt("Tags comma-separated (optional):")
    tags     = [t.strip() for t in tags_raw.split(",") if t.strip()] if tags_raw else []

    task = Task(
        title=title,
        description=desc,
        priority=priority,
        due_date=due,
        tags=tags,
    )
    store.add(task)
    print()
    print(success(f"Task added  ->  {task.id}  \"{task.title}\""))
    _pause()


def _action_edit(store: TaskStore) -> None:
    """Edit any fields of an existing task."""
    _clear()
    tasks = store.all()
    if not tasks:
        print(info("No tasks to edit."))
        _pause()
        return

    tasks.sort(key=lambda t: (_PRIORITY_ORDER[t.priority], t.created_at))
    print(header("Edit Task"))
    for task in tasks:
        print(task_row(task))
    print()

    task = _resolve_task(store, "Enter Task ID to edit:")
    if task is None:
        _pause()
        return

    print()
    print(info(f"Editing \"{task.title}\"  [{task.id}]"))
    print(info("Press Enter to keep the current value."))
    print()

    # title
    new_title = _prompt(f"Title [{task.title}]:")
    if new_title:
        task.title = new_title

    # description
    new_desc = _prompt(f"Description [{task.description or '(none)'}]:")
    if new_desc:
        task.description = new_desc

    # priority
    task.priority = _ask_priority(current=task.priority)

    # status
    task.status = _ask_status(current=task.status)

    # due date
    print(info(f"Current due date: {task.due_date or '(none)'}"))
    new_due = _ask_date("New due date YYYY-MM-DD (Enter to keep current):")
    if new_due is not None:
        task.due_date = new_due

    # tags
    current_tags = ", ".join(task.tags) if task.tags else "(none)"
    new_tags_raw = _prompt(f"Tags [{current_tags}] (comma-separated, Enter to keep):")
    if new_tags_raw:
        task.tags = [t.strip() for t in new_tags_raw.split(",") if t.strip()]

    store.update(task)
    print()
    print(success(f"Updated  ->  \"{task.title}\""))
    _pause()


def _action_complete(store: TaskStore) -> None:
    _clear()
    tasks = store.filter(status=Status.PENDING) + store.filter(status=Status.IN_PROGRESS)
    if not tasks:
        print(info("No pending or in-progress tasks."))
        _pause()
        return

    tasks.sort(key=lambda t: (_PRIORITY_ORDER[t.priority], t.created_at))
    print(header("Mark Task as Completed"))
    for task in tasks:
        print(task_row(task))
    print()

    task = _resolve_task(store, "Enter Task ID to mark as done:")
    if task is None:
        _pause()
        return

    if task.status == Status.DONE:
        print(info(f"\"{task.title}\" is already marked as done."))
        _pause()
        return

    task.status = Status.DONE
    store.update(task)
    print(success(f"Marked done  ->  \"{task.title}\""))
    _pause()


def _action_filter(store: TaskStore) -> None:
    """List tasks filtered by a chosen status."""
    _clear()
    print(header("Filter Tasks by Status"))
    print("  1 - Pending")
    print("  2 - In Progress")
    print("  3 - Completed")
    print()

    while True:
        raw = _prompt("Choose status to filter [1/2/3]:")
        status_map = {
            "1": Status.PENDING,
            "2": Status.IN_PROGRESS,
            "3": Status.DONE,
        }
        if raw in status_map:
            chosen = status_map[raw]
            break
        if raw == "":
            print(info("Cancelled."))
            return
        print(error("Enter 1, 2, or 3."))

    tasks = store.filter(status=chosen)
    if not tasks:
        print(info(f"No tasks with status '{chosen.value}'."))
        _pause()
        return

    tasks.sort(key=lambda t: (_PRIORITY_ORDER[t.priority], t.created_at))
    label = chosen.value.replace("_", " ").title()
    print(header(f"{label} Tasks  —  {len(tasks)} found"))
    for task in tasks:
        print(task_row(task))
    print()
    _pause()


def _action_delete(store: TaskStore) -> None:
    _clear()
    tasks = store.all()
    if not tasks:
        print(info("No tasks to delete."))
        _pause()
        return

    tasks.sort(key=lambda t: (_PRIORITY_ORDER[t.priority], t.created_at))
    print(header("Delete Task"))
    for task in tasks:
        print(task_row(task))
    print()

    task = _resolve_task(store, "Enter Task ID to delete:")
    if task is None:
        _pause()
        return

    while True:
        confirm = _prompt(f"Delete \"{task.title}\" [{task.id}]? [y/N]:")
        if confirm.lower() in ("y", "yes"):
            break
        if confirm.lower() in ("n", "no", ""):
            print(info("Cancelled."))
            _pause()
            return
        print(error("Enter y to confirm or n to cancel."))

    store.delete(task.id)
    print(success(f"Deleted  ->  \"{task.title}\""))
    _pause()


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

_ACTIONS = {
    "1": _action_list,
    "2": _action_add,
    "3": _action_edit,
    "4": _action_complete,
    "5": _action_filter,
    "6": _action_delete,
}


def run() -> int:
    """Start the interactive TUI loop. Returns an exit code."""
    store = TaskStore()
    while True:
        _clear()
        _banner()
        choice = _prompt("Choose an option [1-7]:")

        if choice == "7" or choice.lower() in ("q", "quit", "exit"):
            _clear()
            print(info("Goodbye!\n"))
            return 0

        action = _ACTIONS.get(choice)
        if action is None:
            print(error(f"'{choice}' is not a valid option. Enter a number from 1 to 7."))
            _pause()
            continue

        action(store)
