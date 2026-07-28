# Task Manager — Python CLI + TUI

A terminal-based task manager built with the Python standard library.
No pip installs required to run.

---

## How to run

```bash
# Interactive TUI — numbered menu (recommended)
python tasks.py

# One-shot CLI
python tasks.py <command> [options]
```

---

## TUI menu

```
  Task Manager

  1 - List Tasks
  2 - Add Task
  3 - Edit Task
  4 - Mark Task as Completed
  5 - Filter Tasks by Status
  6 - Delete Task
  7 - Exit
```

Every prompt validates your input and re-asks on bad data — nothing crashes.

---

## CLI commands

| Command | Alias | What it does |
|---------|-------|--------------|
| `add <title>` | — | Add a new task |
| `list` | `ls` | List tasks (filterable) |
| `show <id>` | — | Full detail of one task |
| `complete <id>` | `done` | Mark as done |
| `start <id>` | — | Mark as in-progress |
| `update <id>` | `edit` | Edit one or more fields |
| `delete <id>` | `rm` | Delete (with confirmation) |
| `stats` | — | Summary counts |

### CLI examples

```bash
python tasks.py add "Write report" --priority high --due 2025-08-01
python tasks.py list
python tasks.py list --status pending
python tasks.py list --priority high
python tasks.py list --search "report"
python tasks.py start <id>
python tasks.py complete <id>
python tasks.py update <id> --title "Final report" --priority low
python tasks.py show <id>
python tasks.py delete <id>
python tasks.py stats
```

---

## Where tasks are stored

```
task_manager/tasks.json
```

Created automatically on first run.
Plain JSON — human-readable, easy to back up or inspect.

---

## Requirements

- Python 3.10+
- No third-party packages needed to run
- `pytest` only needed for tests: `pip install pytest`

---

## Running tests

```bash
pytest task_manager/tests/ -v
```

---

## Project structure

```
Python Challenge/
├── tasks.py                  # entry point — TUI (no args) or CLI
└── task_manager/
    ├── models.py             # Task dataclass, Priority & Status enums
    ├── storage.py            # TaskStore — JSON read/write, CRUD methods
    ├── display.py            # ANSI colour helpers, task_row, task_detail
    ├── cli.py                # argparse subcommands + dispatch table
    ├── tui.py                # interactive numbered-menu loop
    ├── tasks.json            # auto-created data file
    └── tests/
        ├── test_models.py
        ├── test_storage.py
        └── test_cli.py
```

---

## Design decisions

### Separation of concerns

The project is split into four layers, each with one job:

| Layer | File | Responsibility |
|-------|------|----------------|
| Model | `models.py` | What a Task *is* — fields, defaults, serialisation |
| Storage | `storage.py` | Where tasks *live* — all disk I/O in one place |
| Presentation | `display.py` | How tasks *look* — all colour and layout decisions |
| Interface | `cli.py` / `tui.py` | How the user *interacts* — argparse vs. menu loop |

This means, for example, swapping JSON for SQLite only requires touching `storage.py`.

### Why a dataclass for Task?

`@dataclass` generates `__init__`, `__repr__`, and `__eq__` automatically.
This keeps the model declaration concise and makes equality checks in tests trivial (`task1 == task2`).

### Why str-Enum for Priority and Status?

Inheriting from `str` means `Priority.HIGH == "high"` is `True`.
Tasks can be stored in JSON as plain strings and reconstructed without a lookup table.

### Why 8-character IDs?

Short enough to type at a prompt; collision probability is negligible for
personal use (< 1 in a million for up to ~10 000 tasks).

### Error handling approach

- **Invalid input in the TUI** — re-prompt loop with a clear error message. No crash, no silent acceptance of garbage.
- **Unknown task ID** — prints a friendly `[!!]` message and returns, never raises an unhandled exception to the user.
- **Corrupted JSON file** — caught on load; the app starts fresh instead of crashing.
- **argparse choices=** — the CLI rejects invalid priority/status values before the handler ever runs.

### Why both a TUI and a CLI?

- TUI is friendlier for a first-time user exploring the tool interactively.
- CLI enables scripting (`tasks add "..." && tasks list`).
- Both share the same `TaskStore` and `display` layer — no logic is duplicated.

---

## Bonus features implemented

| Feature | Where |
|---------|-------|
| Edit an existing task | TUI option 3 · CLI `tasks update <id>` |
| Filter tasks by status | TUI option 5 · CLI `tasks list --status <status>` |
| Graceful invalid-input handling | Every TUI prompt re-asks; CLI uses argparse validation |
| README | This file |

---

## If I had more time…

- **Overdue highlighting** — colour due dates red when past today
- **SQLite backend** — drop-in swap in `storage.py` for larger datasets
- **CSV export** — `tasks export --format csv`
- **Watson Orchestrate integration** — expose commands as WO skills via the SDK

---

*Built with the Python standard library only. No magic.*
