#!/usr/bin/env python3
"""
成交量指标计算模块
包含: VWMA, OBV, 成交量均线, 量比等
"""

import numpy as np
import pandas as pd


class VolumeIndicators:
    """成交量指标计算器"""
    
    @staticmethod
    def calculate_vwma(df: pd.DataFrame, period: int = 20) -> pd.Series:
        """
        计算成交量加权移动平均 (VWMA)
        
        Args:
            df: 包含 close, volume 列的 DataFrame
            period: 周期，默认 20
            
        Returns:
            VWMA 序列
        """
        vwma = (df["close"] * df["volume"]).rolling(window=period).sum() / df["volume"].rolling(window=period).sum()
        return vwma
    
    @staticmethod
    def calculate_obv(df: pd.DataFrame) -> pd.Series:
        """
        计算能量潮指标 (OBV)
        
        Args:
            df: 包含 close, volume 列的 DataFrame
            
        Returns:
            OBV 序列
        """
        obv = (np.sign(df["close"].diff()) * df["volume"]).fillna(0).cumsum()
        return obv
    
    @staticmethod
    def calculate_volume_sma(df: pd.DataFrame, inplace: bool = False) -> pd.DataFrame:
        """
        计算成交量简单移动平均线
        
        Args:
            df: 包含 volume 列的 DataFrame
            inplace: True则直接修改df，False则返回新DataFrame
            
        Returns:
            添加了成交量均线的 DataFrame
        """
        if not inplace:
            df = df.copy()
        
        for period in [5, 10, 20, 50]:
            df[f"volume_sma_{period}"] = df["volume"].rolling(window=period).mean()
        
        return df
    
    @staticmethod
    def calculate_volume_ratio(df: pd.DataFrame, inplace: bool = False) -> pd.DataFrame:
        """
        计算量比指标
        
        Args:
            df: 包含 volume 和成交量均线的 DataFrame
            inplace: True则直接修改df，False则返回新DataFrame
            
        Returns:
            添加了量比指标的 DataFrame
        """
        if not inplace:
            df = df.copy()
        
        if "volume_sma_5" in df.columns:
            df["volume_ratio_5"] = df["volume"] / df["volume_sma_5"]
        
        if "volume_sma_20" in df.columns:
            df["volume_ratio_20"] = df["volume"] / df["volume_sma_20"]
        
        return df
    
    @staticmethod
    def calculate_volume_change(df: pd.DataFrame, inplace: bool = False) -> pd.DataFrame:
        """
        计算成交量变化率和加速度
        
        Args:
            df: 包含 volume 列的 DataFrame
            inplace: True则直接修改df，False则返回新DataFrame
            
        Returns:
            添加了成交量变化指标的 DataFrame
        """
        if not inplace:
            df = df.copy()
        
        df["volume_change_pct"] = df["volume"].pct_change() * 100
        df["volume_acceleration"] = df["volume_change_pct"].diff()
        
        return df
    
    @staticmethod
    def calculate_all_volume_indicators(df: pd.DataFrame, inplace: bool = False) -> pd.DataFrame:
        """
        计算所有成交量指标
        
        Args:
            df: 包含 OHLCV 数据的 DataFrame
            inplace: True则直接修改df，False则返回新DataFrame
            
        Returns:
            添加了所有成交量指标的 DataFrame
        """
        if not inplace:
            df = df.copy()
        
        df["vwma"] = VolumeIndicators.calculate_vwma(df)
        df["obv"] = VolumeIndicators.calculate_obv(df)
        
        df = VolumeIndicators.calculate_volume_sma(df, inplace=True)
        df = VolumeIndicators.calculate_volume_ratio(df, inplace=True)
        df = VolumeIndicators.calculate_volume_change(df, inplace=True)
        
        return df
