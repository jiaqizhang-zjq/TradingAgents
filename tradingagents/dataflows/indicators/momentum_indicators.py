#!/usr/bin/env python3
"""
动量指标计算模块
包含: RSI, MACD, ADX, CMO, MFI等
"""

import numpy as np
import pandas as pd
from typing import Tuple


class MomentumIndicators:
    """动量指标计算器"""
    
    @staticmethod
    def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
        """
        计算相对强弱指数 (RSI)
        
        Args:
            prices: 价格序列
            period: 周期，默认 14
            
        Returns:
            RSI 序列
        """
        delta = prices.diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    @staticmethod
    def calculate_macd(
        prices: pd.Series,
        fast: int = 12,
        slow: int = 26,
        signal: int = 9
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        计算 MACD 指标
        
        Args:
            prices: 价格序列
            fast: 快线周期，默认 12
            slow: 慢线周期，默认 26
            signal: 信号线周期，默认 9
            
        Returns:
            (MACD线, 信号线, MACD柱状图)
        """
        ema_fast = prices.ewm(span=fast, adjust=False).mean()
        ema_slow = prices.ewm(span=slow, adjust=False).mean()
        
        macd = ema_fast - ema_slow
        macd_signal = macd.ewm(span=signal, adjust=False).mean()
        macd_hist = macd - macd_signal
        
        return macd, macd_signal, macd_hist
    
    @staticmethod
    def calculate_adx(df: pd.DataFrame, period: int = 14) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        计算平均趋向指数 (ADX)
        
        Args:
            df: 包含 high, low, close 列的 DataFrame
            period: 周期，默认 14
            
        Returns:
            (ADX, +DI, -DI)
        """
        high_diff = df["high"].diff()
        low_diff = -df["low"].diff()
        
        plus_dm = np.where((high_diff > low_diff) & (high_diff > 0), high_diff, 0)
        minus_dm = np.where((low_diff > high_diff) & (low_diff > 0), low_diff, 0)
        
        tr_series = pd.Series([
            max(
                df["high"].iloc[i] - df["low"].iloc[i],
                abs(df["high"].iloc[i] - df["close"].iloc[i-1]) if i > 0 else 0,
                abs(df["low"].iloc[i] - df["close"].iloc[i-1]) if i > 0 else 0
            )
            for i in range(len(df))
        ], index=df.index)
        
        atr = tr_series.rolling(window=period).mean()
        plus_di = 100 * (pd.Series(plus_dm, index=df.index).rolling(window=period).mean() / atr)
        minus_di = 100 * (pd.Series(minus_dm, index=df.index).rolling(window=period).mean() / atr)
        
        dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.rolling(window=period).mean()
        
        return adx, plus_di, minus_di
    
    @staticmethod
    def calculate_cmo(prices: pd.Series, period: int = 14) -> pd.Series:
        """
        计算钱德动量摆动指标 (CMO)
        
        Args:
            prices: 价格序列
            period: 周期，默认 14
            
        Returns:
            CMO 序列
        """
        delta = prices.diff()
        gain = delta.where(delta > 0, 0).rolling(window=period).sum()
        loss = -delta.where(delta < 0, 0).rolling(window=period).sum()
        
        cmo = 100 * (gain - loss) / (gain + loss)
        return cmo
    
    @staticmethod
    def calculate_mfi(df: pd.DataFrame, period: int = 14) -> pd.Series:
        """
        计算资金流量指标 (MFI)
        
        Args:
            df: 包含 high, low, close, volume 列的 DataFrame
            period: 周期，默认 14
            
        Returns:
            MFI 序列
        """
        typical_price = (df["high"] + df["low"] + df["close"]) / 3
        money_flow = typical_price * df["volume"]
        
        delta = typical_price.diff()
        positive_flow = money_flow.where(delta > 0, 0).rolling(window=period).sum()
        negative_flow = money_flow.where(delta < 0, 0).rolling(window=period).sum()
        
        mfi = 100 - (100 / (1 + positive_flow / negative_flow))
        return mfi
