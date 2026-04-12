"""Tests for memory_storage module.

Tests database operations: init, save, load, clear, and backtest record saving.
"""

import os
import sqlite3
import tempfile
import pytest

from tradingagents.agents.utils.memory_storage import (
    get_connection,
    init_database,
    save_records,
    load_records,
    save_backtest_record,
    clear_records,
)


@pytest.fixture
def db_path():
    """Create a temporary database file for testing."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    os.unlink(path)


class TestGetConnection:
    """Tests for get_connection context manager."""

    def test_connection_commits_on_success(self, db_path):
        """Verify that successful operations are committed."""
        with get_connection(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, val TEXT)")
            cursor.execute("INSERT INTO test (val) VALUES (?)", ("hello",))

        # Verify data persisted
        conn2 = sqlite3.connect(db_path)
        cursor2 = conn2.cursor()
        cursor2.execute("SELECT val FROM test")
        row = cursor2.fetchone()
        conn2.close()

        assert row is not None
        assert row[0] == "hello"

    def test_connection_rollbacks_on_error(self, db_path):
        """Verify that operations are rolled back on error."""
        with get_connection(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, val TEXT)")

        with pytest.raises(Exception):
            with get_connection(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO test (val) VALUES (?)", ("hello",))
                raise Exception("Test error")

        # Verify data was NOT persisted
        conn2 = sqlite3.connect(db_path)
        cursor2 = conn2.cursor()
        cursor2.execute("SELECT COUNT(*) FROM test")
        count = cursor2.fetchone()[0]
        conn2.close()

        assert count == 0


class TestInitDatabase:
    """Tests for init_database function."""

    def test_creates_memory_records_table(self, db_path):
        """Verify that init_database creates the memory_records table."""
        init_database(db_path)

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='memory_records'"
        )
        table = cursor.fetchone()
        conn.close()

        assert table is not None
        assert table[0] == "memory_records"

    def test_creates_index(self, db_path):
        """Verify that init_database creates the index."""
        init_database(db_path)

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_memory_records_memory_name'"
        )
        index = cursor.fetchone()
        conn.close()

        assert index is not None

    def test_idempotent(self, db_path):
        """Verify that calling init_database multiple times is safe."""
        init_database(db_path)
        init_database(db_path)  # Should not raise


class TestSaveAndLoadRecords:
    """Tests for save_records and load_records functions."""

    def test_save_and_load_single_record(self, db_path):
        """Verify saving and loading a single record."""
        init_database(db_path)

        documents = ["Market is bullish for AAPL"]
        recommendations = ["BUY AAPL at current levels"]
        returns = [0.05]

        save_records(db_path, "test_memory", documents, recommendations, returns)

        loaded_docs, loaded_recs, loaded_rets = load_records(db_path, "test_memory")

        assert len(loaded_docs) == 1
        assert loaded_docs[0] == "Market is bullish for AAPL"
        assert loaded_recs[0] == "BUY AAPL at current levels"
        assert loaded_rets[0] == pytest.approx(0.05)

    def test_save_and_load_multiple_records(self, db_path):
        """Verify saving and loading multiple records."""
        init_database(db_path)

        documents = ["Situation A", "Situation B", "Situation C"]
        recommendations = ["Rec A", "Rec B", "Rec C"]
        returns = [0.1, -0.05, 0.03]

        save_records(db_path, "test_memory", documents, recommendations, returns)

        loaded_docs, loaded_recs, loaded_rets = load_records(db_path, "test_memory")

        assert len(loaded_docs) == 3
        assert loaded_rets == pytest.approx([0.1, -0.05, 0.03])

    def test_load_empty_memory(self, db_path):
        """Verify loading from empty database returns empty lists."""
        init_database(db_path)

        loaded_docs, loaded_recs, loaded_rets = load_records(db_path, "nonexistent")

        assert loaded_docs == []
        assert loaded_recs == []
        assert loaded_rets == []

    def test_save_replaces_on_duplicate(self, db_path):
        """Verify that saving with the same situation replaces the record."""
        init_database(db_path)

        save_records(
            db_path, "test_memory",
            ["Same situation"], ["Old rec"], [0.01]
        )
        save_records(
            db_path, "test_memory",
            ["Same situation"], ["New rec"], [0.05]
        )

        loaded_docs, loaded_recs, loaded_rets = load_records(db_path, "test_memory")

        assert len(loaded_docs) == 1
        assert loaded_recs[0] == "New rec"
        assert loaded_rets[0] == pytest.approx(0.05)

    def test_separate_memory_names(self, db_path):
        """Verify that different memory names are isolated."""
        init_database(db_path)

        save_records(db_path, "bull_memory", ["Bull situation"], ["BUY"], [0.1])
        save_records(db_path, "bear_memory", ["Bear situation"], ["SELL"], [-0.05])

        bull_docs, _, _ = load_records(db_path, "bull_memory")
        bear_docs, _, _ = load_records(db_path, "bear_memory")

        assert len(bull_docs) == 1
        assert len(bear_docs) == 1
        assert bull_docs[0] == "Bull situation"
        assert bear_docs[0] == "Bear situation"


class TestSaveBacktestRecord:
    """Tests for save_backtest_record function."""

    def test_save_backtest_record(self, db_path):
        """Verify saving a backtest record."""
        init_database(db_path)

        save_backtest_record(
            db_path, "test_memory",
            "AAPL", "2024-01-15",
            "Market is bullish", "BUY",
            0.08
        )

        loaded_docs, loaded_recs, loaded_rets = load_records(db_path, "test_memory")

        assert len(loaded_docs) == 1
        assert "Market is bullish" in loaded_docs[0]
        assert loaded_rets[0] == pytest.approx(0.08)

    def test_backtest_record_includes_symbol_and_date(self, db_path):
        """Verify that backtest records store symbol and trade_date."""
        init_database(db_path)

        save_backtest_record(
            db_path, "test_memory",
            "NVDA", "2024-02-20",
            "Tech sector strong", "BUY",
            0.12
        )

        # Directly query to check symbol/trade_date columns
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT symbol, trade_date FROM memory_records WHERE memory_name = ?",
            ("test_memory",)
        )
        row = cursor.fetchone()
        conn.close()

        assert row is not None
        assert row[0] == "NVDA"
        assert row[1] == "2024-02-20"


class TestClearRecords:
    """Tests for clear_records function."""

    def test_clear_records(self, db_path):
        """Verify clearing records for a specific memory name."""
        init_database(db_path)

        save_records(db_path, "to_clear", ["Situation"], ["Rec"], [0.01])
        save_records(db_path, "to_keep", ["Other situation"], ["Other rec"], [0.02])

        clear_records(db_path, "to_clear")

        cleared_docs, _, _ = load_records(db_path, "to_clear")
        kept_docs, _, _ = load_records(db_path, "to_keep")

        assert len(cleared_docs) == 0
        assert len(kept_docs) == 1

    def test_clear_nonexistent_memory(self, db_path):
        """Verify clearing nonexistent memory doesn't error."""
        init_database(db_path)
        clear_records(db_path, "nonexistent")  # Should not raise
