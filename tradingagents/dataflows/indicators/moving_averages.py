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
    def calculate_sma(df: pd.DataFrame) -> pd.DataFrame:
        """
        计算简单移动平均线 (SMA)
        
        Args:
            df: 包含 close 列的 DataFrame
            
        Returns:
            添加了 SMA 指标的 DataFrame
        """
        result_df = df.copy()
        
        for period in [5, 10, 20, 50, 100, 200]:
            result_df[f"close_{period}_sma"] = result_df["close"].rolling(window=period).mean()
        
        return result_df
    
    @staticmethod
    def calculate_ema(df: pd.DataFrame) -> pd.DataFrame:
        """
        计算指数移动平均线 (EMA)
        
        Args:
            df: 包含 close 列的 DataFrame
            
        Returns:
            添加了 EMA 指标的 DataFrame
        """
        result_df = df.copy()
        
        for period in [5, 10, 20, 50, 100, 200]:
            result_df[f"close_{period}_ema"] = result_df["close"].ewm(span=period, adjust=False).mean()
        
        return result_df
    
    @staticmethod
    def calculate_bollinger_bands(df: pd.DataFrame, period: int = 20, std_multiplier: float = 2.0) -> pd.DataFrame:
        """
        计算布林带 (Bollinger Bands)
        
        Args:
            df: 包含 close 列的 DataFrame
            period: 周期，默认 20
            std_multiplier: 标准差倍数，默认 2.0
            
        Returns:
            添加了布林带指标的 DataFrame
        """
        result_df = df.copy()
        
        sma = result_df["close"].rolling(window=period).mean()
        std = result_df["close"].rolling(window=period).std()
        
        result_df["boll"] = sma
        result_df["boll_ub"] = sma + (std * std_multiplier)
        result_df["boll_lb"] = sma - (std * std_multiplier)
        result_df["boll_width"] = (result_df["boll_ub"] - result_df["boll_lb"]) / result_df["boll"]
        
        return result_df
    
    @staticmethod
    def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """
        计算平均真实波幅 (ATR)
        
        Args:
            df: 包含 high, low, close 列的 DataFrame
            period: 周期，默认 14
            
        Returns:
            添加了 ATR 指标的 DataFrame
        """
        result_df = df.copy()
        
        high_low = result_df["high"] - result_df["low"]
        high_close = np.abs(result_df["high"] - result_df["close"].shift())
        low_close = np.abs(result_df["low"] - result_df["close"].shift())
        
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        
        result_df["atr"] = atr
        result_df["atr_pct"] = (result_df["atr"] / result_df["close"]) * 100
        
        return result_df
