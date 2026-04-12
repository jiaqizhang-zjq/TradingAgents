"""Tests for y_finance module split (y_finance_financials and y_finance_indicators).

Tests the module-level exports and indicator parameter definitions.
Does NOT make actual API calls to Yahoo Finance.
"""

import pytest

from tradingagents.dataflows.y_finance_indicators import (
    INDICATOR_PARAMS,
    get_stockstats_indicator,
)
from tradingagents.dataflows.y_finance_financials import (
    get_fundamentals,
    get_balance_sheet,
    get_cashflow,
    get_income_statement,
    get_insider_transactions,
)
from tradingagents.dataflows.y_finance import (
    get_YFin_data_online,
    get_stock_stats_indicators_window,
)


class TestIndicatorParams:
    """Tests for INDICATOR_PARAMS dictionary."""

    def test_indicator_params_is_dict(self):
        """Verify INDICATOR_PARAMS is a non-empty dict."""
        assert isinstance(INDICATOR_PARAMS, dict)
        assert len(INDICATOR_PARAMS) > 0

    def test_expected_indicators_present(self):
        """Verify key indicators are present."""
        expected_keys = [
            "close_50_sma", "close_200_sma", "close_10_ema",
            "macd", "macds", "macdh",
            "rsi",
            "boll", "boll_ub", "boll_lb",
            "atr", "vwma", "mfi"
        ]
        for key in expected_keys:
            assert key in INDICATOR_PARAMS, f"Missing indicator: {key}"

    def test_indicator_descriptions_are_strings(self):
        """Verify all indicator descriptions are non-empty strings."""
        for key, desc in INDICATOR_PARAMS.items():
            assert isinstance(desc, str), f"{key} description should be str"
            assert len(desc) > 10, f"{key} description is too short"

    def test_indicator_descriptions_contain_usage(self):
        """Verify descriptions contain usage info."""
        for key, desc in INDICATOR_PARAMS.items():
            assert "Usage:" in desc, f"{key} description missing 'Usage:'"

    def test_indicator_descriptions_contain_tips(self):
        """Verify descriptions contain tips."""
        for key, desc in INDICATOR_PARAMS.items():
            assert "Tips:" in desc, f"{key} description missing 'Tips:'"


class TestModuleExports:
    """Tests that the y_finance module properly re-exports from sub-modules."""

    def test_y_finance_exports_indicators(self):
        """Verify y_finance re-exports indicator functions."""
        from tradingagents.dataflows import y_finance
        assert hasattr(y_finance, 'INDICATOR_PARAMS')
        assert hasattr(y_finance, 'get_stock_stats_indicators_window')

    def test_y_finance_exports_financials(self):
        """Verify y_finance re-exports financial functions."""
        from tradingagents.dataflows import y_finance
        assert hasattr(y_finance, 'get_fundamentals')
        assert hasattr(y_finance, 'get_balance_sheet')
        assert hasattr(y_finance, 'get_cashflow')
        assert hasattr(y_finance, 'get_income_statement')
        assert hasattr(y_finance, 'get_insider_transactions')

    def test_y_finance_exports_data_online(self):
        """Verify y_finance exports the main data retrieval function."""
        from tradingagents.dataflows import y_finance
        assert hasattr(y_finance, 'get_YFin_data_online')

    def test_financial_functions_are_callable(self):
        """Verify all exported financial functions are callable."""
        assert callable(get_fundamentals)
        assert callable(get_balance_sheet)
        assert callable(get_cashflow)
        assert callable(get_income_statement)
        assert callable(get_insider_transactions)

    def test_indicator_function_is_callable(self):
        """Verify indicator functions are callable."""
        assert callable(get_stockstats_indicator)
        assert callable(get_stock_stats_indicators_window)


class TestGetStockStatsIndicatorsWindow:
    """Tests for get_stock_stats_indicators_window validation."""

    def test_invalid_indicator_raises_error(self):
        """Verify that an unsupported indicator raises ValueError."""
        with pytest.raises(ValueError, match="not supported"):
            get_stock_stats_indicators_window(
                "AAPL", "invalid_indicator", "2024-01-15", 30
            )
