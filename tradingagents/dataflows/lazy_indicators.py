#!/usr/bin/env python3
"""
惰性技术指标计算器 - 按需计算，避免不必要的计算
"""

import numpy as np
import pandas as pd
from typing import Dict, Set, Callable, Any
from functools import lru_cache


class LazyIndicatorCalculator:
    """
    惰性指标计算器
    
    特性：
    1. 按需计算：只计算请求的指标
    2. 依赖追踪：自动计算依赖的基础指标
    3. 缓存结果：避免重复计算
    4. 批量优化：可一次性请求多个指标
    """
    
    def __init__(self, df: pd.DataFrame):
        """
        初始化
        
        Args:
            df: 包含 OHLCV 的 DataFrame (需要包含: open, high, low, close, volume)
        """
        self.base_df = df.copy()
        self._cache: Dict[str, pd.Series] = {}
        self._indicator_calculators: Dict[str, Callable] = self._build_calculator_registry()
        
    def get_indicator(self, name: str) -> pd.Series:
        """
        获取单个指标（惰性计算）
        
        Args:
            name: 指标名称，如 'close_20_sma', 'rsi', 'macd'
            
        Returns:
            指标数据的 Series
        """
        if name in self._cache:
            return self._cache[name]
        
        if name not in self._indicator_calculators:
            raise ValueError(f"未知指标: {name}")
        
        # 计算并缓存
        calculator = self._indicator_calculators[name]
        result = calculator(self)
        self._cache[name] = result
        return result
    
    def get_indicators(self, names: list[str]) -> pd.DataFrame:
        """
        批量获取多个指标
        
        Args:
            names: 指标名称列表
            
        Returns:
            包含所有请求指标的 DataFrame
        """
        result_df = self.base_df.copy()
        for name in names:
            result_df[name] = self.get_indicator(name)
        return result_df
    
    def _build_calculator_registry(self) -> Dict[str, Callable]:
        """构建指标计算器注册表"""
        calculators = {}
        
        # ==================== 移动平均线 ====================
        for period in [5, 10, 20, 50, 100, 200]:
            # SMA
            calculators[f'close_{period}_sma'] = lambda self, p=period: (
                self.base_df['close'].rolling(window=p).mean()
            )
            # EMA
            calculators[f'close_{period}_ema'] = lambda self, p=period: (
                self.base_df['close'].ewm(span=p, adjust=False).mean()
            )
        
        # ==================== MACD ====================
        def calc_macd(self):
            ema12 = self.base_df['close'].ewm(span=12, adjust=False).mean()
            ema26 = self.base_df['close'].ewm(span=26, adjust=False).mean()
            return ema12 - ema26
        
        def calc_macds(self):
            macd = self.get_indicator('macd')
            return macd.ewm(span=9, adjust=False).mean()
        
        def calc_macdh(self):
            return self.get_indicator('macd') - self.get_indicator('macds')
        
        calculators['macd'] = calc_macd
        calculators['macds'] = calc_macds
        calculators['macdh'] = calc_macdh
        
        # ==================== RSI ====================
        def calc_rsi(self):
            delta = self.base_df['close'].diff()
            gain = delta.where(delta > 0, 0).rolling(window=14).mean()
            loss = -delta.where(delta < 0, 0).rolling(window=14).mean()
            rs = gain / loss
            return 100 - (100 / (1 + rs))
        
        calculators['rsi'] = calc_rsi
        
        # ==================== 布林带 ====================
        def calc_boll(self):
            return self.base_df['close'].rolling(window=20).mean()
        
        def calc_boll_ub(self):
            sma20 = self.get_indicator('boll')
            std20 = self.base_df['close'].rolling(window=20).std()
            return sma20 + (std20 * 2)
        
        def calc_boll_lb(self):
            sma20 = self.get_indicator('boll')
            std20 = self.base_df['close'].rolling(window=20).std()
            return sma20 - (std20 * 2)
        
        def calc_boll_width(self):
            ub = self.get_indicator('boll_ub')
            lb = self.get_indicator('boll_lb')
            boll = self.get_indicator('boll')
            return (ub - lb) / boll
        
        calculators['boll'] = calc_boll
        calculators['boll_ub'] = calc_boll_ub
        calculators['boll_lb'] = calc_boll_lb
        calculators['boll_width'] = calc_boll_width
        
        # ==================== ATR ====================
        def calc_atr(self):
            high_low = self.base_df['high'] - self.base_df['low']
            high_close = np.abs(self.base_df['high'] - self.base_df['close'].shift())
            low_close = np.abs(self.base_df['low'] - self.base_df['close'].shift())
            true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            return true_range.rolling(window=14).mean()
        
        def calc_atr_pct(self):
            atr = self.get_indicator('atr')
            return (atr / self.base_df['close']) * 100
        
        calculators['atr'] = calc_atr
        calculators['atr_pct'] = calc_atr_pct
        
        # ==================== 成交量指标 ====================
        def calc_vwma(self):
            # 成交量加权移动平均
            return (self.base_df['close'] * self.base_df['volume']).rolling(window=20).sum() / \
                   self.base_df['volume'].rolling(window=20).sum()
        
        def calc_obv(self):
            return (np.sign(self.base_df['close'].diff()) * self.base_df['volume']).fillna(0).cumsum()
        
        calculators['vwma'] = calc_vwma
        calculators['obv'] = calc_obv
        
        # 成交量均线
        for period in [5, 10, 20, 50]:
            calculators[f'volume_sma_{period}'] = lambda self, p=period: (
                self.base_df['volume'].rolling(window=p).mean()
            )
        
        # 量比
        calculators['volume_ratio_5'] = lambda self: (
            self.base_df['volume'] / self.get_indicator('volume_sma_5')
        )
        calculators['volume_ratio_20'] = lambda self: (
            self.base_df['volume'] / self.get_indicator('volume_sma_20')
        )
        
        # 成交量变化率
        calculators['volume_change_pct'] = lambda self: (
            self.base_df['volume'].pct_change() * 100
        )
        
        # 成交量加速度
        calculators['volume_acceleration'] = lambda self: (
            self.get_indicator('volume_change_pct').diff()
        )
        
        # ==================== ADX ====================
        def calc_adx_components(self):
            """计算 ADX 及其组件（一次性计算3个指标）"""
            high = self.base_df['high']
            low = self.base_df['low']
            close = self.base_df['close']
            
            # True Range
            high_low = high - low
            high_close = np.abs(high - close.shift())
            low_close = np.abs(low - close.shift())
            tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            atr = tr.rolling(window=14).mean()
            
            # Directional Movement
            up_move = high.diff()
            down_move = -low.diff()
            
            plus_dm = pd.Series(0.0, index=self.base_df.index)
            minus_dm = pd.Series(0.0, index=self.base_df.index)
            
            plus_dm[(up_move > down_move) & (up_move > 0)] = up_move
            minus_dm[(down_move > up_move) & (down_move > 0)] = down_move
            
            plus_di = 100 * (plus_dm.rolling(window=14).mean() / atr)
            minus_di = 100 * (minus_dm.rolling(window=14).mean() / atr)
            
            # ADX
            dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di)
            adx = dx.rolling(window=14).mean()
            
            return adx, plus_di, minus_di
        
        def calc_adx(self):
            if 'adx' not in self._cache:
                adx, plus_di, minus_di = calc_adx_components(self)
                self._cache['adx'] = adx
                self._cache['plus_di'] = plus_di
                self._cache['minus_di'] = minus_di
            return self._cache['adx']
        
        def calc_plus_di(self):
            if 'plus_di' not in self._cache:
                calc_adx(self)  # 会同时缓存 plus_di
            return self._cache['plus_di']
        
        def calc_minus_di(self):
            if 'minus_di' not in self._cache:
                calc_adx(self)  # 会同时缓存 minus_di
            return self._cache['minus_di']
        
        calculators['adx'] = calc_adx
        calculators['plus_di'] = calc_plus_di
        calculators['minus_di'] = calc_minus_di
        
        # ==================== 压力支撑 ====================
        calculators['resistance_20'] = lambda self: self.base_df['high'].rolling(window=20).max()
        calculators['support_20'] = lambda self: self.base_df['low'].rolling(window=20).min()
        calculators['mid_range_20'] = lambda self: (
            (self.get_indicator('resistance_20') + self.get_indicator('support_20')) / 2
        )
        
        calculators['resistance_50'] = lambda self: self.base_df['high'].rolling(window=50).max()
        calculators['support_50'] = lambda self: self.base_df['low'].rolling(window=50).min()
        
        calculators['position_in_range_20'] = lambda self: (
            (self.base_df['close'] - self.get_indicator('support_20')) / 
            (self.get_indicator('resistance_20') - self.get_indicator('support_20'))
        )
        
        # ==================== 趋势指标 ====================
        def calculate_slope(x):
            if len(x) < 2:
                return np.nan
            try:
                slope, _ = np.polyfit(range(len(x)), x, 1)
                return slope
            except:
                return np.nan
        
        calculators['trend_slope_10'] = lambda self: (
            self.base_df['close'].rolling(window=10).apply(calculate_slope, raw=True)
        )
        calculators['trend_slope_20'] = lambda self: (
            self.base_df['close'].rolling(window=20).apply(calculate_slope, raw=True)
        )
        
        # ==================== 动量指标 ====================
        for period in [5, 10, 20]:
            calculators[f'roc_{period}'] = lambda self, p=period: (
                ((self.base_df['close'] - self.base_df['close'].shift(p)) / 
                 self.base_df['close'].shift(p)) * 100
            )
        
        # CCI
        def calc_cci(self):
            tp = (self.base_df['high'] + self.base_df['low'] + self.base_df['close']) / 3
            sma = tp.rolling(window=20).mean()
            mad = tp.rolling(window=20).apply(lambda x: np.abs(x - x.mean()).mean())
            return (tp - sma) / (0.015 * mad)
        
        calculators['cci'] = calc_cci
        
        # Stochastic
        def calc_stoch_k(self):
            low_min = self.base_df['low'].rolling(window=14).min()
            high_max = self.base_df['high'].rolling(window=14).max()
            return 100 * ((self.base_df['close'] - low_min) / (high_max - low_min))
        
        def calc_stoch_d(self):
            return self.get_indicator('stoch_k').rolling(window=3).mean()
        
        calculators['stoch_k'] = calc_stoch_k
        calculators['stoch_d'] = calc_stoch_d
        
        # Williams %R
        calculators['williams_r'] = lambda self: (
            -100 * ((self.base_df['high'].rolling(window=14).max() - self.base_df['close']) / 
             (self.base_df['high'].rolling(window=14).max() - self.base_df['low'].rolling(window=14).min()))
        )
        
        return calculators
    
    def get_available_indicators(self) -> list[str]:
        """获取所有可用指标名称"""
        return sorted(self._indicator_calculators.keys())
    
    def clear_cache(self):
        """清空缓存"""
        self._cache.clear()


def get_lazy_calculator(df: pd.DataFrame) -> LazyIndicatorCalculator:
    """
    创建惰性计算器的工厂函数
    
    Args:
        df: 包含 OHLCV 的 DataFrame
        
    Returns:
        LazyIndicatorCalculator 实例
    """
    return LazyIndicatorCalculator(df)
