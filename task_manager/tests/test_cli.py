"""
tests/test_cli.py — integration tests for CLI command handlers.
"""

import pytest

from task_manager.cli import main
from task_manager.models import Status
from task_manager.storage import TaskStore


@pytest.fixture
def store(tmp_path):
    return TaskStore(db_path=str(tmp_path / "tasks.json"))


def _run(argv, store):
    """Run main() with a pre-configured store."""
    from task_manager import cli as cli_module
    # Patch the TaskStore constructor for this call only.
    original = cli_module.TaskStore
    cli_module.TaskStore = lambda: store
    try:
        return main(argv)
    finally:
        cli_module.TaskStore = original


def test_add_and_list(store, capsys):
    rc = _run(["add", "Test task", "--priority", "high"], store)
    assert rc == 0
    rc = _run(["list"], store)
    assert rc == 0
    captured = capsys.readouterr()
    assert "Test task" in captured.out


def test_complete(store, capsys):
    _run(["add", "Finish report"], store)
    task_id = store.all()[0].id
    rc = _run(["complete", task_id], store)
    assert rc == 0
    assert store.get(task_id).status == Status.DONE


def test_delete_with_yes_flag(store):
    _run(["add", "Delete me"], store)
    task_id = store.all()[0].id
    rc = _run(["delete", task_id, "--yes"], store)
    assert rc == 0
    assert store.get(task_id) is None


def test_update_title(store):
    _run(["add", "Old title"], store)
    task_id = store.all()[0].id
    rc = _run(["update", task_id, "--title", "New title"], store)
    assert rc == 0
    assert store.get(task_id).title == "New title"


def test_invalid_id_returns_1(store, capsys):
    rc = _run(["show", "badid"], store)
    assert rc == 1


def test_stats_empty(store, capsys):
    rc = _run(["stats"], store)
    assert rc == 0
    captured = capsys.readouterr()
    assert "No tasks" in captured.out
