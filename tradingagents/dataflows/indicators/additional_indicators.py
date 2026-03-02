#!/usr/bin/env python3
"""
扩展指标计算器
包含：ROC、CCI、CMO、MFI、波动率、价格位置、背离、交叉信号等
"""

import numpy as np
import pandas as pd


class AdditionalIndicators:
    """扩展指标计算器"""
    
    @staticmethod
    def calculate_roc(df: pd.DataFrame, inplace: bool = False) -> pd.DataFrame:
        """
        计算ROC（变化率）指标
        
        Args:
            df: 包含 close 列的 DataFrame
            inplace: True则直接修改df，False则返回新DataFrame
            
        Returns:
            添加了ROC指标的 DataFrame
        """
        if not inplace:
            df = df.copy()
        
        df["roc_5"] = ((df["close"] - df["close"].shift(5)) / df["close"].shift(5)) * 100
        df["roc_10"] = ((df["close"] - df["close"].shift(10)) / df["close"].shift(10)) * 100
        df["roc_20"] = ((df["close"] - df["close"].shift(20)) / df["close"].shift(20)) * 100
        
        return df
    
    @staticmethod
    def calculate_cci(df: pd.DataFrame, period: int = 20, inplace: bool = False) -> pd.DataFrame:
        """
        计算CCI（顺势指标）
        
        Args:
            df: 包含 OHLC 数据的 DataFrame
            period: 周期
            inplace: True则直接修改df，False则返回新DataFrame
            
        Returns:
            添加了CCI指标的 DataFrame
        """
        if not inplace:
            df = df.copy()
        
        tp = (df["high"] + df["low"] + df["close"]) / 3
        sma_tp = tp.rolling(window=period).mean()
        mad = tp.rolling(window=period).apply(lambda x: np.abs(x - x.mean()).mean(), raw=True)
        df[f"cci_{period}"] = (tp - sma_tp) / (0.015 * mad)
        
        return df
    
    @staticmethod
    def calculate_cmo(prices: pd.Series, period: int = 14) -> pd.Series:
        """
        计算CMO（钱德动量指标）
        
        Args:
            prices: 价格序列
            period: 周期
            
        Returns:
            CMO指标序列
        """
        delta = prices.diff()
        gain = delta.where(delta > 0, 0).rolling(window=period).sum()
        loss = -delta.where(delta < 0, 0).rolling(window=period).sum()
        cmo = 100 * (gain - loss) / (gain + loss)
        return cmo
    
    @staticmethod
    def calculate_mfi(df: pd.DataFrame, period: int = 14) -> pd.Series:
        """
        计算MFI（资金流量指标）
        
        Args:
            df: 包含 OHLCV 数据的 DataFrame
            period: 周期
            
        Returns:
            MFI指标序列
        """
        typical_price = (df["high"] + df["low"] + df["close"]) / 3
        money_flow = typical_price * df["volume"]
        
        positive_flow = money_flow.where(typical_price > typical_price.shift(1), 0).rolling(window=period).sum()
        negative_flow = money_flow.where(typical_price < typical_price.shift(1), 0).rolling(window=period).sum()
        
        mfi = 100 - (100 / (1 + positive_flow / negative_flow))
        return mfi
    
    @staticmethod
    def calculate_volatility(df: pd.DataFrame, inplace: bool = False) -> pd.DataFrame:
        """
        计算波动率指标
        
        Args:
            df: 包含 close 列的 DataFrame
            inplace: True则直接修改df，False则返回新DataFrame
            
        Returns:
            添加了波动率指标的 DataFrame
        """
        if not inplace:
            df = df.copy()
        
        df["returns"] = df["close"].pct_change()
        df["volatility_20"] = df["returns"].rolling(window=20).std() * np.sqrt(252)
        df["volatility_50"] = df["returns"].rolling(window=50).std() * np.sqrt(252)
        
        return df
    
    @staticmethod
    def calculate_price_position(df: pd.DataFrame, inplace: bool = False) -> pd.DataFrame:
        """
        计算价格位置指标
        
        Args:
            df: 包含 close 和 SMA 列的 DataFrame
            inplace: True则直接修改df，False则返回新DataFrame
            
        Returns:
            添加了价格位置指标的 DataFrame
        """
        if not inplace:
            df = df.copy()
        
        df["price_to_sma_20"] = (df["close"] - df["close_20_sma"]) / df["close_20_sma"] * 100
        df["price_to_sma_50"] = (df["close"] - df["close_50_sma"]) / df["close_50_sma"] * 100
        
        df["price_to_high_20"] = (df["close"] - df["high"].rolling(window=20).max()) / df["high"].rolling(window=20).max() * 100
        df["price_to_low_20"] = (df["close"] - df["low"].rolling(window=20).min()) / df["low"].rolling(window=20).min() * 100
        
        return df
    
    @staticmethod
    def calculate_divergence(df: pd.DataFrame, inplace: bool = False) -> pd.DataFrame:
        """
        计算背离指标
        
        Args:
            df: 包含 close 和 rsi 列的 DataFrame
            inplace: True则直接修改df，False则返回新DataFrame
            
        Returns:
            添加了背离指标的 DataFrame
        """
        if not inplace:
            df = df.copy()
        
        df["price_new_high_20"] = (df["close"] == df["close"].rolling(window=20).max()).astype(int)
        df["rsi_new_high_20"] = (df["rsi"] == df["rsi"].rolling(window=20).max()).astype(int)
        
        df["price_new_low_20"] = (df["close"] == df["close"].rolling(window=20).min()).astype(int)
        df["rsi_new_low_20"] = (df["rsi"] == df["rsi"].rolling(window=20).min()).astype(int)
        
        return df
    
    @staticmethod
    def calculate_crosses(df: pd.DataFrame, inplace: bool = False) -> pd.DataFrame:
        """
        计算交叉信号
        
        Args:
            df: 包含移动平均线和MACD的 DataFrame
            inplace: True则直接修改df，False则返回新DataFrame
            
        Returns:
            添加了交叉信号的 DataFrame
        """
        if not inplace:
            df = df.copy()
        
        # SMA交叉
        df["sma_5_20_cross"] = np.where(
            (df["close_5_sma"] > df["close_20_sma"]) & (df["close_5_sma"].shift(1) <= df["close_20_sma"].shift(1)),
            1,
            np.where(
                (df["close_5_sma"] < df["close_20_sma"]) & (df["close_5_sma"].shift(1) >= df["close_20_sma"].shift(1)),
                -1,
                0
            )
        )
        
        df["sma_20_50_cross"] = np.where(
            (df["close_20_sma"] > df["close_50_sma"]) & (df["close_20_sma"].shift(1) <= df["close_50_sma"].shift(1)),
            1,
            np.where(
                (df["close_20_sma"] < df["close_50_sma"]) & (df["close_20_sma"].shift(1) >= df["close_50_sma"].shift(1)),
                -1,
                0
            )
        )
        
        # MACD交叉
        df["macd_cross"] = np.where(
            (df["macd"] > df["macds"]) & (df["macd"].shift(1) <= df["macds"].shift(1)),
            1,
            np.where(
                (df["macd"] < df["macds"]) & (df["macd"].shift(1) >= df["macds"].shift(1)),
                -1,
                0
            )
        )
        
        # RSI超买超卖
        df["rsi_overbought"] = (df["rsi"] >= 70).astype(int)
        df["rsi_oversold"] = (df["rsi"] <= 30).astype(int)
        
        # 布林带突破
        df["boll_breakout_up"] = (df["close"] > df["boll_ub"]).astype(int)
        df["boll_breakout_down"] = (df["close"] < df["boll_lb"]).astype(int)
        
        return df
    
    @staticmethod
    def calculate_all_additional_indicators(df: pd.DataFrame, inplace: bool = False) -> pd.DataFrame:
        """
        计算所有扩展指标
        
        Args:
            df: 包含 OHLCV 数据的 DataFrame
            inplace: True则直接修改df，False则返回新DataFrame
            
        Returns:
            添加了所有扩展指标的 DataFrame
        """
        if not inplace:
            df = df.copy()
        
        df = AdditionalIndicators.calculate_roc(df, inplace=True)
        df = AdditionalIndicators.calculate_cci(df, inplace=True)
        df["cmo_14"] = AdditionalIndicators.calculate_cmo(df["close"], 14)
        df["mfi_14"] = AdditionalIndicators.calculate_mfi(df)
        df = AdditionalIndicators.calculate_volatility(df, inplace=True)
        df = AdditionalIndicators.calculate_price_position(df, inplace=True)
        df = AdditionalIndicators.calculate_divergence(df, inplace=True)
        df = AdditionalIndicators.calculate_crosses(df, inplace=True)
        
        return df
