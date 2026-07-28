# tasks — Python CLI Task Manager

A small, well-structured task manager that runs entirely in the terminal.
It ships with both an **interactive TUI menu** and a full **argparse CLI** — no third-party packages required.

---

## How to run

### Interactive TUI (recommended)

```bash
python tasks.py
```

No arguments needed. The numbered menu appears immediately.

### One-shot CLI

```bash
python tasks.py <command> [options]
```

---

## TUI Menu

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

| Option | What it does |
|--------|-------------|
| **1 List Tasks** | Shows all tasks sorted by priority then creation date |
| **2 Add Task** | Guided prompts for title, description, priority, due date, tags |
| **3 Edit Task** | Change any field of an existing task; press Enter to keep the current value |
| **4 Mark Completed** | Shows only pending / in-progress tasks; marks the chosen one as done |
| **5 Filter by Status** | Lists only Pending, In Progress, or Completed tasks |
| **6 Delete Task** | Asks for confirmation before deleting |
| **7 Exit** | Quit (also accepts `q`, `quit`, `exit`) |

---

## CLI commands

| Command | Alias | Description |
|---------|-------|-------------|
| `add <title>` | — | Add a new task |
| `list` | `ls` | List tasks (with optional filters) |
| `show <id>` | — | Show full detail of one task |
| `complete <id>` | `done` | Mark a task as done |
| `start <id>` | — | Mark a task as in-progress |
| `update <id>` | `edit` | Update one or more fields |
| `delete <id>` | `rm` | Delete a task |
| `stats` | — | Show summary statistics |

### CLI examples

```bash
# Add tasks
python tasks.py add "Write technical exercise" --priority high --due 2025-07-16
python tasks.py add "Review pull requests" --priority medium --tags "work,code"

# List / filter
python tasks.py list
python tasks.py list --status pending
python tasks.py list --priority high
python tasks.py list --search "review"

# Workflow
python tasks.py start <id>
python tasks.py complete <id>

# Update
python tasks.py update <id> --title "Revised title" --priority low
python tasks.py update <id> --due 2025-12-31 --tags "personal,urgent"

# Inspect / stats
python tasks.py show <id>
python tasks.py stats

# Remove
python tasks.py delete <id>       # prompts for confirmation
python tasks.py delete <id> --yes # skip confirmation
```

---

## Requirements

- Python 3.10 or higher
- No third-party packages required to run
- `pytest` is only needed to run the test suite

```bash
python -m pip install pytest   # optional — tests only
```

---

## Where tasks are stored

```
<project root>/task_manager/tasks.json
```

The file is created automatically on first run.
It is plain JSON — easy to inspect, back up, or migrate.

---

## Project structure

```
Python Challenge/
├── tasks.py                  # launcher — TUI when no args, CLI otherwise
└── task_manager/
    ├── __init__.py
    ├── models.py             # Task dataclass, Priority & Status enums
    ├── storage.py            # TaskStore — JSON persistence layer
    ├── display.py            # ANSI colour helpers
    ├── cli.py                # argparse subcommands
    ├── tui.py                # interactive numbered-menu loop
    ├── tasks.json            # auto-created data file
    └── tests/
        ├── test_models.py
        ├── test_storage.py
        └── test_cli.py
```

---

## Running tests

```bash
pytest task_manager/tests/ -v
```

---

## Design decisions

| Concern | Choice | Reason |
|---------|--------|--------|
| **Persistence** | JSON file in `task_manager/tasks.json` | Zero external dependencies; human-readable; trivially portable |
| **Architecture** | 3-layer separation: `models` → `storage` → `cli` / `tui` | Single responsibility per layer; easy to swap storage backend |
| **IDs** | 8-character UUID prefix | Short enough to type, collision-resistant for personal use |
| **Output** | ANSI colour with graceful fallback | Readable at a glance; degrades cleanly when piped or on plain terminals |
| **Input validation** | Re-prompt loop on bad input | Never crashes on user error; guides the user to the correct format |
| **TUI vs CLI** | Both exposed from one launcher | TUI for interactive use; CLI for scripting and automation |
| **Dependencies** | Standard library only | No `pip install` required; runs anywhere Python 3.10+ is available |

---

## Bonus features implemented

- **Edit Task** — option 3 in the TUI; `tasks update <id>` in the CLI
- **Filter by Status** — option 5 in the TUI; `tasks list --status <status>` in the CLI
- **Graceful invalid-input handling** — every prompt re-asks on bad input with a clear error message (empty required fields, wrong date format, out-of-range menu choice, unknown task ID, already-completed task)
- **README** — this file

---

## If I had more time…

- **Due-date reminders** — highlight overdue tasks in red on list
- **Recurring tasks** — `recur` field (`daily`, `weekly`, etc.)
- **SQLite backend** — drop-in replacement for the JSON store for larger datasets
- **Export** — `tasks export --format csv` for spreadsheet integration
- **Watson Orchestrate integration** — expose commands as skills via the WO SDK

---

*Built with the Python standard library. No magic.*
