"""
models.py — Task domain model.

This is the centre of the application.  Every other module imports from here,
but this module imports nothing from the rest of the project — the dependency
arrow only ever points inward.

Design decisions
----------------
* dataclass  — gives __init__, __repr__, and __eq__ for free, which makes
  the model trivial to construct in tests.
* str-Enum   — inheriting from str means Priority.HIGH == "high" is True,
  so we can store the raw string in JSON and round-trip without a lookup table.
* 8-char UUID — short enough to type at a prompt, statistically unique for
  personal use (collision probability is negligible below ~100 k tasks).
* ISO-8601 timestamps — human-readable and lexicographically sortable.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class Priority(str, Enum):
    LOW    = "low"
    MEDIUM = "medium"
    HIGH   = "high"

    def __str__(self) -> str:
        # Makes f"{task.priority}" produce "high" instead of "Priority.HIGH".
        return self.value


class Status(str, Enum):
    PENDING     = "pending"
    IN_PROGRESS = "in_progress"
    DONE        = "done"

    def __str__(self) -> str:
        return self.value


@dataclass
class Task:
    """Represents a single unit of work."""

    # Required field — everything else has a sensible default.
    title: str

    description: str          = ""
    priority:    Priority     = Priority.MEDIUM
    status:      Status       = Status.PENDING
    due_date:    Optional[str] = None          # ISO-8601, e.g. "2025-12-31"
    tags:        list[str]    = field(default_factory=list)

    # Auto-generated on creation; never supplied by the caller.
    id:         str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    created_at: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))

    # ------------------------------------------------------------------
    # Serialisation helpers
    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        """Convert to a plain dict so json.dump can serialise it."""
        return {
            "id":          self.id,
            "title":       self.title,
            "description": self.description,
            "priority":    self.priority.value,
            "status":      self.status.value,
            "due_date":    self.due_date,
            "tags":        self.tags,
            "created_at":  self.created_at,
            "updated_at":  self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        """Reconstruct a Task from a dict loaded out of JSON.

        .get() with defaults means the model stays backwards-compatible if
        new fields are added later — old JSON files won't crash on load.
        """
        return cls(
            id=          data["id"],
            title=       data["title"],
            description= data.get("description", ""),
            priority=    Priority(data.get("priority", Priority.MEDIUM.value)),
            status=      Status(data.get("status",   Status.PENDING.value)),
            due_date=    data.get("due_date"),
            tags=        data.get("tags", []),
            created_at=  data.get("created_at", datetime.now().isoformat(timespec="seconds")),
            updated_at=  data.get("updated_at", datetime.now().isoformat(timespec="seconds")),
        )

    def touch(self) -> None:
        """Stamp updated_at whenever the task is mutated."""
        self.updated_at = datetime.now().isoformat(timespec="seconds")
