"""Tests for memory_learner module.

Tests learning from research records and building situation-recommendation pairs.
"""

import os
import sqlite3
import tempfile
import pytest

from tradingagents.agents.utils.memory_learner import (
    _build_full_situation,
    _build_recommendation,
    _build_simple_recommendation,
    learn_from_research_records,
)
from tradingagents.agents.utils.memory_storage import init_database


@pytest.fixture
def research_db():
    """Create a temporary research tracker database with test data."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    conn = sqlite3.connect(path)
    cursor = conn.cursor()

    # Create research_records table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS research_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            researcher_name TEXT,
            symbol TEXT,
            trade_date TEXT,
            prediction TEXT,
            reasoning TEXT,
            outcome TEXT DEFAULT 'pending',
            actual_return REAL,
            verified_date TEXT
        )
    ''')

    # Insert test data
    test_records = [
        ("bull_researcher", "AAPL", "2024-01-15", "BUY",
         "Strong earnings expected with good market conditions",
         "correct", 0.05, "2024-01-20"),
        ("bull_researcher", "NVDA", "2024-01-16", "BUY",
         "AI demand driving growth in semiconductor sector",
         "correct", 0.12, "2024-01-21"),
        ("bull_researcher", "TSLA", "2024-01-17", "BUY",
         "Production ramp-up ahead of schedule",
         "incorrect", -0.03, "2024-01-22"),
        ("bear_researcher", "META", "2024-01-15", "SELL",
         "Advertising revenue concerns amid economic slowdown",
         "correct", -0.08, "2024-01-20"),
    ]

    for record in test_records:
        cursor.execute('''
            INSERT INTO research_records 
            (researcher_name, symbol, trade_date, prediction, reasoning, 
             outcome, actual_return, verified_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', record)

    # Also insert a pending record (should be ignored)
    cursor.execute('''
        INSERT INTO research_records 
        (researcher_name, symbol, trade_date, prediction, reasoning, outcome)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', ("bull_researcher", "GOOG", "2024-01-18", "BUY", "Good outlook", "pending"))

    conn.commit()
    conn.close()

    yield path
    os.unlink(path)


@pytest.fixture
def analysis_db():
    """Create a temporary analysis database with test data."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    conn = sqlite3.connect(path)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS analysis_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT,
            trade_date TEXT,
            market_report TEXT,
            sentiment_report TEXT,
            news_report TEXT,
            fundamentals_report TEXT,
            candlestick_report TEXT
        )
    ''')

    cursor.execute('''
        INSERT INTO analysis_reports 
        (symbol, trade_date, market_report, sentiment_report, news_report,
         fundamentals_report, candlestick_report)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        "AAPL", "2024-01-15",
        "Market trending up", "Positive sentiment",
        "Good news coverage", "Strong fundamentals",
        "Bullish candlestick pattern"
    ))

    conn.commit()
    conn.close()

    yield path
    os.unlink(path)


class TestBuildFullSituation:
    """Tests for _build_full_situation helper."""

    def test_with_analysis_reports(self, analysis_db):
        """Verify full situation is built from analysis reports."""
        conn = sqlite3.connect(analysis_db)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        result = _build_full_situation(cursor, "AAPL", "2024-01-15", "fallback reasoning")
        conn.close()

        assert "AAPL" in result
        assert "2024-01-15" in result
        assert "市场报告" in result
        assert "Market trending up" in result
        assert "Positive sentiment" in result
        assert "Good news coverage" in result

    def test_without_analysis_reports(self, analysis_db):
        """Verify fallback to reasoning when no analysis reports found."""
        conn = sqlite3.connect(analysis_db)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        result = _build_full_situation(cursor, "NVDA", "2024-01-16", "fallback reasoning")
        conn.close()

        assert result == "fallback reasoning"

    def test_with_invalid_cursor(self):
        """Verify graceful fallback on error."""
        # Create a cursor on a DB without the table
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        conn = sqlite3.connect(path)
        cursor = conn.cursor()

        result = _build_full_situation(cursor, "AAPL", "2024-01-15", "fallback")
        conn.close()
        os.unlink(path)

        assert result == "fallback"


