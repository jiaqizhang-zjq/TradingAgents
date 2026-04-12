"""Tests for exceptions module.

Tests all custom exception classes for correct behavior.
"""

import pytest

from tradingagents.exceptions import (
    TradingAgentsException,
    ValidationError,
    DataError,
    DataFetchError,
    DataValidationError,
    DataNotFoundError,
    InsufficientDataError,
    LLMError,
    LLMInvokeError,
    LLMTimeoutError,
    LLMResponseParseError,
    StateError,
    InvalidStateError,
    MissingStateFieldError,
    ConfigError,
    MissingConfigError,
    InvalidConfigError,
    APIError,
    APIKeyError,
    APIRateLimitError,
    APIResponseError,
    AgentError,
    AgentExecutionError,
    AgentNotFoundError,
    CacheError,
    CacheExpiredError,
    DatabaseError,
    DatabaseConnectionError,
    DatabaseQueryError,
)


class TestExceptionHierarchy:
    """Verify the exception class hierarchy."""

    def test_base_exception(self):
        """TradingAgentsException inherits from Exception."""
        assert issubclass(TradingAgentsException, Exception)

    def test_validation_error_inherits_value_error(self):
        """ValidationError inherits from ValueError (for compat)."""
        assert issubclass(ValidationError, ValueError)

    def test_data_errors_inherit_from_base(self):
        """All data errors inherit from DataError -> TradingAgentsException."""
        for cls in [DataFetchError, DataValidationError, DataNotFoundError, InsufficientDataError]:
            assert issubclass(cls, DataError)
            assert issubclass(cls, TradingAgentsException)

    def test_llm_errors_inherit_from_base(self):
        """All LLM errors inherit from LLMError -> TradingAgentsException."""
        for cls in [LLMInvokeError, LLMTimeoutError, LLMResponseParseError]:
            assert issubclass(cls, LLMError)
            assert issubclass(cls, TradingAgentsException)

    def test_state_errors_inherit_from_base(self):
        """All state errors inherit from StateError."""
        for cls in [InvalidStateError, MissingStateFieldError]:
            assert issubclass(cls, StateError)

    def test_config_errors_inherit_from_base(self):
        """All config errors inherit from ConfigError."""
        for cls in [MissingConfigError, InvalidConfigError]:
            assert issubclass(cls, ConfigError)

    def test_api_errors_inherit_from_base(self):
        """All API errors inherit from APIError."""
        for cls in [APIKeyError, APIRateLimitError, APIResponseError]:
            assert issubclass(cls, APIError)

    def test_agent_errors_inherit_from_base(self):
        """All agent errors inherit from AgentError."""
        for cls in [AgentExecutionError, AgentNotFoundError]:
            assert issubclass(cls, AgentError)


class TestValidationError:
    """Tests for ValidationError."""

    def test_attributes(self):
        err = ValidationError("symbol", "股票代码不能为空")
        assert err.field == "symbol"
        assert err.message == "股票代码不能为空"
        assert "股票代码不能为空" in str(err)

    def test_catchable_as_valueerror(self):
        with pytest.raises(ValueError):
            raise ValidationError("test", "error")


class TestDataFetchError:
    """Tests for DataFetchError."""

    def test_basic(self):
        err = DataFetchError("yfinance", "AAPL", "timeout")
        assert err.vendor == "yfinance"
        assert err.symbol == "AAPL"
        assert err.reason == "timeout"
        assert "yfinance" in str(err)
        assert "AAPL" in str(err)

    def test_with_original_error(self):
        original = ConnectionError("network down")
        err = DataFetchError("yfinance", "AAPL", "network error", original)
        assert err.original_error is original
        assert "network down" in str(err)


class TestDataValidationError:
    """Tests for DataValidationError."""

    def test_attributes(self):
        err = DataValidationError("price", -1.0, "price must be positive")
        assert err.field == "price"
        assert err.value == -1.0
        assert "price" in str(err)
        assert "positive" in str(err)


class TestInsufficientDataError:
    """Tests for InsufficientDataError."""

    def test_attributes(self):
        err = InsufficientDataError(100, 50, "trading days")
        assert err.required == 100
        assert err.actual == 50
        assert "100" in str(err)
        assert "50" in str(err)


class TestLLMInvokeError:
    """Tests for LLMInvokeError."""

    def test_basic(self):
        err = LLMInvokeError("gpt-4", "rate limit exceeded")
        assert err.model == "gpt-4"
        assert "gpt-4" in str(err)
        assert "rate limit" in str(err)

    def test_with_original(self):
        original = RuntimeError("API error")
        err = LLMInvokeError("gpt-4", "invoke failed", original)
        assert err.original_error is original


class TestLLMTimeoutError:
    """Tests for LLMTimeoutError."""

    def test_attributes(self):
        err = LLMTimeoutError("gpt-4", 30)
        assert err.model == "gpt-4"
        assert err.timeout == 30
        assert "30s" in str(err)


class TestAPIRateLimitError:
    """Tests for APIRateLimitError."""

    def test_without_retry_after(self):
        err = APIRateLimitError("yfinance")
        assert err.service == "yfinance"
        assert err.retry_after is None

    def test_with_retry_after(self):
        err = APIRateLimitError("yfinance", retry_after=60)
        assert err.retry_after == 60
        assert "60s" in str(err)


class TestAPIResponseError:
    """Tests for APIResponseError."""

    def test_attributes(self):
        err = APIResponseError("yfinance", 429, "Too many requests")
        assert err.status_code == 429
        assert "429" in str(err)
        assert "Too many requests" in str(err)


class TestMissingStateFieldError:
    """Tests for MissingStateFieldError."""

    def test_attributes(self):
        err = MissingStateFieldError("trade_date", "AgentState")
        assert err.field == "trade_date"
        assert err.state_type == "AgentState"
        assert "trade_date" in str(err)


class TestDatabaseErrors:
    """Tests for database-related errors."""

    def test_connection_error(self):
        err = DatabaseConnectionError("/path/to/db", "file not found")
        assert err.db_path == "/path/to/db"
        assert "file not found" in str(err)

    def test_query_error(self):
        err = DatabaseQueryError("SELECT *", "syntax error")
        assert err.query == "SELECT *"
        assert "syntax error" in str(err)
