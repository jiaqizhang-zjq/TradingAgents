#!/usr/bin/env python3
"""
趋势指标计算器
包含：趋势线斜率、线性回归预测、压力支撑线等
"""

import numpy as np
import pandas as pd


class TrendIndicators:
    """趋势指标计算器"""
    
    @staticmethod
    def calculate_support_resistance(df: pd.DataFrame, inplace: bool = False) -> pd.DataFrame:
        """
        计算压力支撑线
        
        Args:
            df: 包含 OHLC 数据的 DataFrame
            inplace: True则直接修改df，False则返回新DataFrame
            
        Returns:
            添加了压力支撑指标的 DataFrame
        """
        if not inplace:
            df = df.copy()
        
        # 20日压力支撑
        window = 20
        df["resistance_20"] = df["high"].rolling(window=window).max()
        df["support_20"] = df["low"].rolling(window=window).min()
        df["mid_range_20"] = (df["resistance_20"] + df["support_20"]) / 2
        
        # 50日压力支撑
        window = 50
        df["resistance_50"] = df["high"].rolling(window=window).max()
        df["support_50"] = df["low"].rolling(window=window).min()
        
        # 当前价格相对位置
        df["position_in_range_20"] = (df["close"] - df["support_20"]) / (df["resistance_20"] - df["support_20"])
        
        return df
    
    @staticmethod
    def calculate_trend_slope(df: pd.DataFrame, inplace: bool = False) -> pd.DataFrame:
        """
        计算趋势线斜率
        
        Args:
            df: 包含 close 列的 DataFrame
            inplace: True则直接修改df，False则返回新DataFrame
            
        Returns:
            添加了趋势斜率指标的 DataFrame
        """
        if not inplace:
            df = df.copy()
        
        def calculate_slope(x):
            if len(x) < 2:
                return np.nan
            try:
                slope, _ = np.polyfit(range(len(x)), x, 1)
                return slope
            except (ValueError, TypeError, np.linalg.LinAlgError):
                return np.nan
        
        df["trend_slope_10"] = df["close"].rolling(window=10).apply(
            calculate_slope, raw=True
        )
        df["trend_slope_20"] = df["close"].rolling(window=20).apply(
            calculate_slope, raw=True
        )
        
        return df
    
    @staticmethod
    def calculate_linear_regression(df: pd.DataFrame, inplace: bool = False) -> pd.DataFrame:
        """
        计算线性回归预测值
        
        Args:
            df: 包含 close 列的 DataFrame
            inplace: True则直接修改df，False则返回新DataFrame
            
        Returns:
            添加了线性回归预测的 DataFrame
        """
        if not inplace:
            df = df.copy()
        
        def linear_regression_pred(x):
            if len(x) < 2:
                return np.nan
            try:
                slope, intercept = np.polyfit(range(len(x)), x, 1)
                return intercept + slope * len(x)
            except (ValueError, TypeError, np.linalg.LinAlgError):
                return np.nan
        
        df["lr_pred_20"] = df["close"].rolling(window=20).apply(
            linear_regression_pred, raw=True
        )
        
        return df
    
    @staticmethod
    def calculate_all_trend_indicators(df: pd.DataFrame, inplace: bool = False) -> pd.DataFrame:
        """
        计算所有趋势指标
        
        Args:
            df: 包含 OHLCV 数据的 DataFrame
            inplace: True则直接修改df，False则返回新DataFrame
            
        Returns:
            添加了所有趋势指标的 DataFrame
        """
        if not inplace:
            df = df.copy()
        
        df = TrendIndicators.calculate_support_resistance(df, inplace=True)
        df = TrendIndicators.calculate_trend_slope(df, inplace=True)
        df = TrendIndicators.calculate_linear_regression(df, inplace=True)
        
        return df
