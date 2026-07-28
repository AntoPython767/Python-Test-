"""
storage.py — JSON-file persistence layer.

All file I/O lives here.  The rest of the application never touches the disk
directly — it calls TaskStore methods.  This isolation means:
  * Swapping to SQLite (or a REST API) only requires changing this file.
  * Tests can pass a temp-file path and never pollute real data.

Storage format: a JSON array of task dicts, written with indent=2 so the
file is human-readable and easy to diff in version control.
"""

from __future__ import annotations

import json
import os
from typing import Optional

from .models import Priority, Status, Task

# Default location: alongside this source file, inside the project folder.
# Using abspath(__file__) makes it work regardless of the working directory.
DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tasks.json")


class TaskStore:
    """Loads and saves tasks to a JSON file.

    All mutating methods (_add_, _update_, _delete_) call _save() immediately
    so the file is always up to date — there is no separate "commit" step.
    """

    def __init__(self, db_path: str = DEFAULT_DB_PATH) -> None:
        self.db_path = db_path
        # In-memory store: task ID → Task object for O(1) lookups.
        self._tasks: dict[str, Task] = {}
        self._load()

    # ------------------------------------------------------------------
    # Public CRUD interface
    # ------------------------------------------------------------------

    def add(self, task: Task) -> Task:
        self._tasks[task.id] = task
        self._save()
        return task

    def get(self, task_id: str) -> Optional[Task]:
        """Return a Task by ID, or None if not found."""
        return self._tasks.get(task_id)

    def all(self) -> list[Task]:
        """Return every task as a list (insertion order preserved in Python 3.7+)."""
        return list(self._tasks.values())

    def update(self, task: Task) -> Task:
        """Persist changes to an existing task.  Raises KeyError if ID is unknown."""
        if task.id not in self._tasks:
            raise KeyError(f"Task '{task.id}' not found.")
        task.touch()            # update the updated_at timestamp
        self._tasks[task.id] = task
        self._save()
        return task

    def delete(self, task_id: str) -> Task:
        """Remove a task and return it.  Raises KeyError if ID is unknown."""
        if task_id not in self._tasks:
            raise KeyError(f"Task '{task_id}' not found.")
        task = self._tasks.pop(task_id)
        self._save()
        return task

    def filter(
        self,
        status:   Optional[Status]   = None,
        priority: Optional[Priority] = None,
        tag:      Optional[str]      = None,
        search:   Optional[str]      = None,
    ) -> list[Task]:
        """Return tasks matching ALL supplied criteria (AND logic).

        Passing no arguments is equivalent to calling all().
        """
        results = self.all()

        if status:
            results = [t for t in results if t.status == status]
        if priority:
            results = [t for t in results if t.priority == priority]
        if tag:
            # Case-insensitive tag match.
            results = [t for t in results if tag.lower() in [tg.lower() for tg in t.tags]]
        if search:
            needle = search.lower()
            results = [
                t for t in results
                if needle in t.title.lower() or needle in t.description.lower()
            ]
        return results

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load(self) -> None:
        """Read tasks from disk into memory on startup."""
        if not os.path.exists(self.db_path):
            return  # first run — start with an empty store

        try:
            with open(self.db_path, "r", encoding="utf-8") as fh:
                raw = json.load(fh)
            self._tasks = {item["id"]: Task.from_dict(item) for item in raw}
        except (json.JSONDecodeError, KeyError):
            # Corrupted or unreadable file — start fresh rather than crash.
            # A real production system might log a warning here.
            self._tasks = {}

    def _save(self) -> None:
        """Write the current in-memory state to disk."""
        # makedirs is safe to call even if the directory already exists.
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        with open(self.db_path, "w", encoding="utf-8") as fh:
            json.dump(
                [t.to_dict() for t in self._tasks.values()],
                fh,
                indent=2,
                ensure_ascii=False,   # keep non-ASCII characters readable
            )
