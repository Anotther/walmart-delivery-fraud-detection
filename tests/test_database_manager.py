from __future__ import annotations

import pandas as pd

import src.config.database as config_database
from src.database.manager import DatabaseManager


class _DummyConnection:
    def __init__(self) -> None:
        self.executed: list[str] = []

    def execute(self, statement):  # noqa: ANN001 - SQLAlchemy statement object
        self.executed.append(str(statement))
        return None


class _DummyContextManager:
    def __init__(self, connection: _DummyConnection) -> None:
        self._connection = connection

    def __enter__(self) -> _DummyConnection:
        return self._connection

    def __exit__(self, exc_type, exc, tb) -> bool:  # noqa: ANN001
        return False


class _BrokenContextManager:
    def __enter__(self):  # noqa: ANN001
        raise RuntimeError("connection failed")

    def __exit__(self, exc_type, exc, tb) -> bool:  # noqa: ANN001
        return False


def test_initialize_marks_database_available_on_success(monkeypatch):
    conn = _DummyConnection()
    monkeypatch.setattr(
        config_database,
        "get_connection",
        lambda: _DummyContextManager(conn),
    )

    def fake_read_sql(query, connection):  # noqa: ANN001
        assert connection is conn
        return pd.DataFrame({"count": [10]})

    monkeypatch.setattr(pd, "read_sql", fake_read_sql)

    manager = DatabaseManager()
    ok = manager.initialize()

    assert ok is True
    assert manager.db_available is True
    assert manager.use_fallback is False
    assert manager._last_error is None
    assert any("SELECT 1" in statement for statement in conn.executed)


def test_initialize_enables_fallback_on_connection_error(monkeypatch):
    monkeypatch.setattr(config_database, "get_connection", lambda: _BrokenContextManager())

    manager = DatabaseManager()
    ok = manager.initialize()

    assert ok is False
    assert manager.db_available is False
    assert manager.use_fallback is True
    assert isinstance(manager._last_error, RuntimeError)
