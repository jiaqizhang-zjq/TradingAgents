#!/usr/bin/env python3
"""
惰性技术指标计算器
使用cached_property实现按需计算和缓存
"""

import pandas as pd
from functools import cached_property
from typing import List, Optional, Dict, Any
from .complete_indicators import CompleteTechnicalIndicators
from .indicators.moving_averages import MovingAverageIndicators
from .indicators.momentum_indicators import MomentumIndicators
from .indicators.volume_indicators import VolumeIndicators


class LazyIndicators:
    """
    惰性指标计算器
    
    使用cached_property按需计算指标，避免不必要的计算开销
    """
    
    def __init__(self, df: pd.DataFrame):
        """
        初始化
        
        Args:
            df: 包含OHLCV数据的DataFrame
        """
        self._df = df.copy()
        self._calculated_groups: Dict[str, bool] = {}
    
    @cached_property
    def moving_averages(self) -> pd.DataFrame:
        """计算移动平均线指标（SMA, EMA, BOLL, ATR）"""
        result = self._df.copy()
        result = MovingAverageIndicators.calculate_sma(result)
        result = MovingAverageIndicators.calculate_ema(result)
        result = MovingAverageIndicators.calculate_bollinger_bands(result)
        result = MovingAverageIndicators.calculate_atr(result)
        self._calculated_groups['moving_averages'] = True
        return result
    
    @cached_property
    def momentum(self) -> pd.DataFrame:
        """计算动量指标（RSI, MACD, ADX）"""
        result = self._df.copy()
        
        # RSI
        result["rsi"] = MomentumIndicators.calculate_rsi(result["close"])
        
        # MACD
        macd, signal, hist = MomentumIndicators.calculate_macd(result["close"])
        result["macd"] = macd
        result["macds"] = signal
        result["macdh"] = hist
        
        # ADX
        adx, plus_di, minus_di = MomentumIndicators.calculate_adx(result)
        result["adx"] = adx
        result["plus_di"] = plus_di
        result["minus_di"] = minus_di
        
        self._calculated_groups['momentum'] = True
        return result
    
    @cached_property
    def volume(self) -> pd.DataFrame:
        """计算成交量指标（OBV, VWMA, 成交量均线等）"""
        result = self._df.copy()
        result = VolumeIndicators.calculate_all_volume_indicators(result)
        self._calculated_groups['volume'] = True
        return result
    
    @cached_property
    def all_indicators(self) -> pd.DataFrame:
        """计算所有指标"""
        return CompleteTechnicalIndicators.calculate_all_indicators(self._df)
    
    def calculate_only(self, groups: List[str]) -> pd.DataFrame:
        """
        只计算指定的指标组
        
        Args:
            groups: 指标组列表，可选值：
                - 'moving_averages': 移动平均线
                - 'momentum': 动量指标
                - 'volume': 成交量指标
                - 'all': 所有指标
        
        Returns:
            包含指定指标组的DataFrame
            
        Examples:
            >>> lazy = LazyIndicators(df)
            >>> # 只计算移动平均线
            >>> result = lazy.calculate_only(['moving_averages'])
            >>> 
            >>> # 计算动量和成交量指标
            >>> result = lazy.calculate_only(['momentum', 'volume'])
        """
        if 'all' in groups:
            return self.all_indicators
        
        result = self._df.copy()
        
        # 按需合并指标
        if 'moving_averages' in groups:
            ma_df = self.moving_averages
            # 只添加新列
            new_cols = [col for col in ma_df.columns if col not in result.columns]
            result = result.join(ma_df[new_cols])
        
        if 'momentum' in groups:
            mom_df = self.momentum
            new_cols = [col for col in mom_df.columns if col not in result.columns]
            result = result.join(mom_df[new_cols])
        
        if 'volume' in groups:
            vol_df = self.volume
            new_cols = [col for col in vol_df.columns if col not in result.columns]
            result = result.join(vol_df[new_cols])
        
        return result
    
    def get_calculated_groups(self) -> List[str]:
        """获取已计算的指标组"""
        return list(self._calculated_groups.keys())
    
    def clear_cache(self):
        """清除所有缓存"""
        # 删除cached_property缓存
        for attr in ['moving_averages', 'momentum', 'volume', 'all_indicators']:
            if attr in self.__dict__:
                del self.__dict__[attr]
        self._calculated_groups.clear()


# 便捷函数
def get_lazy_indicators(df: pd.DataFrame) -> LazyIndicators:
    """
    创建惰性指标计算器
    
    Args:
        df: 包含OHLCV数据的DataFrame
        
    Returns:
        LazyIndicators实例
    """
    return LazyIndicators(df)


def calculate_indicators_lazy(
    df: pd.DataFrame,
    groups: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    惰性计算指标（便捷函数）
    
    Args:
        df: 包含OHLCV数据的DataFrame
        groups: 指标组列表，None表示计算所有指标
        
    Returns:
        包含指标的DataFrame
    """
    lazy = LazyIndicators(df)
    
    if groups is None:
        return lazy.all_indicators
    
    return lazy.calculate_only(groups)
