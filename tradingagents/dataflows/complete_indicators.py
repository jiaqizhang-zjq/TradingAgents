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
    def get_all_indicator_groups(df: pd.DataFrame, look_back_days: int = 120) -> str:
        """
        获取所有指标组的数据，按组格式化输出
        
        Args:
            df: 包含所有指标的 DataFrame
            look_back_days: 回看天数
            
        Returns:
            格式化的字符串，包含所有指标组
        """
        result = ""
        
        for group_name, group_cols in INDICATOR_GROUPS.items():
            # 获取该组的指标
            keep_cols = get_indicator_columns(group_name, list(df.columns))
            group_df = df[[col for col in keep_cols if col in df.columns]].copy()
            group_df = group_df.tail(look_back_days + 10)
            
            result += f"\n=== {group_name.upper()} INDICATOR GROUP ===\n"
            result += group_df.to_csv(index=False)
            result += "\n"
        
        return result
    
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
        
        # 计算平均成交量用于验证
        avg_volume = df['volume'].mean() if 'volume' in df.columns else 0
        
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
                "volume": curr.get("volume", 0),
                "volume_confirmed": False,
                "patterns": []
            }
            
            curr_body = abs(curr["close"] - curr["open"])
            curr_range = curr["high"] - curr["low"]
            curr_upper_shadow = curr["high"] - max(curr["open"], curr["close"])
            curr_lower_shadow = min(curr["open"], curr["close"]) - curr["low"]
            curr_is_bullish = curr["close"] > curr["open"]
            curr_is_bearish = curr["close"] < curr["open"]
            curr_vol = curr.get("volume", avg_volume)
            
            prev1_body = abs(prev1["close"] - prev1["open"])
            prev1_range = prev1["high"] - prev1["low"]
            prev1_is_bullish = prev1["close"] > prev1["open"]
            prev1_is_bearish = prev1["close"] < prev1["open"]
            prev1_vol = prev1.get("volume", avg_volume)
            
            prev2_body = abs(prev2["close"] - prev2["open"])
            prev2_is_bullish = prev2["close"] > prev2["open"]
            prev2_is_bearish = prev2["close"] < prev2["open"]
            prev2_vol = prev2.get("volume", avg_volume)
            
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
                    # 锤子线：成交量验证 - 应放量
                    if curr_vol > avg_volume * 1.2:
                        pattern_info["volume_confirmed"] = True
                else:
                    pattern_info["patterns"].append("HANGING_MAN")
                    # 上吊线：成交量验证 - 应放量
                    if curr_vol > avg_volume * 1.2:
                        pattern_info["volume_confirmed"] = True
            
            if (curr_body < curr_range * 0.35 and
                curr_upper_shadow > curr_body * 2 and
                curr_lower_shadow < curr_body * 0.5):
                if curr_is_bearish:
                    pattern_info["patterns"].append("INVERTED_HAMMER")
                    # 倒锤子线：成交量验证
                    if curr_vol > avg_volume * 1.2:
                        pattern_info["volume_confirmed"] = True
                else:
                    pattern_info["patterns"].append("SHOOTING_STAR")
                    # 流星线：成交量验证 - 应放量
                    if curr_vol > avg_volume * 1.2:
                        pattern_info["volume_confirmed"] = True
            
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
                # 看涨吞没：成交量验证 - 应放量
                if curr_vol > avg_volume * 1.3:
                    pattern_info["volume_confirmed"] = True
            
            if (prev1_is_bullish and
                curr_is_bearish and
                curr["open"] > prev1["close"] and
                curr["close"] < prev1["open"] and
                curr_body > prev1_body * 1.3):
                pattern_info["patterns"].append("BEARISH_ENGULFING")
                # 看跌吞没：成交量验证 - 应放量
                if curr_vol > avg_volume * 1.3:
                    pattern_info["volume_confirmed"] = True
            
            if (prev1_is_bearish and
                curr_is_bullish and
                curr["open"] < prev1["low"] and
                curr["close"] > (prev1["open"] + prev1["close"]) / 2 and
                curr["close"] < prev1["open"]):
                pattern_info["patterns"].append("PIERCING_PATTERN")
                # 刺穿形态：成交量验证 - 应放量
                if curr_vol > avg_volume * 1.3:
                    pattern_info["volume_confirmed"] = True
            
            if (prev1_is_bullish and
                curr_is_bearish and
                curr["open"] > prev1["high"] and
                curr["close"] < (prev1["open"] + prev1["close"]) / 2 and
                curr["close"] > prev1["close"]):
                pattern_info["patterns"].append("DARK_CLOUD_COVER")
                # 乌云盖顶：成交量验证 - 应放量
                if curr_vol > avg_volume * 1.3:
                    pattern_info["volume_confirmed"] = True
            
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
                    # 早晨之星：成交量验证 - 第三根K线应放量
                    if prev1_vol > avg_volume * 1.3:
                        pattern_info["volume_confirmed"] = True
                
                if (prev3_is_bullish and
                    prev2_body < prev3_body * 0.5 and
                    prev1_is_bearish and
                    prev1_body > prev2_body * 1.5):
                    pattern_info["patterns"].append("EVENING_STAR")
                    # 黄昏之星：成交量验证 - 第三根K线应放量
                    if prev1_vol > avg_volume * 1.3:
                        pattern_info["volume_confirmed"] = True
                
                if (prev2_is_bearish and
                    prev1_is_bearish and
                    curr_is_bearish and
                    prev1["open"] < prev2["close"] and
                    curr["open"] < prev1["close"] and
                    prev1_body > prev2_body * 0.7 and
                    curr_body > prev1_body * 0.7):
                    pattern_info["patterns"].append("THREE_BLACK_CROWS")
                    # 三只乌鸦：成交量验证 - 应伴随放量
                    if (prev2_vol + prev1_vol + curr_vol) / 3 > avg_volume * 1.2:
                        pattern_info["volume_confirmed"] = True
                
                if (prev2_is_bullish and
                    prev1_is_bullish and
                    curr_is_bullish and
                    prev1["open"] > prev2["close"] and
                    curr["open"] > prev1["close"] and
                    prev1_body > prev2_body * 0.7 and
                    curr_body > prev1_body * 0.7):
                    pattern_info["patterns"].append("THREE_WHITE_SOLDIERS")
                    # 三白兵：成交量验证 - 应伴随放量
                    if (prev2_vol + prev1_vol + curr_vol) / 3 > avg_volume * 1.2:
                        pattern_info["volume_confirmed"] = True
                
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


