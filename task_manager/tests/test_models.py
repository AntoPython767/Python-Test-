"""
tests/test_models.py — unit tests for the Task domain model.
"""

from task_manager.models import Priority, Status, Task


def test_task_defaults():
    t = Task(title="Buy milk")
    assert t.title == "Buy milk"
    assert t.status == Status.PENDING
    assert t.priority == Priority.MEDIUM
    assert len(t.id) == 8


def test_task_roundtrip():
    t = Task(title="Test task", description="desc", priority=Priority.HIGH, tags=["work"])
    d = t.to_dict()
    t2 = Task.from_dict(d)
    assert t2.id == t.id
    assert t2.title == t.title
    assert t2.priority == t.priority
    assert t2.tags == t.tags


def test_task_touch_updates_timestamp():
    import time
    t = Task(title="Touch test")
    before = t.updated_at
    time.sleep(0.01)
    t.touch()
    assert t.updated_at >= before
