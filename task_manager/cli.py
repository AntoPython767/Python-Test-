"""
cli.py — Command-line interface built on argparse.

Each subcommand maps to a single handler function.  Handlers receive
parsed args and a TaskStore; they print output and return an exit code.

Design note: no global state — the store is injected so the handlers
are trivially testable with a temporary store.
"""

from __future__ import annotations

import argparse
import sys
from typing import Optional

from .display import error, header, info, success, task_detail, task_row
from .models import Priority, Status, Task
from .storage import TaskStore


# ---------------------------------------------------------------------------
# Command handlers
# ---------------------------------------------------------------------------

def cmd_add(args: argparse.Namespace, store: TaskStore) -> int:
    tags = [t.strip() for t in args.tags.split(",")] if args.tags else []
    task = Task(
        title=args.title,
        description=args.description or "",
        priority=Priority(args.priority),
        due_date=args.due,
        tags=tags,
    )
    store.add(task)
    print(success(f"Task added  ->  {task.id}  \"{task.title}\""))
    return 0


def cmd_list(args: argparse.Namespace, store: TaskStore) -> int:
    status = Status(args.status) if args.status else None
    priority = Priority(args.priority) if args.priority else None
    tasks = store.filter(
        status=status,
        priority=priority,
        tag=args.tag or None,
        search=args.search or None,
    )

    if not tasks:
        print(info("No tasks match your criteria."))
        return 0

    # Sort: high priority first, then by created_at
    priority_order = {Priority.HIGH: 0, Priority.MEDIUM: 1, Priority.LOW: 2}
    tasks.sort(key=lambda t: (priority_order[t.priority], t.created_at))

    label_parts = []
    if status:
        label_parts.append(f"status={status}")
    if priority:
        label_parts.append(f"priority={priority}")
    if args.tag:
        label_parts.append(f"tag={args.tag}")
    if args.search:
        label_parts.append(f'search="{args.search}"')
    label = "  ".join(label_parts) or "all"
    print(header(f"Tasks  ({label})  —  {len(tasks)} found"))

    for task in tasks:
        print(task_row(task))
    print()
    return 0


def cmd_show(args: argparse.Namespace, store: TaskStore) -> int:
    task = _resolve(args.id, store)
    if task is None:
        return 1
    print(task_detail(task))
    return 0


def cmd_complete(args: argparse.Namespace, store: TaskStore) -> int:
    task = _resolve(args.id, store)
    if task is None:
        return 1
    task.status = Status.DONE
    store.update(task)
    print(success(f"Marked done  ->  \"{task.title}\""))
    return 0


def cmd_start(args: argparse.Namespace, store: TaskStore) -> int:
    task = _resolve(args.id, store)
    if task is None:
        return 1
    task.status = Status.IN_PROGRESS
    store.update(task)
    print(success(f"Marked in-progress  ->  \"{task.title}\""))
    return 0


def cmd_update(args: argparse.Namespace, store: TaskStore) -> int:
    task = _resolve(args.id, store)
    if task is None:
        return 1

    changed = False
    if args.title:
        task.title = args.title
        changed = True
    if args.description is not None:
        task.description = args.description
        changed = True
    if args.priority:
        task.priority = Priority(args.priority)
        changed = True
    if args.status:
        task.status = Status(args.status)
        changed = True
    if args.due is not None:
        task.due_date = args.due or None
        changed = True
    if args.tags is not None:
        task.tags = [t.strip() for t in args.tags.split(",")] if args.tags else []
        changed = True

    if not changed:
        print(info("Nothing to update — supply at least one field to change."))
        return 0

    store.update(task)
    print(success(f"Updated  ->  \"{task.title}\""))
    return 0


def cmd_delete(args: argparse.Namespace, store: TaskStore) -> int:
    task = _resolve(args.id, store)
    if task is None:
        return 1
    if not args.yes:
        confirm = input(f"   Delete \"{task.title}\" [{task.id}]? [y/N] ").strip().lower()
        if confirm not in ("y", "yes"):
            print(info("Cancelled."))
            return 0
    store.delete(task.id)
    print(success(f"Deleted  ->  \"{task.title}\""))
    return 0


