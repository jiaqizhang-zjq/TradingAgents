"""
pytest 配置文件 - 共享 fixtures 和配置
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


@pytest.fixture
def sample_stock_data():
    """
    生成样本股票数据
    返回包含 OHLCV 的 DataFrame
    """
    dates = pd.date_range('2024-01-01', periods=100, freq='D')
    np.random.seed(42)
    
    close_prices = 100 + np.cumsum(np.random.randn(100) * 2)
    high_prices = close_prices + np.random.rand(100) * 2
    low_prices = close_prices - np.random.rand(100) * 2
    open_prices = close_prices + np.random.randn(100)
    volume = np.random.randint(1000000, 5000000, 100)
    
    df = pd.DataFrame({
        'date': dates,
        'open': open_prices,
        'high': high_prices,
        'low': low_prices,
        'close': close_prices,
        'volume': volume
    })
    
    return df


@pytest.fixture
def mock_llm_response():
    """模拟LLM响应"""
    return {
        "bullish": "上涨, 高",
        "bearish": "下跌, 中等",
        "neutral": "持平, 低"
    }


@pytest.fixture
def sample_symbols():
    """常用测试股票代码"""
    return ["AAPL", "TSLA", "NVDA", "MSFT", "GOOGL"]


@pytest.fixture
def sample_dates():
    """常用测试日期"""
    return [
        "2024-01-15",
        "2024-02-20",
        "2024-03-25"
    ]


def pytest_configure(config):
    """pytest 配置钩子"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