class ChartPatterns:
    """
    图表形态识别器 (西方技术分析)
    识别基于价格走势的几何形态，如头肩顶/底、双顶/底、三角形等
    """
    
    @staticmethod
    def identify_all_patterns(df: pd.DataFrame, lookback: int = 60) -> Dict[str, Any]:
        """
        识别所有图表形态
        
        Args:
            df: 包含 OHLCV 数据的 DataFrame
            lookback: 回溯周期，默认60天
            
        Returns:
            包含所有识别出的形态信息的字典
        """
        if len(df) < lookback:
            lookback = len(df)
        
        recent_df = df.tail(lookback).copy()
        
        patterns = {
            "head_and_shoulders": ChartPatterns._identify_head_and_shoulders(recent_df),
            "double_top": ChartPatterns._identify_double_top(recent_df),
            "double_bottom": ChartPatterns._identify_double_bottom(recent_df),
            "ascending_triangle": ChartPatterns._identify_ascending_triangle(recent_df),
            "descending_triangle": ChartPatterns._identify_descending_triangle(recent_df),
            "symmetrical_triangle": ChartPatterns._identify_symmetrical_triangle(recent_df),
            "flag": ChartPatterns._identify_flag(recent_df),
            "wedge": ChartPatterns._identify_wedge(recent_df),
            "rounding_top": ChartPatterns._identify_rounding_top(recent_df),
            "rounding_bottom": ChartPatterns._identify_rounding_bottom(recent_df),
            "rectangle": ChartPatterns._identify_rectangle(recent_df),
        }
        
        return patterns
    
    @staticmethod
    def _find_peaks_and_troughs(df: pd.DataFrame, window: int = 5) -> tuple:
        """
        找出价格的峰值和谷值
        
        Args:
            df: DataFrame with 'high' and 'low' columns
            window: 窗口大小用于确认峰值/谷值
            
        Returns:
            (peaks, troughs) - 峰值和谷值的索引列表
        """
        highs = df['high'].values
        lows = df['low'].values
        
        peaks = []
        troughs = []
        
        for i in range(window, len(df) - window):
            # 峰值：比前后window个数据点都高
            if all(highs[i] > highs[i-j] for j in range(1, window+1)) and \
               all(highs[i] > highs[i+j] for j in range(1, window+1)):
                peaks.append(i)
            
            # 谷值：比前后window个数据点都低
            if all(lows[i] < lows[i-j] for j in range(1, window+1)) and \
               all(lows[i] < lows[i+j] for j in range(1, window+1)):
                troughs.append(i)
        
        return peaks, troughs
    
    @staticmethod
    def _identify_head_and_shoulders(df: pd.DataFrame) -> Dict[str, Any]:
        """识别头肩顶/底形态"""
        peaks, troughs = ChartPatterns._find_peaks_and_troughs(df)
        
        if len(peaks) < 3:
            return {"detected": False, "type": None, "confidence": 0}
        
        # 计算平均成交量用于比较
        avg_volume = df['volume'].mean()
        
        # 检查头肩顶 (三个峰值，中间最高)
        avg_volume = df['volume'].mean()
        
        for i in range(len(peaks) - 2):
            left_shoulder = df.iloc[peaks[i]]['high']
            head = df.iloc[peaks[i+1]]['high']
            right_shoulder = df.iloc[peaks[i+2]]['high']
            
            # 头肩顶条件：中间峰值最高，左右肩大致相等
            if (head > left_shoulder and head > right_shoulder and
                abs(left_shoulder - right_shoulder) / head < 0.05):  # 5%容差
                
                # 计算颈线
                left_trough_idx = [t for t in troughs if peaks[i] < t < peaks[i+1]]
                right_trough_idx = [t for t in troughs if peaks[i+1] < t < peaks[i+2]]
                
                if left_trough_idx and right_trough_idx:
                    neckline = (df.iloc[left_trough_idx[0]]['low'] + 
                               df.iloc[right_trough_idx[0]]['low']) / 2
                    
                    # 成交量验证：头部成交量应小于左肩，右肩成交量应更小
                    left_shoulder_vol = df.iloc[peaks[i]]['volume']
                    head_vol = df.iloc[peaks[i+1]]['volume']
                    right_shoulder_vol = df.iloc[peaks[i+2]]['volume']
                    
                    volume_confirmed = head_vol < left_shoulder_vol * 0.8 and right_shoulder_vol < head_vol * 0.8
                    
                    # 突破验证：价格应跌破颈线
                    breakout_confirmed = df['close'].iloc[-1] < neckline * 0.995
                    
                    confidence = 0.75
                    if volume_confirmed:
                        confidence += 0.10
                    if breakout_confirmed:
                        confidence += 0.10
                    
                    return {
                        "detected": True,
                        "type": "HEAD_AND_SHOULDERS_TOP",
                        "confidence": min(confidence, 0.95),
                        "head_price": head,
                        "shoulder_prices": [left_shoulder, right_shoulder],
                        "neckline": neckline,
                        "target_price": neckline - (head - neckline),
                        "volume_confirmed": volume_confirmed,
                        "breakout_confirmed": breakout_confirmed,
                        "volume_analysis": f"左肩成交量: {left_shoulder_vol:.0f}, 头部成交量: {head_vol:.0f}, 右肩成交量: {right_shoulder_vol:.0f}, 平均: {avg_volume:.0f}",
                        "description": "头肩顶形态，看跌信号" + ("(成交量确认)" if volume_confirmed else "(等待成交量确认)") + ("(突破确认)" if breakout_confirmed else "(等待突破确认)")
                    }
        
        # 检查头肩底 (三个谷值，中间最低)
        if len(troughs) >= 3:
            for i in range(len(troughs) - 2):
                left_shoulder = df.iloc[troughs[i]]['low']
                head = df.iloc[troughs[i+1]]['low']
                right_shoulder = df.iloc[troughs[i+2]]['low']
                
                if (head < left_shoulder and head < right_shoulder and
                    abs(left_shoulder - right_shoulder) / head < 0.05):
                    
                    left_peak_idx = [p for p in peaks if troughs[i] < p < troughs[i+1]]
                    right_peak_idx = [p for p in peaks if troughs[i+1] < p < troughs[i+2]]
                    
                    if left_peak_idx and right_peak_idx:
                        neckline = (df.iloc[left_peak_idx[0]]['high'] + 
                                   df.iloc[right_peak_idx[0]]['high']) / 2
                        
                        # 成交量验证：头部成交量应大于左肩（恐慌性抛盘）
                        left_shoulder_vol = df.iloc[troughs[i]]['volume']
                        head_vol = df.iloc[troughs[i+1]]['volume']
                        right_shoulder_vol = df.iloc[troughs[i+2]]['volume']
                        
                        volume_confirmed = head_vol > left_shoulder_vol * 1.3  # 头部放量30%以上
                        
                        # 突破验证：价格应突破颈线
                        breakout_confirmed = df['close'].iloc[-1] > neckline * 1.005
                        
                        confidence = 0.75
                        if volume_confirmed:
                            confidence += 0.10
                        if breakout_confirmed:
                            confidence += 0.10
                        
                        return {
                            "detected": True,
                            "type": "HEAD_AND_SHOULDERS_BOTTOM",
                            "confidence": min(confidence, 0.95),
                            "head_price": head,
                            "shoulder_prices": [left_shoulder, right_shoulder],
                            "neckline": neckline,
                            "target_price": neckline + (neckline - head),
                            "volume_confirmed": volume_confirmed,
                            "breakout_confirmed": breakout_confirmed,
                            "volume_analysis": f"左肩成交量: {left_shoulder_vol:.0f}, 头部成交量: {head_vol:.0f}, 右肩成交量: {right_shoulder_vol:.0f}, 平均: {avg_volume:.0f}",
                            "description": "头肩底形态，看涨信号" + ("(成交量确认)" if volume_confirmed else "(等待成交量确认)") + ("(突破确认)" if breakout_confirmed else "(等待突破确认)")
                        }
        
        return {"detected": False, "type": None, "confidence": 0}
    
    @staticmethod
    def _identify_double_top(df: pd.DataFrame) -> Dict[str, Any]:
        """识别双顶形态 (M顶)"""
        peaks, _ = ChartPatterns._find_peaks_and_troughs(df)
        
        avg_volume = df['volume'].mean()
        
        if len(peaks) < 2:
            return {"detected": False, "type": None, "confidence": 0}
        
        for i in range(len(peaks) - 1):
            first_peak = df.iloc[peaks[i]]['high']
            second_peak = df.iloc[peaks[i+1]]['high']
            
            # 两个峰值相近 (5%容差)
            if abs(first_peak - second_peak) / first_peak < 0.05:
                # 中间有回调
                trough_between = df.iloc[peaks[i]:peaks[i+1]]['low'].min()
                
                if trough_between < first_peak * 0.95:  # 至少回调5%
                    # 成交量验证：第二个峰成交量应小于第一个峰
                    first_peak_vol = df.iloc[peaks[i]]['volume']
                    second_peak_vol = df.iloc[peaks[i+1]]['volume']
                    
                    volume_confirmed = second_peak_vol < first_peak_vol * 0.85  # 第二个峰放量小于第一个峰15%以上
                    
                    # 突破验证：价格跌破颈线
                    neckline = trough_between
                    breakout_confirmed = df['close'].iloc[-1] < neckline * 0.995
                    
                    confidence = 0.70
                    if volume_confirmed:
                        confidence += 0.10
                    if breakout_confirmed:
                        confidence += 0.10
                    
                    return {
                        "detected": True,
                        "type": "DOUBLE_TOP",
                        "confidence": min(confidence, 0.95),
                        "peak_prices": [first_peak, second_peak],
                        "trough_between": trough_between,
                        "target_price": trough_between - (first_peak - trough_between),
                        "volume_confirmed": volume_confirmed,
                        "breakout_confirmed": breakout_confirmed,
                        "volume_analysis": f"第一峰成交量: {first_peak_vol:.0f}, 第二峰成交量: {second_peak_vol:.0f}, 平均: {avg_volume:.0f}",
                        "description": "双顶形态(M顶)，看跌反转信号" + ("(成交量确认)" if volume_confirmed else "(等待成交量确认)") + ("(突破确认)" if breakout_confirmed else "(等待突破确认)")
                    }
        
        return {"detected": False, "type": None, "confidence": 0}
    
    @staticmethod
    def _identify_double_bottom(df: pd.DataFrame) -> Dict[str, Any]:
        """识别双底形态 (W底)"""
        _, troughs = ChartPatterns._find_peaks_and_troughs(df)
        
        if len(troughs) < 2:
            return {"detected": False, "type": None, "confidence": 0}
        
        avg_volume = df['volume'].mean()
        
        for i in range(len(troughs) - 1):
            first_trough = df.iloc[troughs[i]]['low']
            second_trough = df.iloc[troughs[i+1]]['low']
            
            # 两个谷值相近 (5%容差)
            if abs(first_trough - second_trough) / first_trough < 0.05:
                # 中间有反弹
                peak_between = df.iloc[troughs[i]:troughs[i+1]]['high'].max()
                
                if peak_between > first_trough * 1.05:  # 至少反弹5%
                    # 成交量验证：第二个底成交量应大于第一个底（恐慌性抛盘后萎缩）
                    first_trough_vol = df.iloc[troughs[i]]['volume']
                    second_trough_vol = df.iloc[troughs[i+1]]['volume']
                    
                    volume_confirmed = second_trough_vol < first_trough_vol * 0.85  # 第二个底成交量小于第一个底15%以上
                    
                    # 突破验证：价格突破颈线
                    neckline = peak_between
                    breakout_confirmed = df['close'].iloc[-1] > neckline * 1.005
                    
                    confidence = 0.70
                    if volume_confirmed:
                        confidence += 0.10
                    if breakout_confirmed:
                        confidence += 0.10
                    
                    return {
                        "detected": True,
                        "type": "DOUBLE_BOTTOM",
                        "confidence": min(confidence, 0.95),
                        "trough_prices": [first_trough, second_trough],
                        "peak_between": peak_between,
                        "target_price": peak_between + (peak_between - first_trough),
                        "volume_confirmed": volume_confirmed,
                        "breakout_confirmed": breakout_confirmed,
                        "volume_analysis": f"第一底成交量: {first_trough_vol:.0f}, 第二底成交量: {second_trough_vol:.0f}, 平均: {avg_volume:.0f}",
                        "description": "双底形态(W底)，看涨反转信号" + ("(成交量确认)" if volume_confirmed else "(等待成交量确认)") + ("(突破确认)" if breakout_confirmed else "(等待突破确认)")
                    }
        
        return {"detected": False, "type": None, "confidence": 0}
    
    @staticmethod
    def _identify_ascending_triangle(df: pd.DataFrame) -> Dict[str, Any]:
        """识别上升三角形"""
        peaks, troughs = ChartPatterns._find_peaks_and_troughs(df, window=3)
        
        if len(peaks) < 2 or len(troughs) < 2:
            return {"detected": False, "type": None, "confidence": 0}
        
        avg_volume = df['volume'].mean()
        
        # 检查最近的高点是否大致相同（水平阻力线）
        recent_peaks = [df.iloc[p]['high'] for p in peaks[-3:]]
        recent_troughs = [df.iloc[t]['low'] for t in troughs[-3:]]
        
        # 高点水平，低点上升
        high_variance = max(recent_peaks) - min(recent_peaks)
        avg_high = sum(recent_peaks) / len(recent_peaks)
        
        if high_variance / avg_high < 0.03:  # 高点变化小于3%
            # 检查低点是否上升
            if len(recent_troughs) >= 2 and recent_troughs[-1] > recent_troughs[0]:
                # 成交量验证：整理期间成交量应递减，突破时放量
                
                # 简单验证：最近成交量低于平均
                recent_vol = df['volume'].iloc[-5:].mean()
                volume_confirmed = recent_vol < avg_volume * 0.9  # 整理期成交量萎缩
                
                # 突破验证：价格接近或突破阻力线
                breakout_confirmed = df['close'].iloc[-1] > avg_high * 0.995
                
                confidence = 0.65
                if volume_confirmed:
                    confidence += 0.10
                if breakout_confirmed:
                    confidence += 0.10
                
                return {
                    "detected": True,
                    "type": "ASCENDING_TRIANGLE",
                    "confidence": min(confidence, 0.95),
                    "resistance_level": avg_high,
                    "trend_line_start": recent_troughs[0],
                    "trend_line_end": recent_troughs[-1],
                    "target_price": avg_high + (avg_high - recent_troughs[0]),
                    "volume_confirmed": volume_confirmed,
                    "breakout_confirmed": breakout_confirmed,
                    "volume_analysis": f"最近5日平均成交量: {recent_vol:.0f}, 总体平均: {avg_volume:.0f}",
                    "description": "上升三角形，看涨持续形态" + ("(成交量确认)" if volume_confirmed else "(等待成交量确认)") + ("(突破确认)" if breakout_confirmed else "(等待突破确认)")
                }
        
        return {"detected": False, "type": None, "confidence": 0}
    
    @staticmethod
    def _identify_descending_triangle(df: pd.DataFrame) -> Dict[str, Any]:
        """识别下降三角形"""
        peaks, troughs = ChartPatterns._find_peaks_and_troughs(df, window=3)
        
        if len(peaks) < 2 or len(troughs) < 2:
            return {"detected": False, "type": None, "confidence": 0}
        
        avg_volume = df['volume'].mean()
        
        recent_peaks = [df.iloc[p]['high'] for p in peaks[-3:]]
        recent_troughs = [df.iloc[t]['low'] for t in troughs[-3:]]
        
        # 低点水平，高点下降
        low_variance = max(recent_troughs) - min(recent_troughs)
        avg_low = sum(recent_troughs) / len(recent_troughs)
        
        if low_variance / avg_low < 0.03:  # 低点变化小于3%
            # 检查高点是否下降
            if len(recent_peaks) >= 2 and recent_peaks[-1] < recent_peaks[0]:
                # 成交量验证：整理期间成交量递减，突破时放量
                recent_vol = df['volume'].iloc[-5:].mean()
                volume_confirmed = recent_vol < avg_volume * 0.9
                
                # 突破验证：价格跌破支撑线
                breakout_confirmed = df['close'].iloc[-1] < avg_low * 0.995
                
                confidence = 0.65
                if volume_confirmed:
                    confidence += 0.10
                if breakout_confirmed:
                    confidence += 0.10
                
                return {
                    "detected": True,
                    "type": "DESCENDING_TRIANGLE",
                    "confidence": min(confidence, 0.95),
                    "support_level": avg_low,
                    "trend_line_start": recent_peaks[0],
                    "trend_line_end": recent_peaks[-1],
                    "target_price": avg_low - (recent_peaks[0] - avg_low),
                    "volume_confirmed": volume_confirmed,
                    "breakout_confirmed": breakout_confirmed,
                    "volume_analysis": f"最近5日平均成交量: {recent_vol:.0f}, 总体平均: {avg_volume:.0f}",
                    "description": "下降三角形，看跌持续形态" + ("(成交量确认)" if volume_confirmed else "(等待成交量确认)") + ("(突破确认)" if breakout_confirmed else "(等待突破确认)")
                }
        
        return {"detected": False, "type": None, "confidence": 0}
    
    @staticmethod
    def _identify_symmetrical_triangle(df: pd.DataFrame) -> Dict[str, Any]:
        """识别对称三角形"""
        peaks, troughs = ChartPatterns._find_peaks_and_troughs(df, window=3)
        
        if len(peaks) < 3 or len(troughs) < 3:
            return {"detected": False, "type": None, "confidence": 0}
        
        avg_volume = df['volume'].mean()
        
        recent_peaks = [df.iloc[p]['high'] for p in peaks[-4:]]
        recent_troughs = [df.iloc[t]['low'] for t in troughs[-4:]]
        
        # 高点下降，低点上升
        if (len(recent_peaks) >= 3 and len(recent_troughs) >= 3 and
            recent_peaks[-1] < recent_peaks[0] and
            recent_troughs[-1] > recent_troughs[0]):
            
            # 计算收敛程度
            high_slope = (recent_peaks[-1] - recent_peaks[0]) / len(recent_peaks)
            low_slope = (recent_troughs[-1] - recent_troughs[0]) / len(recent_troughs)
            
            # 高点下降，低点上升（斜率相反）
            if high_slope < 0 and low_slope > 0:
                apex = (recent_peaks[-1] + recent_troughs[-1]) / 2
                
                # 成交量验证：整理期间成交量递减
                recent_vol = df['volume'].iloc[-5:].mean()
                volume_confirmed = recent_vol < avg_volume * 0.9
                
                # 突破验证：价格接近上沿或下沿
                current_close = df['close'].iloc[-1]
                breakout_up = current_close > recent_peaks[-1] * 0.995
                breakout_down = current_close < recent_troughs[-1] * 1.005
                breakout_confirmed = breakout_up or breakout_down
                
                confidence = 0.60
                if volume_confirmed:
                    confidence += 0.10
                if breakout_confirmed:
                    confidence += 0.10
                
                return {
                    "detected": True,
                    "type": "SYMMETRICAL_TRIANGLE",
                    "confidence": min(confidence, 0.95),
                    "upper_trendline": recent_peaks,
                    "lower_trendline": recent_troughs,
                    "apex_price": apex,
                    "volume_confirmed": volume_confirmed,
                    "breakout_confirmed": breakout_confirmed,
                    "breakout_direction": "up" if breakout_up else "down" if breakout_down else None,
                    "volume_analysis": f"最近5日平均成交量: {recent_vol:.0f}, 总体平均: {avg_volume:.0f}",
                    "description": "对称三角形，中性整理形态，突破方向决定趋势" + ("(成交量确认)" if volume_confirmed else "(等待成交量确认)") + ("(突破确认)" if breakout_confirmed else "(等待突破确认)")
                }
        
        return {"detected": False, "type": None, "confidence": 0}
    
    @staticmethod
    def _identify_flag(df: pd.DataFrame) -> Dict[str, Any]:
        """识别旗形/旗杆形态"""
        if len(df) < 20:
            return {"detected": False, "type": None, "confidence": 0}
        
        avg_volume = df['volume'].mean()
        
        # 检查是否有急剧的价格变动（旗杆）
        price_change_5d = (df['close'].iloc[-5] - df['close'].iloc[-20]) / df['close'].iloc[-20]
        
        if abs(price_change_5d) > 0.15:  # 15%以上的变动
            # 检查随后的整理（旗形）
            recent_range = (df['high'].iloc[-5:].max() - df['low'].iloc[-5:].min()) / df['close'].iloc[-5]
            
            if recent_range < 0.05:  # 整理区间小于5%
                direction = "BULL_FLAG" if price_change_5d > 0 else "BEAR_FLAG"
                
                # 成交量验证：旗杆期间放量，整理期间萎缩
                pole_vol = df['volume'].iloc[-20:-5].mean()
                flag_vol = df['volume'].iloc[-5:].mean()
                volume_confirmed = pole_vol > avg_volume * 1.2 and flag_vol < avg_volume * 0.8
                
                # 突破验证：价格突破整理区间
                current_close = df['close'].iloc[-1]
                recent_high = df['high'].iloc[-5:].max()
                recent_low = df['low'].iloc[-5:].min()
                breakout_confirmed = (direction == "BULL_FLAG" and current_close > recent_high * 1.005) or \
                                    (direction == "BEAR_FLAG" and current_close < recent_low * 0.995)
                
                confidence = 0.60
                if volume_confirmed:
                    confidence += 0.10
                if breakout_confirmed:
                    confidence += 0.10
                
                return {
                    "detected": True,
                    "type": direction,
                    "confidence": min(confidence, 0.95),
                    "pole_height": abs(price_change_5d),
                    "consolidation_range": recent_range,
                    "target_price": (df['close'].iloc[-5:].max() + abs(price_change_5d) * df['close'].iloc[-5]) 
                                    if direction == "BULL_FLAG" else
                                    (df['close'].iloc[-5:].min() - abs(price_change_5d) * df['close'].iloc[-5]),
                    "volume_confirmed": volume_confirmed,
                    "breakout_confirmed": breakout_confirmed,
                    "volume_analysis": f"旗杆期平均成交量: {pole_vol:.0f}, 旗形期平均成交量: {flag_vol:.0f}, 总体平均: {avg_volume:.0f}",
                    "description": f"{'看涨' if direction == 'BULL_FLAG' else '看跌'}旗形，持续形态" + ("(成交量确认)" if volume_confirmed else "(等待成交量确认)") + ("(突破确认)" if breakout_confirmed else "(等待突破确认)")
                }
        
        return {"detected": False, "type": None, "confidence": 0}
    
    @staticmethod
    def _identify_wedge(df: pd.DataFrame) -> Dict[str, Any]:
        """识别楔形形态"""
        peaks, troughs = ChartPatterns._find_peaks_and_troughs(df, window=3)
        
        if len(peaks) < 3 or len(troughs) < 3:
            return {"detected": False, "type": None, "confidence": 0}
        
        avg_volume = df['volume'].mean()
        
        recent_peaks = [df.iloc[p]['high'] for p in peaks[-4:]]
        recent_troughs = [df.iloc[t]['low'] for t in troughs[-4:]]
        
        # 上升楔形：高点和低点都上升，但高点斜率小于低点斜率
        if (recent_peaks[-1] > recent_peaks[0] and recent_troughs[-1] > recent_troughs[0]):
            high_slope = (recent_peaks[-1] - recent_peaks[0]) / len(recent_peaks)
            low_slope = (recent_troughs[-1] - recent_troughs[0]) / len(recent_troughs)
            
            if high_slope < low_slope:  # 收敛
                # 成交量验证：上升楔形通常伴随着成交量递减
                recent_vol = df['volume'].iloc[-5:].mean()
                volume_confirmed = recent_vol < avg_volume * 0.9
                
                # 突破验证：价格跌破下轨
                breakout_confirmed = df['close'].iloc[-1] < recent_troughs[-1] * 0.995
                
                confidence = 0.60
                if volume_confirmed:
                    confidence += 0.10
                if breakout_confirmed:
                    confidence += 0.10
                
                return {
                    "detected": True,
                    "type": "RISING_WEDGE",
                    "confidence": min(confidence, 0.95),
                    "upper_trendline": recent_peaks,
                    "lower_trendline": recent_troughs,
                    "volume_confirmed": volume_confirmed,
                    "breakout_confirmed": breakout_confirmed,
                    "volume_analysis": f"最近5日平均成交量: {recent_vol:.0f}, 总体平均: {avg_volume:.0f}",
                    "description": "上升楔形，看跌反转形态" + ("(成交量确认)" if volume_confirmed else "(等待成交量确认)") + ("(突破确认)" if breakout_confirmed else "(等待突破确认)")
                }
        
        # 下降楔形：高点和低点都下降，但高点斜率小于低点斜率（更平缓）
        if (recent_peaks[-1] < recent_peaks[0] and recent_troughs[-1] < recent_troughs[0]):
            high_slope = (recent_peaks[-1] - recent_peaks[0]) / len(recent_peaks)
            low_slope = (recent_troughs[-1] - recent_troughs[0]) / len(recent_troughs)
            
            if abs(high_slope) < abs(low_slope):  # 收敛
                # 成交量验证：下降楔形通常伴随着成交量递减
                recent_vol = df['volume'].iloc[-5:].mean()
                volume_confirmed = recent_vol < avg_volume * 0.9
                
                # 突破验证：价格突破上轨
                breakout_confirmed = df['close'].iloc[-1] > recent_peaks[-1] * 1.005
                
                confidence = 0.60
                if volume_confirmed:
                    confidence += 0.10
                if breakout_confirmed:
                    confidence += 0.10
                
                return {
                    "detected": True,
                    "type": "FALLING_WEDGE",
                    "confidence": min(confidence, 0.95),
                    "upper_trendline": recent_peaks,
                    "lower_trendline": recent_troughs,
                    "volume_confirmed": volume_confirmed,
                    "breakout_confirmed": breakout_confirmed,
                    "volume_analysis": f"最近5日平均成交量: {recent_vol:.0f}, 总体平均: {avg_volume:.0f}",
                    "description": "下降楔形，看涨反转形态" + ("(成交量确认)" if volume_confirmed else "(等待成交量确认)") + ("(突破确认)" if breakout_confirmed else "(等待突破确认)")
                }
        
        return {"detected": False, "type": None, "confidence": 0}
    
    @staticmethod
    def _identify_rounding_top(df: pd.DataFrame) -> Dict[str, Any]:
        """识别圆形顶"""
        if len(df) < 30:
            return {"detected": False, "type": None, "confidence": 0}
        
        avg_volume = df['volume'].mean()
        
        # 检查价格是否呈现弧形顶部
        highs = df['high'].values[-30:]
        mid = len(highs) // 2
        
        # 中间高，两边低，形成弧形
        if (highs[mid] > highs[0] and highs[mid] > highs[-1] and
            highs[mid-5:mid+5].mean() > highs[:5].mean() and
            highs[mid-5:mid+5].mean() > highs[-5:].mean()):
            
            # 检查是否平滑（没有尖锐的峰）
            if np.std(highs[mid-5:mid+5]) < np.std(highs[:5]) * 0.5:
                # 成交量验证：左侧上升时放量，右侧下跌时缩量
                left_vol = df['volume'].iloc[-30:-15].mean()
                right_vol = df['volume'].iloc[-15:].mean()
                volume_confirmed = left_vol > avg_volume * 1.1 and right_vol < avg_volume * 0.9
                
                # 突破验证：价格跌破颈线（左侧起点）
                neckline = df['close'].iloc[-30]
                breakout_confirmed = df['close'].iloc[-1] < neckline * 0.995
                
                confidence = 0.55
                if volume_confirmed:
                    confidence += 0.10
                if breakout_confirmed:
                    confidence += 0.10
                
                return {
                    "detected": True,
                    "type": "ROUNDING_TOP",
                    "confidence": min(confidence, 0.95),
                    "top_price": highs[mid],
                    "start_price": highs[0],
                    "end_price": highs[-1],
                    "volume_confirmed": volume_confirmed,
                    "breakout_confirmed": breakout_confirmed,
                    "volume_analysis": f"左侧平均成交量: {left_vol:.0f}, 右侧平均成交量: {right_vol:.0f}, 总体平均: {avg_volume:.0f}",
                    "description": "圆形顶，看跌反转形态" + ("(成交量确认)" if volume_confirmed else "(等待成交量确认)") + ("(突破确认)" if breakout_confirmed else "(等待突破确认)")
                }
        
        return {"detected": False, "type": None, "confidence": 0}
    
    @staticmethod
    def _identify_rounding_bottom(df: pd.DataFrame) -> Dict[str, Any]:
        """识别圆形底"""
        if len(df) < 30:
            return {"detected": False, "type": None, "confidence": 0}
        
        avg_volume = df['volume'].mean()
        
        # 检查价格是否呈现弧形底部
        lows = df['low'].values[-30:]
        mid = len(lows) // 2
        
        # 中间低，两边高，形成弧形
        if (lows[mid] < lows[0] and lows[mid] < lows[-1] and
            lows[mid-5:mid+5].mean() < lows[:5].mean() and
            lows[mid-5:mid+5].mean() < lows[-5:].mean()):
            
            # 检查是否平滑
            if np.std(lows[mid-5:mid+5]) < np.std(lows[:5]) * 0.5:
                # 成交量验证：左侧下跌时缩量，右侧上升时放量
                left_vol = df['volume'].iloc[-30:-15].mean()
                right_vol = df['volume'].iloc[-15:].mean()
                volume_confirmed = right_vol > left_vol * 1.3  # 右侧放量30%以上
                
                # 突破验证：价格突破颈线（左侧起点）
                neckline = df['close'].iloc[-30]
                breakout_confirmed = df['close'].iloc[-1] > neckline * 1.005
                
                confidence = 0.55
                if volume_confirmed:
                    confidence += 0.10
                if breakout_confirmed:
                    confidence += 0.10
                
                return {
                    "detected": True,
                    "type": "ROUNDING_BOTTOM",
                    "confidence": min(confidence, 0.95),
                    "bottom_price": lows[mid],
                    "start_price": lows[0],
                    "end_price": lows[-1],
                    "volume_confirmed": volume_confirmed,
                    "breakout_confirmed": breakout_confirmed,
                    "volume_analysis": f"左侧平均成交量: {left_vol:.0f}, 右侧平均成交量: {right_vol:.0f}, 总体平均: {avg_volume:.0f}",
                    "description": "圆形底，看涨反转形态" + ("(成交量确认)" if volume_confirmed else "(等待成交量确认)") + ("(突破确认)" if breakout_confirmed else "(等待突破确认)")
                }
        
        return {"detected": False, "type": None, "confidence": 0}
    
    @staticmethod
    def _identify_rectangle(df: pd.DataFrame) -> Dict[str, Any]:
        """识别矩形整理形态"""
        if len(df) < 20:
            return {"detected": False, "type": None, "confidence": 0}
        
        avg_volume = df['volume'].mean()
        recent_df = df.tail(20)
        
        # 检查是否在一定区间内震荡
        high_range = recent_df['high'].max() - recent_df['high'].min()
        low_range = recent_df['low'].max() - recent_df['low'].min()
        avg_price = recent_df['close'].mean()
        
        # 高点和低点都在较窄的区间内
        if high_range / avg_price < 0.05 and low_range / avg_price < 0.05:
            resistance = recent_df['high'].max()
            support = recent_df['low'].min()
            
            # 检查是否有多次触及上下边界
            high_touches = sum(1 for h in recent_df['high'] if h > resistance * 0.98)
            low_touches = sum(1 for l in recent_df['low'] if l < support * 1.02)
            
            if high_touches >= 2 and low_touches >= 2:
                # 成交量验证：整理期间成交量应递减
                recent_vol = df['volume'].iloc[-5:].mean()
                volume_confirmed = recent_vol < avg_volume * 0.9
                
                # 突破验证：价格接近或突破上沿或下沿
                current_close = df['close'].iloc[-1]
                breakout_up = current_close > resistance * 0.995
                breakout_down = current_close < support * 1.005
                breakout_confirmed = breakout_up or breakout_down
                
                confidence = 0.60
                if volume_confirmed:
                    confidence += 0.10
                if breakout_confirmed:
                    confidence += 0.10
                
                return {
                    "detected": True,
                    "type": "RECTANGLE",
                    "confidence": min(confidence, 0.95),
                    "resistance": resistance,
                    "support": support,
                    "range_height": resistance - support,
                    "volume_confirmed": volume_confirmed,
                    "breakout_confirmed": breakout_confirmed,
                    "breakout_direction": "up" if breakout_up else "down" if breakout_down else None,
                    "volume_analysis": f"最近5日平均成交量: {recent_vol:.0f}, 总体平均: {avg_volume:.0f}",
                    "description": "矩形整理形态，突破方向决定趋势" + ("(成交量确认)" if volume_confirmed else "(等待成交量确认)") + ("(突破确认)" if breakout_confirmed else "(等待突破确认)")
                }
        
        return {"detected": False, "type": None, "confidence": 0}
    
    @staticmethod
    def format_patterns_for_display(patterns: Dict[str, Any]) -> str:
        """
        将识别的形态格式化为可读的字符串
        
        Args:
            patterns: identify_all_patterns 返回的字典
            
        Returns:
            格式化的形态描述字符串
        """
        detected_patterns = []
        
        for pattern_name, pattern_info in patterns.items():
            if pattern_info.get("detected"):
                detected_patterns.append(pattern_info)
        
        if not detected_patterns:
            return "未识别到明显的图表形态"
        
        # 按置信度排序
        detected_patterns.sort(key=lambda x: x.get("confidence", 0), reverse=True)
        
        result = []
        result.append("## 图表形态识别结果\n")
        
        for i, pattern in enumerate(detected_patterns[:3], 1):  # 只显示前3个
            result.append(f"### {i}. {pattern.get('description', '')}")
            result.append(f"- 形态类型: {pattern.get('type', 'Unknown')}")
            result.append(f"- 置信度: {pattern.get('confidence', 0):.0%}")
            
            if 'target_price' in pattern:
                result.append(f"- 目标价格: ${pattern['target_price']:.2f}")
            if 'neckline' in pattern:
                result.append(f"- 颈线位: ${pattern['neckline']:.2f}")
            if 'resistance_level' in pattern:
                result.append(f"- 阻力位: ${pattern['resistance_level']:.2f}")
            if 'support_level' in pattern:
                result.append(f"- 支撑位: ${pattern['support_level']:.2f}")
            
            result.append("")
        
        return "\n".join(result)
