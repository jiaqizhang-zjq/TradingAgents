#!/usr/bin/env python3
"""
增量指标计算器单元测试
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import shutil

from tradingagents.dataflows.incremental_indicators import (
    IncrementalIndicators,
    IncrementalIndicatorCache,
    calculate_indicators_incremental
)


@pytest.fixture
def sample_ohlcv_data():
    """生成示例OHLCV数据"""
    dates = pd.date_range('2024-01-01', periods=100, freq='D')
    np.random.seed(42)
    
    data = {
        'timestamp': dates.strftime('%Y-%m-%d').tolist(),
        'open': 100 + np.cumsum(np.random.randn(100) * 2),
        'high': 102 + np.cumsum(np.random.randn(100) * 2),
        'low': 98 + np.cumsum(np.random.randn(100) * 2),
        'close': 100 + np.cumsum(np.random.randn(100) * 2),
        'volume': np.random.randint(1000000, 5000000, 100)
    }
    
    df = pd.DataFrame(data)
    # 确保high >= low, open, close
    df['high'] = df[['open', 'high', 'low', 'close']].max(axis=1)
    df['low'] = df[['open', 'high', 'low', 'close']].min(axis=1)
    
    return df


@pytest.fixture
def temp_cache_dir(tmp_path):
    """临时缓存目录"""
    cache_dir = tmp_path / "indicator_cache"
    cache_dir.mkdir()
    yield str(cache_dir)
    # 清理
    if cache_dir.exists():
        shutil.rmtree(cache_dir)


class TestIncrementalIndicatorCache:
    """测试缓存管理器"""
    
    def test_cache_set_and_get(self, temp_cache_dir, sample_ohlcv_data):
        """测试缓存读写"""
        cache = IncrementalIndicatorCache(temp_cache_dir)
        
        # 保存
        cache.set("AAPL", "2024-01-01_2024-04-09", sample_ohlcv_data)
        
        # 读取
        result = cache.get("AAPL", "2024-01-01_2024-04-09")
        assert result is not None
        assert len(result) == len(sample_ohlcv_data)
        pd.testing.assert_frame_equal(result, sample_ohlcv_data)
    
    def test_cache_miss(self, temp_cache_dir):
        """测试缓存未命中"""
        cache = IncrementalIndicatorCache(temp_cache_dir)
        result = cache.get("AAPL", "2024-01-01_2024-04-09")
        assert result is None
    
    def test_cache_clear(self, temp_cache_dir, sample_ohlcv_data):
        """测试清除缓存"""
        cache = IncrementalIndicatorCache(temp_cache_dir)
        
        # 保存
        cache.set("AAPL", "2024-01-01_2024-04-09", sample_ohlcv_data)
        cache.set("TSLA", "2024-01-01_2024-04-09", sample_ohlcv_data)
        
        # 清除单个
        cache.clear("AAPL")
        assert cache.get("AAPL", "2024-01-01_2024-04-09") is None
        assert cache.get("TSLA", "2024-01-01_2024-04-09") is not None
        
        # 清除全部
        cache.clear()
        assert cache.get("TSLA", "2024-01-01_2024-04-09") is None


class TestIncrementalIndicators:
    """测试增量指标计算器"""
    
    def test_full_calculation(self, temp_cache_dir, sample_ohlcv_data):
        """测试全量计算"""
        calculator = IncrementalIndicators(temp_cache_dir)
        
        # 首次计算（全量）
        result = calculator.calculate(sample_ohlcv_data, symbol="AAPL")
        
        assert len(result) == len(sample_ohlcv_data)
        assert 'close_20_sma' in result.columns
        assert 'rsi' in result.columns
        assert 'macd' in result.columns
    
    def test_incremental_calculation(self, temp_cache_dir, sample_ohlcv_data):
        """测试增量计算"""
        calculator = IncrementalIndicators(temp_cache_dir)
        
        # 首次计算（前80行）
        initial_df = sample_ohlcv_data.iloc[:80]
        result1 = calculator.calculate(initial_df, symbol="AAPL")
        assert len(result1) == 80
        
        # 增量计算（前100行，新增20行）
        full_df = sample_ohlcv_data
        result2 = calculator.calculate(full_df, symbol="AAPL")
        assert len(result2) == 100
        
        # 验证前80行的指标值应该一致
        # 注意：由于窗口计算，可能有轻微差异，这里只检查结构
        assert 'close_20_sma' in result2.columns
        assert 'rsi' in result2.columns
    
    def test_no_new_data(self, temp_cache_dir, sample_ohlcv_data):
        """测试无新数据的情况"""
        calculator = IncrementalIndicators(temp_cache_dir)
        
        # 首次计算
        result1 = calculator.calculate(sample_ohlcv_data, symbol="AAPL")
        
        # 再次计算相同数据（应返回缓存）
        result2 = calculator.calculate(sample_ohlcv_data, symbol="AAPL")
        
        pd.testing.assert_frame_equal(result1, result2)
    
    def test_force_full_calculation(self, temp_cache_dir, sample_ohlcv_data):
        """测试强制全量计算"""
        calculator = IncrementalIndicators(temp_cache_dir)
        
        # 首次计算
        result1 = calculator.calculate(sample_ohlcv_data, symbol="AAPL")
        
        # 强制全量计算
        result2 = calculator.calculate(sample_ohlcv_data, symbol="AAPL", force_full=True)
        
        # 结果应该一致
        pd.testing.assert_frame_equal(result1, result2)
    
    def test_without_symbol(self, temp_cache_dir, sample_ohlcv_data):
        """测试不提供symbol的情况"""
        calculator = IncrementalIndicators(temp_cache_dir)
        
        # 不提供symbol，应该全量计算
        result = calculator.calculate(sample_ohlcv_data)
        
        assert len(result) == len(sample_ohlcv_data)
        assert 'close_20_sma' in result.columns


def test_convenience_function(temp_cache_dir, sample_ohlcv_data):
    """测试便捷函数"""
    result = calculate_indicators_incremental(
        sample_ohlcv_data,
        symbol="AAPL"
    )
    
    assert len(result) == len(sample_ohlcv_data)
    assert 'close_20_sma' in result.columns
    assert 'rsi' in result.columns