class TestBuildRecommendation:
    """Tests for _build_recommendation helper."""

    def test_format(self):
        """Verify recommendation format."""
        result = _build_recommendation(
            "bull_researcher", "BUY",
            "Strong earnings expected", 0.05
        )

        assert "Bull Researcher" in result
        assert "BUY" in result
        assert "Strong earnings expected" in result
        assert "5.00%" in result

    def test_truncates_long_reasoning(self):
        """Verify that long reasoning is truncated."""
        long_reasoning = "x" * 2000
        result = _build_recommendation(
            "test_memory", "HOLD", long_reasoning, 0.01
        )

        # Should be truncated to 1000 chars + "..."
        assert "..." in result
        assert len(result) < 1100  # reasonable upper bound


class TestBuildSimpleRecommendation:
    """Tests for _build_simple_recommendation helper."""

    def test_format(self):
        """Verify simple recommendation format."""
        result = _build_simple_recommendation("bear_researcher", "SELL", -0.08)

        assert "Bear Researcher" in result
        assert "SELL" in result
        assert "-8.00%" in result

    def test_no_reasoning(self):
        """Verify simple recommendation does not include reasoning."""
        result = _build_simple_recommendation("test", "BUY", 0.10)
        assert "推理" not in result


class TestLearnFromResearchRecords:
    """Tests for learn_from_research_records function."""

    def test_basic_learning(self, research_db):
        """Verify basic learning from research records."""
        # Initialize the memory_records table in the research DB
        init_database(research_db)

        docs, recs, rets, count = learn_from_research_records(
            db_path=research_db,
            memory_name="bull_researcher",
            existing_documents=[],
            limit=100,
            analysis_db_path="/nonexistent/path.db"  # No analysis DB
        )

        assert count == 3  # 3 non-pending bull_researcher records
        assert len(docs) == 3
        assert len(recs) == 3
        assert len(rets) == 3

    def test_deduplication(self, research_db):
        """Verify existing documents are deduplicated."""
        init_database(research_db)

        # First call
        docs1, _, _, count1 = learn_from_research_records(
            db_path=research_db,
            memory_name="bull_researcher",
            existing_documents=[],
            limit=100,
            analysis_db_path="/nonexistent/path.db"
        )

        # Second call with existing documents
        docs2, _, _, count2 = learn_from_research_records(
            db_path=research_db,
            memory_name="bull_researcher",
            existing_documents=docs1,
            limit=100,
            analysis_db_path="/nonexistent/path.db"
        )

        assert count2 == 0  # All duplicates

    def test_filter_by_researcher_name(self, research_db):
        """Verify filtering by researcher name."""
        init_database(research_db)

        docs, _, _, count = learn_from_research_records(
            db_path=research_db,
            memory_name="bear_researcher",
            existing_documents=[],
            limit=100,
            analysis_db_path="/nonexistent/path.db"
        )

        assert count == 1  # Only 1 bear_researcher record

    def test_limit_parameter(self, research_db):
        """Verify limit parameter works."""
        init_database(research_db)

        docs, _, _, count = learn_from_research_records(
            db_path=research_db,
            memory_name="bull_researcher",
            existing_documents=[],
            limit=1,
            analysis_db_path="/nonexistent/path.db"
        )

        assert count == 1

    def test_with_analysis_reports(self, research_db, analysis_db):
        """Verify learning with analysis reports enriches situations."""
        init_database(research_db)

        docs, _, _, count = learn_from_research_records(
            db_path=research_db,
            memory_name="bull_researcher",
            existing_documents=[],
            limit=100,
            analysis_db_path=analysis_db
        )

        # AAPL record should have full analysis report
        aapl_doc = [d for d in docs if "AAPL" in d]
        assert len(aapl_doc) >= 1
        assert "市场报告" in aapl_doc[0]

    def test_nonexistent_db(self):
        """Verify graceful handling of nonexistent database."""
        docs, recs, rets, count = learn_from_research_records(
            db_path="/nonexistent/path.db",
            memory_name="test",
            existing_documents=[],
            limit=100
        )

        assert count == 0
        assert docs == []

    def test_skips_empty_reasoning(self, research_db):
        """Verify records with empty reasoning are skipped."""
        init_database(research_db)

        # Add a record with empty reasoning
        conn = sqlite3.connect(research_db)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO research_records 
            (researcher_name, symbol, trade_date, prediction, reasoning, 
             outcome, actual_return, verified_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', ("empty_researcher", "TEST", "2024-01-20", "BUY", "",
              "correct", 0.01, "2024-01-25"))
        conn.commit()
        conn.close()

        docs, _, _, count = learn_from_research_records(
            db_path=research_db,
            memory_name="empty_researcher",
            existing_documents=[],
            limit=100,
            analysis_db_path="/nonexistent/path.db"
        )

        assert count == 0  # Empty reasoning should be skipped