def cmd_stats(args: argparse.Namespace, store: TaskStore) -> int:
    tasks = store.all()
    if not tasks:
        print(info("No tasks yet."))
        return 0

    total = len(tasks)
    by_status = {s: sum(1 for t in tasks if t.status == s) for s in Status}
    by_priority = {p: sum(1 for t in tasks if t.priority == p) for p in Priority}

    print(header("Task Statistics"))
    print(f"  Total       {total}")
    print()
    for s in Status:
        print(f"  {s.value.replace('_', ' ').ljust(12)}  {by_status[s]}")
    print()
    for p in Priority:
        print(f"  {p.value.ljust(12)}  {by_priority[p]}")
    print()
    return 0


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _resolve(task_id: str, store: TaskStore):
    """Look up a task by ID; print an error and return None if not found."""
    task = store.get(task_id)
    if task is None:
        print(error(f"No task with ID '{task_id}' found."))
        return None
    return task


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------

_PRIORITIES = [p.value for p in Priority]
_STATUSES = [s.value for s in Status]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tasks",
        description="A simple command-line task manager.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  tasks add "Write technical exercise" --priority high --due 2025-07-16
  tasks list
  tasks list --status pending --priority high
  tasks list --search "exercise"
  tasks show <id>
  tasks complete <id>
  tasks start <id>
  tasks update <id> --title "New title" --priority low
  tasks delete <id>
  tasks stats
""",
    )

    sub = parser.add_subparsers(dest="command", metavar="<command>")
    sub.required = True

    # --- add ---
    p_add = sub.add_parser("add", help="Add a new task.")
    p_add.add_argument("title", help="Task title.")
    p_add.add_argument("-d", "--description", help="Optional longer description.")
    p_add.add_argument(
        "-p", "--priority", choices=_PRIORITIES, default="medium",
        help="Priority level (default: medium).",
    )
    p_add.add_argument("--due", metavar="DATE", help="Due date in YYYY-MM-DD format.")
    p_add.add_argument("--tags", metavar="TAG1,TAG2", help="Comma-separated tags.")

    # --- list ---
    p_list = sub.add_parser("list", aliases=["ls"], help="List tasks.")
    p_list.add_argument("-s", "--status", choices=_STATUSES, help="Filter by status.")
    p_list.add_argument("-p", "--priority", choices=_PRIORITIES, help="Filter by priority.")
    p_list.add_argument("--tag", help="Filter by tag.")
    p_list.add_argument("--search", help="Search title and description.")

    # --- show ---
    p_show = sub.add_parser("show", help="Show full detail of one task.")
    p_show.add_argument("id", help="Task ID.")

    # --- complete ---
    p_done = sub.add_parser("complete", aliases=["done"], help="Mark a task as done.")
    p_done.add_argument("id", help="Task ID.")

    # --- start ---
    p_start = sub.add_parser("start", help="Mark a task as in-progress.")
    p_start.add_argument("id", help="Task ID.")

    # --- update ---
    p_upd = sub.add_parser("update", aliases=["edit"], help="Update task fields.")
    p_upd.add_argument("id", help="Task ID.")
    p_upd.add_argument("--title", help="New title.")
    p_upd.add_argument("--description", help="New description.")
    p_upd.add_argument("-p", "--priority", choices=_PRIORITIES, help="New priority.")
    p_upd.add_argument("-s", "--status", choices=_STATUSES, help="New status.")
    p_upd.add_argument("--due", metavar="DATE", help="New due date (empty string clears it).")
    p_upd.add_argument("--tags", metavar="TAG1,TAG2", help="New tags (empty string clears them).")

    # --- delete ---
    p_del = sub.add_parser("delete", aliases=["rm"], help="Delete a task.")
    p_del.add_argument("id", help="Task ID.")
    p_del.add_argument("-y", "--yes", action="store_true", help="Skip confirmation prompt.")

    # --- stats ---
    sub.add_parser("stats", help="Show summary statistics.")

    return parser


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

COMMAND_MAP = {
    "add":      cmd_add,
    "list":     cmd_list,
    "ls":       cmd_list,
    "show":     cmd_show,
    "complete": cmd_complete,
    "done":     cmd_complete,
    "start":    cmd_start,
    "update":   cmd_update,
    "edit":     cmd_update,
    "delete":   cmd_delete,
    "rm":       cmd_delete,
    "stats":    cmd_stats,
}


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    store = TaskStore()
    handler = COMMAND_MAP[args.command]
    try:
        return handler(args, store)
    except KeyError as exc:
        print(error(str(exc)))
        return 1
    except ValueError as exc:
        print(error(f"Invalid value: {exc}"))
        return 1


if __name__ == "__main__":
    sys.exit(main())
