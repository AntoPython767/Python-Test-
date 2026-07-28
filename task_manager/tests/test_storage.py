"""
tests/test_storage.py — unit tests for the TaskStore.
"""

import os
import tempfile

import pytest

from task_manager.models import Priority, Status, Task
from task_manager.storage import TaskStore


@pytest.fixture
def store(tmp_path):
    """A fresh TaskStore backed by a temp file for each test."""
    return TaskStore(db_path=str(tmp_path / "tasks.json"))


def _task(title="Sample task", **kwargs) -> Task:
    return Task(title=title, **kwargs)


def test_add_and_get(store):
    t = store.add(_task("Do laundry"))
    assert store.get(t.id) is not None
    assert store.get(t.id).title == "Do laundry"


def test_all_returns_all(store):
    store.add(_task("A"))
    store.add(_task("B"))
    store.add(_task("C"))
    assert len(store.all()) == 3


def test_update(store):
    t = store.add(_task("Original"))
    t.title = "Updated"
    store.update(t)
    assert store.get(t.id).title == "Updated"


def test_delete(store):
    t = store.add(_task("Temp"))
    store.delete(t.id)
    assert store.get(t.id) is None


def test_delete_nonexistent_raises(store):
    with pytest.raises(KeyError):
        store.delete("nope")


def test_filter_by_status(store):
    store.add(_task("A", status=Status.PENDING))
    store.add(_task("B", status=Status.DONE))
    pending = store.filter(status=Status.PENDING)
    assert len(pending) == 1
    assert pending[0].title == "A"


def test_filter_by_priority(store):
    store.add(_task("X", priority=Priority.HIGH))
    store.add(_task("Y", priority=Priority.LOW))
    high = store.filter(priority=Priority.HIGH)
    assert len(high) == 1


def test_filter_by_tag(store):
    store.add(_task("Tagged", tags=["work"]))
    store.add(_task("Untagged"))
    assert len(store.filter(tag="work")) == 1
    assert len(store.filter(tag="home")) == 0


def test_filter_by_search(store):
    store.add(_task("Buy groceries"))
    store.add(_task("Pay bills"))
    assert len(store.filter(search="groceries")) == 1
    assert len(store.filter(search="GROCERIES")) == 1  # case-insensitive


def test_persistence(tmp_path):
    """Data written by one store instance is readable by a new instance."""
    path = str(tmp_path / "tasks.json")
    s1 = TaskStore(db_path=path)
    t = s1.add(_task("Persist me"))

    s2 = TaskStore(db_path=path)
    assert s2.get(t.id) is not None
    assert s2.get(t.id).title == "Persist me"
