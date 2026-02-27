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
    def calculate_volume_sma(df: pd.DataFrame) -> pd.DataFrame:
        """
        计算成交量简单移动平均线
        
        Args:
            df: 包含 volume 列的 DataFrame
            
        Returns:
            添加了成交量均线的 DataFrame
        """
        result_df = df.copy()
        
        for period in [5, 10, 20, 50]:
            result_df[f"volume_sma_{period}"] = result_df["volume"].rolling(window=period).mean()
        
        return result_df
    
    @staticmethod
    def calculate_volume_ratio(df: pd.DataFrame) -> pd.DataFrame:
        """
        计算量比指标
        
        Args:
            df: 包含 volume 和成交量均线的 DataFrame
            
        Returns:
            添加了量比指标的 DataFrame
        """
        result_df = df.copy()
        
        if "volume_sma_5" in result_df.columns:
            result_df["volume_ratio_5"] = result_df["volume"] / result_df["volume_sma_5"]
        
        if "volume_sma_20" in result_df.columns:
            result_df["volume_ratio_20"] = result_df["volume"] / result_df["volume_sma_20"]
        
        return result_df
    
    @staticmethod
    def calculate_volume_change(df: pd.DataFrame) -> pd.DataFrame:
        """
        计算成交量变化率和加速度
        
        Args:
            df: 包含 volume 列的 DataFrame
            
        Returns:
            添加了成交量变化指标的 DataFrame
        """
        result_df = df.copy()
        
        result_df["volume_change_pct"] = result_df["volume"].pct_change() * 100
        result_df["volume_acceleration"] = result_df["volume_change_pct"].diff()
        
        return result_df
    
    @staticmethod
    def calculate_all_volume_indicators(df: pd.DataFrame) -> pd.DataFrame:
        """
        计算所有成交量指标
        
        Args:
            df: 包含 OHLCV 数据的 DataFrame
            
        Returns:
            添加了所有成交量指标的 DataFrame
        """
        result_df = df.copy()
        
        result_df["vwma"] = VolumeIndicators.calculate_vwma(result_df)
        result_df["obv"] = VolumeIndicators.calculate_obv(result_df)
        
        result_df = VolumeIndicators.calculate_volume_sma(result_df)
        result_df = VolumeIndicators.calculate_volume_ratio(result_df)
        result_df = VolumeIndicators.calculate_volume_change(result_df)
        
        return result_df
