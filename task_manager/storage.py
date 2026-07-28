"""
storage.py — JSON-file persistence layer.

All file I/O is isolated here.  If the storage mechanism ever changes
(e.g. SQLite, a REST API), only this file needs to change.
"""

from __future__ import annotations

import json
import os
from typing import Callable, Optional

from .models import Priority, Status, Task

DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tasks.json")


class TaskStore:
    """Loads and saves tasks to a JSON file."""

    def __init__(self, db_path: str = DEFAULT_DB_PATH) -> None:
        self.db_path = db_path
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
        return self._tasks.get(task_id)

    def all(self) -> list[Task]:
        return list(self._tasks.values())

    def update(self, task: Task) -> Task:
        if task.id not in self._tasks:
            raise KeyError(f"Task '{task.id}' not found.")
        task.touch()
        self._tasks[task.id] = task
        self._save()
        return task

    def delete(self, task_id: str) -> Task:
        if task_id not in self._tasks:
            raise KeyError(f"Task '{task_id}' not found.")
        task = self._tasks.pop(task_id)
        self._save()
        return task

    def filter(
        self,
        status: Optional[Status] = None,
        priority: Optional[Priority] = None,
        tag: Optional[str] = None,
        search: Optional[str] = None,
    ) -> list[Task]:
        """Return tasks that match ALL supplied criteria."""
        results = self.all()
        if status:
            results = [t for t in results if t.status == status]
        if priority:
            results = [t for t in results if t.priority == priority]
        if tag:
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
        if not os.path.exists(self.db_path):
            return
        try:
            with open(self.db_path, "r", encoding="utf-8") as fh:
                raw = json.load(fh)
            self._tasks = {item["id"]: Task.from_dict(item) for item in raw}
        except (json.JSONDecodeError, KeyError):
            # Corrupted file — start fresh rather than crash.
            self._tasks = {}

    def _save(self) -> None:
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        with open(self.db_path, "w", encoding="utf-8") as fh:
            json.dump(
                [t.to_dict() for t in self._tasks.values()],
                fh,
                indent=2,
                ensure_ascii=False,
            )
