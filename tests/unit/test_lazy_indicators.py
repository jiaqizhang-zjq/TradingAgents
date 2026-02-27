"""
测试惰性指标计算器
"""

import pytest
import pandas as pd
import numpy as np
from tradingagents.dataflows.lazy_indicators import LazyIndicatorCalculator, get_lazy_calculator


@pytest.fixture
def sample_ohlcv_data():
    """生成样本OHLCV数据"""
    dates = pd.date_range('2024-01-01', periods=100, freq='D')
    np.random.seed(42)
    
    # 生成模拟股票数据
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


class TestLazyIndicatorCalculator:
    """测试LazyIndicatorCalculator类"""
    
    def test_initialization(self, sample_ohlcv_data):
        """测试初始化"""
        calc = LazyIndicatorCalculator(sample_ohlcv_data)
        assert calc.base_df is not None
        assert len(calc.base_df) == 100
        assert len(calc._cache) == 0, "初始化时缓存应该为空"
    
    def test_get_single_indicator(self, sample_ohlcv_data):
        """测试获取单个指标"""
        calc = LazyIndicatorCalculator(sample_ohlcv_data)
        
        # 获取SMA20
        sma20 = calc.get_indicator('close_20_sma')
        assert isinstance(sma20, pd.Series)
        assert len(sma20) == 100
        assert not sma20.iloc[-1] is np.nan, "最后一个值不应该是NaN"
    
    def test_cache_mechanism(self, sample_ohlcv_data):
        """测试缓存机制"""
        calc = LazyIndicatorCalculator(sample_ohlcv_data)
        
        # 第一次调用
        sma20_1 = calc.get_indicator('close_20_sma')
        assert 'close_20_sma' in calc._cache, "计算后应该缓存"
        
        # 第二次调用
        sma20_2 = calc.get_indicator('close_20_sma')
        assert sma20_1 is sma20_2, "应该返回缓存的对象（内存地址相同）"
    
    def test_get_multiple_indicators(self, sample_ohlcv_data):
        """测试批量获取指标"""
        calc = LazyIndicatorCalculator(sample_ohlcv_data)
        
        indicators = ['close_20_sma', 'close_50_sma', 'rsi', 'macd']
        result_df = calc.get_indicators(indicators)
        
        assert isinstance(result_df, pd.DataFrame)
        assert all(ind in result_df.columns for ind in indicators), "所有指标都应该在结果中"
        assert len(result_df) == 100
    
    def test_sma_calculation(self, sample_ohlcv_data):
        """测试SMA计算正确性"""
        calc = LazyIndicatorCalculator(sample_ohlcv_data)
        
        sma20 = calc.get_indicator('close_20_sma')
        
        # 手动计算验证
        expected = sample_ohlcv_data['close'].rolling(window=20).mean()
        pd.testing.assert_series_equal(sma20, expected, check_names=False)
    
    def test_ema_calculation(self, sample_ohlcv_data):
        """测试EMA计算正确性"""
        calc = LazyIndicatorCalculator(sample_ohlcv_data)
        
        ema20 = calc.get_indicator('close_20_ema')
        
        # 手动计算验证
        expected = sample_ohlcv_data['close'].ewm(span=20, adjust=False).mean()
        pd.testing.assert_series_equal(ema20, expected, check_names=False)
    
    def test_rsi_calculation(self, sample_ohlcv_data):
        """测试RSI计算"""
        calc = LazyIndicatorCalculator(sample_ohlcv_data)
        
        rsi = calc.get_indicator('rsi')
        
        # 验证RSI范围
        assert rsi.min() >= 0, "RSI最小值应该>=0"
        assert rsi.max() <= 100, "RSI最大值应该<=100"
    
    def test_macd_calculation(self, sample_ohlcv_data):
        """测试MACD计算"""
        calc = LazyIndicatorCalculator(sample_ohlcv_data)
        
        macd = calc.get_indicator('macd')
        macds = calc.get_indicator('macds')
        macdh = calc.get_indicator('macdh')
        
        # 验证关系
        expected_macdh = macd - macds
        pd.testing.assert_series_equal(macdh, expected_macdh, check_names=False)
    
    def test_bollinger_bands(self, sample_ohlcv_data):
        """测试布林带计算"""
        calc = LazyIndicatorCalculator(sample_ohlcv_data)
        
        boll = calc.get_indicator('boll')
        boll_ub = calc.get_indicator('boll_ub')
        boll_lb = calc.get_indicator('boll_lb')
        
        # 验证上轨 >= 中轨 >= 下轨（忽略NaN值）
        valid_indices = ~(boll.isna() | boll_ub.isna() | boll_lb.isna())
        assert (boll_ub[valid_indices] >= boll[valid_indices]).all(), "上轨应该>=中轨"
        assert (boll[valid_indices] >= boll_lb[valid_indices]).all(), "中轨应该>=下轨"
    
    def test_dependent_indicators(self, sample_ohlcv_data):
        """测试依赖指标的计算（如MACDH依赖MACD和MACDS）"""
        calc = LazyIndicatorCalculator(sample_ohlcv_data)
        
        # 先计算MACDH（会自动计算MACD和MACDS）
        macdh = calc.get_indicator('macdh')
        
        # 验证依赖指标也被缓存
        assert 'macd' in calc._cache, "依赖的MACD应该被缓存"
        assert 'macds' in calc._cache, "依赖的MACDS应该被缓存"
    
    def test_clear_cache(self, sample_ohlcv_data):
        """测试清空缓存"""
        calc = LazyIndicatorCalculator(sample_ohlcv_data)
        
        # 计算一些指标
        calc.get_indicator('close_20_sma')
        calc.get_indicator('rsi')
        assert len(calc._cache) > 0, "缓存应该有内容"
        
        # 清空缓存
        calc.clear_cache()
        assert len(calc._cache) == 0, "缓存应该被清空"
    
    def test_get_available_indicators(self, sample_ohlcv_data):
        """测试获取可用指标列表"""
        calc = LazyIndicatorCalculator(sample_ohlcv_data)
        
        indicators = calc.get_available_indicators()
        assert isinstance(indicators, list)
        assert len(indicators) > 0
        assert 'close_20_sma' in indicators
        assert 'rsi' in indicators
        assert 'macd' in indicators
    
    def test_invalid_indicator_name(self, sample_ohlcv_data):
        """测试无效指标名"""
        calc = LazyIndicatorCalculator(sample_ohlcv_data)
        
        with pytest.raises(ValueError, match="未知指标"):
            calc.get_indicator('invalid_indicator_name')
    
    def test_volume_indicators(self, sample_ohlcv_data):
        """测试成交量指标"""
        calc = LazyIndicatorCalculator(sample_ohlcv_data)
        
        # 测试成交量均线
        volume_sma_20 = calc.get_indicator('volume_sma_20')
        assert isinstance(volume_sma_20, pd.Series)
        
        # 测试量比
        volume_ratio_20 = calc.get_indicator('volume_ratio_20')
        assert volume_ratio_20.min() >= 0, "量比应该>=0"
    
    def test_atr_calculation(self, sample_ohlcv_data):
        """测试ATR计算"""
        calc = LazyIndicatorCalculator(sample_ohlcv_data)
        
        atr = calc.get_indicator('atr')
        atr_pct = calc.get_indicator('atr_pct')
        
        assert atr.min() >= 0, "ATR应该>=0"
        assert atr_pct.min() >= 0, "ATR百分比应该>=0"


class TestFactoryFunction:
    """测试工厂函数"""
    
    def test_get_lazy_calculator(self, sample_ohlcv_data):
        """测试工厂函数"""
        calc = get_lazy_calculator(sample_ohlcv_data)
        assert isinstance(calc, LazyIndicatorCalculator)
        assert calc.base_df is not None


class TestPerformance:
    """测试性能（惰性计算 vs 全量计算）"""
    
    def test_lazy_vs_eager(self, sample_ohlcv_data):
        """测试惰性计算的优势：只计算需要的指标"""
        calc = LazyIndicatorCalculator(sample_ohlcv_data)
        
        # 只请求一个指标
        calc.get_indicator('close_20_sma')
        
        # 验证缓存中只有这一个指标
        assert len(calc._cache) == 1, "惰性计算应该只计算请求的指标"
        assert 'close_20_sma' in calc._cache
        
        # 验证其他指标没有被计算
        assert 'rsi' not in calc._cache
        assert 'macd' not in calc._cache


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
