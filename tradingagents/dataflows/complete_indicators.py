#!/usr/bin/env python3
"""
完整技术指标计算库
包含：成交量指标、压力支撑线、趋势指标、动量指标、波动率指标、蜡烛图形态等
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional
from .indicator_groups import (
    INDICATOR_GROUPS,
    COMMON_BASE_INDICATORS,
    BASE_COLUMNS,
    get_indicator_columns
)


class CompleteTechnicalIndicators:
    """完整技术指标计算器"""
    
    @staticmethod
    def calculate_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
        """
        计算所有技术指标
        
        Args:
            df: 包含 OHLCV 数据的 DataFrame，需要包含以下列：
                - open, high, low, close, volume
                
        Returns:
            包含所有技术指标的 DataFrame
        """
        result_df = df.copy()
        
        # ==================== 移动平均线 ====================
        # SMA
        result_df["close_5_sma"] = result_df["close"].rolling(window=5).mean()
        result_df["close_10_sma"] = result_df["close"].rolling(window=10).mean()
        result_df["close_20_sma"] = result_df["close"].rolling(window=20).mean()
        result_df["close_50_sma"] = result_df["close"].rolling(window=50).mean()
        result_df["close_100_sma"] = result_df["close"].rolling(window=100).mean()
        result_df["close_200_sma"] = result_df["close"].rolling(window=200).mean()
        
        # EMA
        result_df["close_5_ema"] = result_df["close"].ewm(span=5, adjust=False).mean()
        result_df["close_10_ema"] = result_df["close"].ewm(span=10, adjust=False).mean()
        result_df["close_20_ema"] = result_df["close"].ewm(span=20, adjust=False).mean()
        result_df["close_50_ema"] = result_df["close"].ewm(span=50, adjust=False).mean()
        result_df["close_100_ema"] = result_df["close"].ewm(span=100, adjust=False).mean()
        result_df["close_200_ema"] = result_df["close"].ewm(span=200, adjust=False).mean()
        
        # ==================== MACD ====================
        macd, signal, hist = CompleteTechnicalIndicators._calculate_macd(result_df["close"])
        result_df["macd"] = macd
        result_df["macds"] = signal
        result_df["macdh"] = hist
        
        # ==================== RSI ====================
        result_df["rsi"] = CompleteTechnicalIndicators._calculate_rsi(result_df["close"])
        
        # ==================== 布林带 ====================
        sma20 = result_df["close"].rolling(window=20).mean()
        std20 = result_df["close"].rolling(window=20).std()
        result_df["boll"] = sma20
        result_df["boll_ub"] = sma20 + (std20 * 2)
        result_df["boll_lb"] = sma20 - (std20 * 2)
        result_df["boll_width"] = (result_df["boll_ub"] - result_df["boll_lb"]) / result_df["boll"]
        
        # ==================== ATR ====================
        result_df["atr"] = CompleteTechnicalIndicators._calculate_atr(result_df)
        result_df["atr_pct"] = (result_df["atr"] / result_df["close"]) * 100
        
        # ==================== 成交量指标 ====================
        result_df["vwma"] = CompleteTechnicalIndicators._calculate_vwma(result_df)
        result_df["obv"] = CompleteTechnicalIndicators._calculate_obv(result_df)
        
        # 成交量均线
        result_df["volume_sma_5"] = result_df["volume"].rolling(window=5).mean()
        result_df["volume_sma_10"] = result_df["volume"].rolling(window=10).mean()
        result_df["volume_sma_20"] = result_df["volume"].rolling(window=20).mean()
        result_df["volume_sma_50"] = result_df["volume"].rolling(window=50).mean()
        
        # 量比
        result_df["volume_ratio_5"] = result_df["volume"] / result_df["volume_sma_5"]
        result_df["volume_ratio_20"] = result_df["volume"] / result_df["volume_sma_20"]
        
        # 成交量变化率
        result_df["volume_change_pct"] = result_df["volume"].pct_change() * 100
        
        # 成交量加速度
        result_df["volume_acceleration"] = result_df["volume_change_pct"].diff()
        
        # ==================== ADX ====================
        adx, plus_di, minus_di = CompleteTechnicalIndicators._calculate_adx(result_df)
        result_df["adx"] = adx
        result_df["plus_di"] = plus_di
        result_df["minus_di"] = minus_di
        
        # ==================== 压力支撑指标 ====================
        window = 20
        result_df["resistance_20"] = result_df["high"].rolling(window=window).max()
        result_df["support_20"] = result_df["low"].rolling(window=window).min()
        result_df["mid_range_20"] = (result_df["resistance_20"] + result_df["support_20"]) / 2
        
        window = 50
        result_df["resistance_50"] = result_df["high"].rolling(window=window).max()
        result_df["support_50"] = result_df["low"].rolling(window=window).min()
        
        # 当前价格相对位置
        result_df["position_in_range_20"] = (result_df["close"] - result_df["support_20"]) / (result_df["resistance_20"] - result_df["support_20"])
        
        # ==================== 趋势指标 ====================
        # 趋势线斜率
        def calculate_slope(x):
            if len(x) < 2:
                return np.nan
            try:
                slope, _ = np.polyfit(range(len(x)), x, 1)
                return slope
            except:
                return np.nan
        
        result_df["trend_slope_10"] = result_df["close"].rolling(window=10).apply(
            calculate_slope, raw=True
        )
        result_df["trend_slope_20"] = result_df["close"].rolling(window=20).apply(
            calculate_slope, raw=True
        )
        
        # 线性回归预测值
        def linear_regression_pred(x):
            if len(x) < 2:
                return np.nan
            try:
                slope, intercept = np.polyfit(range(len(x)), x, 1)
                return intercept + slope * len(x)
            except:
                return np.nan
        
        result_df["lr_pred_20"] = result_df["close"].rolling(window=20).apply(
            linear_regression_pred, raw=True
        )
        
        # ==================== 动量指标 ====================
        # ROC
        result_df["roc_5"] = ((result_df["close"] - result_df["close"].shift(5)) / result_df["close"].shift(5)) * 100
        result_df["roc_10"] = ((result_df["close"] - result_df["close"].shift(10)) / result_df["close"].shift(10)) * 100
        result_df["roc_20"] = ((result_df["close"] - result_df["close"].shift(20)) / result_df["close"].shift(20)) * 100
        
        # CCI
        tp = (result_df["high"] + result_df["low"] + result_df["close"]) / 3
        sma_tp = tp.rolling(window=20).mean()
        mad = tp.rolling(window=20).apply(lambda x: np.abs(x - x.mean()).mean(), raw=True)
        result_df["cci_20"] = (tp - sma_tp) / (0.015 * mad)
        
        # CMO
        result_df["cmo_14"] = CompleteTechnicalIndicators._calculate_cmo(result_df["close"], 14)
        
        # MFI
        result_df["mfi_14"] = CompleteTechnicalIndicators._calculate_mfi(result_df)
        
        # ==================== 波动率指标 ====================
        result_df["returns"] = result_df["close"].pct_change()
        result_df["volatility_20"] = result_df["returns"].rolling(window=20).std() * np.sqrt(252)
        result_df["volatility_50"] = result_df["returns"].rolling(window=50).std() * np.sqrt(252)
        
        # ==================== 价格位置指标 ====================
        result_df["price_to_sma_20"] = (result_df["close"] - result_df["close_20_sma"]) / result_df["close_20_sma"] * 100
        result_df["price_to_sma_50"] = (result_df["close"] - result_df["close_50_sma"]) / result_df["close_50_sma"] * 100
        
        result_df["price_to_high_20"] = (result_df["close"] - result_df["high"].rolling(window=20).max()) / result_df["high"].rolling(window=20).max() * 100
        result_df["price_to_low_20"] = (result_df["close"] - result_df["low"].rolling(window=20).min()) / result_df["low"].rolling(window=20).min() * 100
        
        # ==================== 背离指标 ====================
        result_df["price_new_high_20"] = (result_df["close"] == result_df["close"].rolling(window=20).max()).astype(int)
        result_df["rsi_new_high_20"] = (result_df["rsi"] == result_df["rsi"].rolling(window=20).max()).astype(int)
        
        result_df["price_new_low_20"] = (result_df["close"] == result_df["close"].rolling(window=20).min()).astype(int)
        result_df["rsi_new_low_20"] = (result_df["rsi"] == result_df["rsi"].rolling(window=20).min()).astype(int)
        
        # ==================== 交叉信号 ====================
        result_df["sma_5_20_cross"] = np.where(
            (result_df["close_5_sma"] > result_df["close_20_sma"]) & (result_df["close_5_sma"].shift(1) <= result_df["close_20_sma"].shift(1)),
            1,
            np.where(
                (result_df["close_5_sma"] < result_df["close_20_sma"]) & (result_df["close_5_sma"].shift(1) >= result_df["close_20_sma"].shift(1)),
                -1,
                0
            )
        )
        
        result_df["sma_20_50_cross"] = np.where(
            (result_df["close_20_sma"] > result_df["close_50_sma"]) & (result_df["close_20_sma"].shift(1) <= result_df["close_50_sma"].shift(1)),
            1,
            np.where(
                (result_df["close_20_sma"] < result_df["close_50_sma"]) & (result_df["close_20_sma"].shift(1) >= result_df["close_50_sma"].shift(1)),
                -1,
                0
            )
        )
        
        result_df["macd_cross"] = np.where(
            (result_df["macd"] > result_df["macds"]) & (result_df["macd"].shift(1) <= result_df["macds"].shift(1)),
            1,
            np.where(
                (result_df["macd"] < result_df["macds"]) & (result_df["macd"].shift(1) >= result_df["macds"].shift(1)),
                -1,
                0
            )
        )
        
        result_df["rsi_overbought"] = (result_df["rsi"] >= 70).astype(int)
        result_df["rsi_oversold"] = (result_df["rsi"] <= 30).astype(int)
        
        result_df["boll_breakout_up"] = (result_df["close"] > result_df["boll_ub"]).astype(int)
        result_df["boll_breakout_down"] = (result_df["close"] < result_df["boll_lb"]).astype(int)
        
        return result_df
    
    @staticmethod
    def get_indicator_group(df: pd.DataFrame, indicator: str, look_back_days: int = 120) -> pd.DataFrame:
        """
        获取指定指标组的数据
        
        Args:
            df: 包含所有指标的 DataFrame
            indicator: 指标名称或指标组名称
            look_back_days: 回看天数
            
        Returns:
            包含指定指标的 DataFrame
        """
        keep_cols = get_indicator_columns(indicator, list(df.columns))
        
        # 只保留需要的列
        result_df = df[[col for col in keep_cols if col in df.columns]].copy()
        
        # 只返回最近look_back_days天的数据
        result_df = result_df.tail(look_back_days + 10)
        
        return result_df
    
    @staticmethod
    def _calculate_rsi(prices, period=14):
        """计算RSI指标"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    @staticmethod
    def _calculate_macd(prices, fast=12, slow=26, signal=9):
        """计算MACD指标"""
        ema_fast = prices.ewm(span=fast, adjust=False).mean()
        ema_slow = prices.ewm(span=slow, adjust=False).mean()
        macd = ema_fast - ema_slow
        signal_line = macd.ewm(span=signal, adjust=False).mean()
        histogram = macd - signal_line
        return macd, signal_line, histogram
    
    @staticmethod
    def _calculate_atr(df, period=14):
        """计算ATR指标"""
        high_low = df["high"] - df["low"]
        high_close = np.abs(df["high"] - df["close"].shift())
        low_close = np.abs(df["low"] - df["close"].shift())
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        return atr
    
    @staticmethod
    def _calculate_vwma(df, period=20):
        """计算VWMA指标"""
        typical_price = (df["high"] + df["low"] + df["close"]) / 3
        vp = typical_price * df["volume"]
        vwma = vp.rolling(window=period).sum() / df["volume"].rolling(window=period).sum()
        return vwma
    
    @staticmethod
    def _calculate_obv(df):
        """计算OBV指标"""
        obv = (np.sign(df["close"].diff()) * df["volume"]).fillna(0).cumsum()
        return obv
    
    @staticmethod
    def _calculate_adx(df, period=14):
        """计算ADX指标"""
        high = df["high"]
        low = df["low"]
        close = df["close"]
        
        plus_dm = high.diff()
        minus_dm = low.diff() * (-1)
        
        plus_dm = plus_dm.where((plus_dm > minus_dm) & (plus_dm > 0), 0)
        minus_dm = minus_dm.where((minus_dm > plus_dm) & (minus_dm > 0), 0)
        
        tr = CompleteTechnicalIndicators._calculate_atr(df, period=1)
        
        plus_di = 100 * (plus_dm.rolling(window=period).mean() / tr.rolling(window=period).mean())
        minus_di = 100 * (minus_dm.rolling(window=period).mean() / tr.rolling(window=period).mean())
        
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.rolling(window=period).mean()
        
        return adx, plus_di, minus_di
    
    @staticmethod
    def _calculate_cmo(prices, period=14):
        """计算CMO指标"""
        deltas = prices.diff()
        gains = deltas.where(deltas > 0, 0).rolling(window=period).sum()
        losses = -deltas.where(deltas < 0, 0).rolling(window=period).sum()
        return 100 * (gains - losses) / (gains + losses)
    
    @staticmethod
    def _calculate_mfi(df, period=14):
        """计算MFI指标"""
        typical_price = (df["high"] + df["low"] + df["close"]) / 3
        raw_money_flow = typical_price * df["volume"]
        
        positive_flow = []
        negative_flow = []
        
        for i in range(1, len(typical_price)):
            if typical_price.iloc[i] > typical_price.iloc[i-1]:
                positive_flow.append(raw_money_flow.iloc[i])
                negative_flow.append(0)
            elif typical_price.iloc[i] < typical_price.iloc[i-1]:
                positive_flow.append(0)
                negative_flow.append(raw_money_flow.iloc[i])
            else:
                positive_flow.append(0)
                negative_flow.append(0)
        
        positive_flow = pd.Series([0] + positive_flow, index=df.index)
        negative_flow = pd.Series([0] + negative_flow, index=df.index)
        
        pos_sum = positive_flow.rolling(window=period).sum()
        neg_sum = negative_flow.rolling(window=period).sum()
        
        money_ratio = pos_sum / neg_sum
        mfi = 100 - (100 / (1 + money_ratio))
        return mfi


