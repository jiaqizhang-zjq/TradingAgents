#!/usr/bin/env python3
"""
移动平均线和趋势指标计算模块
包含: SMA, EMA, 布林带, ATR等
"""

import numpy as np
import pandas as pd
from typing import Tuple


class MovingAverageIndicators:
    """移动平均线指标计算器"""
    
    @staticmethod
    def calculate_sma(df: pd.DataFrame, inplace: bool = False) -> pd.DataFrame:
        """
        计算简单移动平均线 (SMA)
        
        Args:
            df: 包含 close 列的 DataFrame
            inplace: True则直接修改df，False则返回新DataFrame
            
        Returns:
            添加了 SMA 指标的 DataFrame
        """
        if not inplace:
            df = df.copy()
        
        for period in [5, 10, 20, 50, 100, 200]:
            df[f"close_{period}_sma"] = df["close"].rolling(window=period).mean()
        
        return df
    
    @staticmethod
    def calculate_ema(df: pd.DataFrame, inplace: bool = False) -> pd.DataFrame:
        """
        计算指数移动平均线 (EMA)
        
        Args:
            df: 包含 close 列的 DataFrame
            inplace: True则直接修改df，False则返回新DataFrame
            
        Returns:
            添加了 EMA 指标的 DataFrame
        """
        if not inplace:
            df = df.copy()
        
        for period in [5, 10, 20, 50, 100, 200]:
            df[f"close_{period}_ema"] = df["close"].ewm(span=period, adjust=False).mean()
        
        return df
    
    @staticmethod
    def calculate_bollinger_bands(df: pd.DataFrame, period: int = 20, std_multiplier: float = 2.0, inplace: bool = False) -> pd.DataFrame:
        """
        计算布林带 (Bollinger Bands)
        
        Args:
            df: 包含 close 列的 DataFrame
            period: 周期，默认 20
            std_multiplier: 标准差倍数，默认 2.0
            inplace: True则直接修改df，False则返回新DataFrame
            
        Returns:
            添加了布林带指标的 DataFrame
        """
        if not inplace:
            df = df.copy()
        
        sma = df["close"].rolling(window=period).mean()
        std = df["close"].rolling(window=period).std()
        
        df["boll"] = sma
        df["boll_ub"] = sma + (std * std_multiplier)
        df["boll_lb"] = sma - (std * std_multiplier)
        df["boll_width"] = (df["boll_ub"] - df["boll_lb"]) / df["boll"]
        
        return df
    
    @staticmethod
    def calculate_atr(df: pd.DataFrame, period: int = 14, inplace: bool = False) -> pd.DataFrame:
        """
        计算平均真实波幅 (ATR)
        
        Args:
            df: 包含 high, low, close 列的 DataFrame
            period: 周期，默认 14
            inplace: True则直接修改df，False则返回新DataFrame
            
        Returns:
            添加了 ATR 指标的 DataFrame
        """
        if not inplace:
            df = df.copy()
        
        high_low = df["high"] - df["low"]
        high_close = np.abs(df["high"] - df["close"].shift())
        low_close = np.abs(df["low"] - df["close"].shift())
        
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        
        df["atr"] = atr
        df["atr_pct"] = (df["atr"] / df["close"]) * 100
        
        return df