class CompleteCandlestickPatterns:
    """完整蜡烛图形态识别器"""
    
    @staticmethod
    def identify_patterns(df: pd.DataFrame) -> pd.DataFrame:
        """
        识别蜡烛图形态
        
        Args:
            df: 包含 OHLCV 数据的 DataFrame
            
        Returns:
            包含蜡烛图形态的 DataFrame
        """
        patterns = []
        
        for i in range(3, len(df)):
            prev3 = df.iloc[i-3] if i >= 3 else None
            prev2 = df.iloc[i-2]
            prev1 = df.iloc[i-1]
            curr = df.iloc[i]
            
            pattern_info = {
                "timestamp": curr.get("timestamp", curr.get("date", i)),
                "open": curr["open"],
                "high": curr["high"],
                "low": curr["low"],
                "close": curr["close"],
                "patterns": []
            }
            
            curr_body = abs(curr["close"] - curr["open"])
            curr_range = curr["high"] - curr["low"]
            curr_upper_shadow = curr["high"] - max(curr["open"], curr["close"])
            curr_lower_shadow = min(curr["open"], curr["close"]) - curr["low"]
            curr_is_bullish = curr["close"] > curr["open"]
            curr_is_bearish = curr["close"] < curr["open"]
            
            prev1_body = abs(prev1["close"] - prev1["open"])
            prev1_range = prev1["high"] - prev1["low"]
            prev1_is_bullish = prev1["close"] > prev1["open"]
            prev1_is_bearish = prev1["close"] < prev1["open"]
            
            prev2_body = abs(prev2["close"] - prev2["open"])
            prev2_is_bullish = prev2["close"] > prev2["open"]
            prev2_is_bearish = prev2["close"] < prev2["open"]
            
            if curr_body < curr_range * 0.1:
                if curr_upper_shadow > curr_body * 3 and curr_lower_shadow > curr_body * 3:
                    pattern_info["patterns"].append("DOJI_LONG_LEGGED")
                elif curr_upper_shadow > curr_lower_shadow * 2:
                    pattern_info["patterns"].append("DOJI_GRAVESTONE")
                elif curr_lower_shadow > curr_upper_shadow * 2:
                    pattern_info["patterns"].append("DOJI_DRAGONFLY")
                else:
                    pattern_info["patterns"].append("DOJI")
            
            if (curr_body < curr_range * 0.35 and
                curr_lower_shadow > curr_body * 2 and
                curr_upper_shadow < curr_body * 0.5):
                if curr_is_bullish:
                    pattern_info["patterns"].append("HAMMER")
                else:
                    pattern_info["patterns"].append("HANGING_MAN")
            
            if (curr_body < curr_range * 0.35 and
                curr_upper_shadow > curr_body * 2 and
                curr_lower_shadow < curr_body * 0.5):
                if curr_is_bearish:
                    pattern_info["patterns"].append("INVERTED_HAMMER")
                else:
                    pattern_info["patterns"].append("SHOOTING_STAR")
            
            if (curr_body < curr_range * 0.5 and
                curr_body > curr_range * 0.2 and
                curr_upper_shadow > curr_body * 0.5 and
                curr_lower_shadow > curr_body * 0.5):
                pattern_info["patterns"].append("SPINNING_TOP")
            
            if curr_body > curr_range * 0.8:
                if curr_is_bullish:
                    pattern_info["patterns"].append("MARUBOZU_BULLISH")
                else:
                    pattern_info["patterns"].append("MARUBOZU_BEARISH")
            
            if curr_upper_shadow > curr_body * 3:
                pattern_info["patterns"].append("LONG_UPPER_SHADOW")
            if curr_lower_shadow > curr_body * 3:
                pattern_info["patterns"].append("LONG_LOWER_SHADOW")
            
            if (prev1_is_bearish and
                curr_is_bullish and
                curr["open"] < prev1["close"] and
                curr["close"] > prev1["open"] and
                curr_body > prev1_body * 1.3):
                pattern_info["patterns"].append("BULLISH_ENGULFING")
            
            if (prev1_is_bullish and
                curr_is_bearish and
                curr["open"] > prev1["close"] and
                curr["close"] < prev1["open"] and
                curr_body > prev1_body * 1.3):
                pattern_info["patterns"].append("BEARISH_ENGULFING")
            
            if (prev1_is_bearish and
                curr_is_bullish and
                curr["open"] < prev1["low"] and
                curr["close"] > (prev1["open"] + prev1["close"]) / 2 and
                curr["close"] < prev1["open"]):
                pattern_info["patterns"].append("PIERCING_PATTERN")
            
            if (prev1_is_bullish and
                curr_is_bearish and
                curr["open"] > prev1["high"] and
                curr["close"] < (prev1["open"] + prev1["close"]) / 2 and
                curr["close"] > prev1["close"]):
                pattern_info["patterns"].append("DARK_CLOUD_COVER")
            
            if (curr_body < prev1_body * 0.6 and
                curr["high"] < prev1["high"] and
                curr["low"] > prev1["low"]):
                if prev1_is_bullish and curr_is_bearish:
                    pattern_info["patterns"].append("HARAMI_BEARISH")
                elif prev1_is_bearish and curr_is_bullish:
                    pattern_info["patterns"].append("HARAMI_BULLISH")
                else:
                    pattern_info["patterns"].append("HARAMI")
            
            if (curr_body < curr_range * 0.1 and
                curr["high"] < prev1["high"] and
                curr["low"] > prev1["low"]):
                pattern_info["patterns"].append("HARAMI_CROSS")
            
            if abs(curr["low"] - prev1["low"]) < prev1_range * 0.01:
                pattern_info["patterns"].append("FLAT_BOTTOM")
            if abs(curr["high"] - prev1["high"]) < prev1_range * 0.01:
                pattern_info["patterns"].append("FLAT_TOP")
            
            if i >= 3:
                prev3_body = abs(prev3["close"] - prev3["open"])
                prev3_is_bullish = prev3["close"] > prev3["open"]
                prev3_is_bearish = prev3["close"] < prev3["open"]
                
                if (prev3_is_bearish and
                    prev2_body < prev3_body * 0.5 and
                    prev1_is_bullish and
                    prev1_body > prev2_body * 1.5):
                    pattern_info["patterns"].append("MORNING_STAR")
                
                if (prev3_is_bullish and
                    prev2_body < prev3_body * 0.5 and
                    prev1_is_bearish and
                    prev1_body > prev2_body * 1.5):
                    pattern_info["patterns"].append("EVENING_STAR")
                
                if (prev2_is_bearish and
                    prev1_is_bearish and
                    curr_is_bearish and
                    prev1["open"] < prev2["close"] and
                    curr["open"] < prev1["close"] and
                    prev1_body > prev2_body * 0.7 and
                    curr_body > prev1_body * 0.7):
                    pattern_info["patterns"].append("THREE_BLACK_CROWS")
                
                if (prev2_is_bullish and
                    prev1_is_bullish and
                    curr_is_bullish and
                    prev1["open"] > prev2["close"] and
                    curr["open"] > prev1["close"] and
                    prev1_body > prev2_body * 0.7 and
                    curr_body > prev1_body * 0.7):
                    pattern_info["patterns"].append("THREE_WHITE_SOLDIERS")
                
                if (prev3_is_bullish and
                    prev3_body > prev2_body * 2 and
                    prev2_is_bearish and
                    prev1_is_bearish and
                    curr_is_bullish and
                    curr["close"] > prev3["close"] and
                    prev2["low"] > prev3["low"] and
                    prev1["low"] > prev3["low"]):
                    pattern_info["patterns"].append("THREE_RISING_METHODS")
                
                if (prev3_is_bearish and
                    prev3_body > prev2_body * 2 and
                    prev2_is_bullish and
                    prev1_is_bullish and
                    curr_is_bearish and
                    curr["close"] < prev3["close"] and
                    prev2["high"] < prev3["high"] and
                    prev1["high"] < prev3["high"]):
                    pattern_info["patterns"].append("THREE_FALLING_METHODS")
                
                if (prev2_is_bullish and
                    prev1_is_bullish and
                    curr_is_bullish and
                    prev1_body > prev2_body and
                    curr_body < prev1_body * 0.7):
                    pattern_info["patterns"].append("THREE_ADVANCING_BLOCKS")
                
                if (prev2_is_bearish and
                    prev1_is_bearish and
                    curr_is_bearish and
                    prev1_body > prev2_body and
                    curr_body < prev1_body * 0.7):
                    pattern_info["patterns"].append("THREE_DECLINING_BLOCKS")
            
            if i >= 2:
                consecutive_up = 0
                consecutive_down = 0
                for j in range(max(0, i-4), i+1):
                    if df.iloc[j]["close"] > df.iloc[j]["open"]:
                        consecutive_up += 1
                        consecutive_down = 0
                    else:
                        consecutive_down += 1
                        consecutive_up = 0
                
                if consecutive_up >= 3:
                    pattern_info["patterns"].append(f"CONSECUTIVE_UP_{consecutive_up}")
                if consecutive_down >= 3:
                    pattern_info["patterns"].append(f"CONSECUTIVE_DOWN_{consecutive_down}")
            
            if i >= 20:
                recent_high = df.iloc[max(0, i-20):i+1]["high"].max()
                recent_low = df.iloc[max(0, i-20):i+1]["low"].min()
                if curr["high"] >= recent_high * 0.999:
                    pattern_info["patterns"].append("NEW_20_HIGH")
                if curr["low"] <= recent_low * 1.001:
                    pattern_info["patterns"].append("NEW_20_LOW")
            
            if pattern_info["patterns"]:
                patterns.append(pattern_info)
        
        result_df = pd.DataFrame(patterns)
        if len(result_df) > 0:
            result_df["patterns"] = result_df["patterns"].apply(lambda x: "|".join(x))
        return result_df
