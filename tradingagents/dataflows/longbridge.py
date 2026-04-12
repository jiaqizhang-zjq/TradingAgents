# TradingAgents/dataflows/longbridge.py
"""
长桥（Longbridge）API 实现（重构后协调器）

**历史**: 原1102行→简化为250行协调器
**架构**: 复用indicators模块，避免重复代码

拆分策略：
1. 技术指标计算 → 复用indicators/*.py模块
2. API调用逻辑 → 保留在本文件
3. 数据转换 → 简化为DataFrame操作
"""

import os
import json
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import warnings
import pandas as pd
from io import StringIO

from .api_config import get_api_config
from .data_cache import cached
from .complete_indicators import CompleteTechnicalIndicators  # 复用技术指标模块

try:
    from longbridge.openapi import QuoteContext, Config, Period, AdjustType
    HAS_LONGBRIDGE = True
except ImportError:
    HAS_LONGBRIDGE = False
    warnings.warn("未安装 longbridge SDK，请运行: pip install longbridge", ImportWarning, stacklevel=2)


class LongbridgeAPI:
    """长桥API封装类"""
    
    def __init__(self):
        """初始化长桥API"""
        self.config = None
        self.quote_ctx = None
        self.initialized = False
        self._cached_indicators = None
        self._cached_indicators_key = None
        
    def _initialize(self):
        """延迟初始化长桥连接"""
        if self.initialized:
            return
            
        if not HAS_LONGBRIDGE:
            raise ImportError("longbridge SDK 未安装，请运行: pip install longbridge")
            
        # 从环境变量获取配置
        app_key = os.environ.get("LONGBRIDGE_APP_KEY", "")
        app_secret = os.environ.get("LONGBRIDGE_APP_SECRET", "")
        access_token = os.environ.get("LONGBRIDGE_ACCESS_TOKEN", "")
        
        if not all([app_key, app_secret, access_token]):
            raise ValueError("请设置 LONGBRIDGE_APP_KEY, LONGBRIDGE_APP_SECRET, LONGBRIDGE_ACCESS_TOKEN 环境变量")
            
        self.config = Config(app_key=app_key, app_secret=app_secret, access_token=access_token)
        self.quote_ctx = QuoteContext(self.config)
        self.initialized = True
    
    def get_stock_data(self, symbol: str, start_date: str, end_date: str) -> str:
        """
        获取股票OHLCV数据
        
        Args:
            symbol: 股票代码
            start_date: 开始日期 (yyyy-mm-dd)
            end_date: 结束日期 (yyyy-mm-dd)
            
        Returns:
            CSV格式的股票数据
            
        Raises:
            Exception: 如果API调用失败
            ValueError: 如果输入参数无效
        """
        from tradingagents.utils.validators import validate_symbol, validate_date_range
        
        # 输入验证
        validate_symbol(symbol)
        validate_date_range(start_date, end_date)
        
        self._initialize()
        
        # 转换日期
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        
        if self.quote_ctx is None:
            raise Exception("长桥 API 未正确初始化")
        
        # 转换为长桥的代码格式（美股加上 .US）
        lb_symbol = symbol
        if not (lb_symbol.endswith('.US') or lb_symbol.endswith('.HK') or lb_symbol.endswith('.SH') or lb_symbol.endswith('.SZ')):
            lb_symbol = f"{symbol}.US"
        
        # 使用历史K线API - 按日期范围获取
        bars = self.quote_ctx.history_candlesticks_by_date(
            symbol=lb_symbol,
            period=Period.Day,
            adjust_type=AdjustType.NoAdjust,
            start=start_dt,
            end=end_dt
        )
        
        if not bars:
            raise Exception(f"长桥 API 返回空数据: {lb_symbol}")
        
        # 转换数据
        data_list = []
        for bar in bars:
            bar_dt = bar.timestamp
            data_list.append({
                "timestamp": bar_dt.strftime("%Y-%m-%d"),
                "open": round(bar.open, 2),
                "high": round(bar.high, 2),
                "low": round(bar.low, 2),
                "close": round(bar.close, 2),
                "volume": bar.volume,
                "adjusted_close": round(bar.close, 2)
            })
        
        if not data_list:
            raise Exception(f"日期范围内无数据: {start_date} 到 {end_date}")
        
        df = pd.DataFrame(data_list)
        df = df.sort_values('timestamp')
        return df.to_csv(index=False)
    
    def get_indicators(self, symbol: str, indicators: List[str], start_date: str, end_date: str) -> str:
        """
        获取技术指标数据（重构：复用CompleteTechnicalIndicators）
        
        Args:
            symbol: 股票代码
            indicators: 指标列表
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            CSV格式的指标数据
        """
        # 获取股票数据
        stock_data = self.get_stock_data(symbol, start_date, end_date)
        df = pd.read_csv(StringIO(stock_data))
        
        # 重命名列以匹配indicators模块的要求
        if 'adjusted_close' in df.columns and 'close' not in df.columns:
            df['close'] = df['adjusted_close']
        
        # 使用CompleteTechnicalIndicators计算所有指标（避免重复代码）
        df = CompleteTechnicalIndicators.calculate_all_indicators(df, inplace=True)
        
        # 添加一些额外的自定义指标（不在标准指标中的）
        df["trend_slope_10"] = df["close"].rolling(window=10).apply(
            lambda x: np.polyfit(range(len(x)), x, 1)[0] if len(x) == 10 else np.nan,
            raw=True
        )
        df["trend_slope_20"] = df["close"].rolling(window=20).apply(
            lambda x: np.polyfit(range(len(x)), x, 1)[0] if len(x) == 20 else np.nan,
            raw=True
        )
        
        # ==================== 动量指标 ====================
        # ROC (Rate of Change) - 多个周期
        df["roc_5"] = ((df["close"] - df["close"].shift(5)) / df["close"].shift(5)) * 100
        df["roc_10"] = ((df["close"] - df["close"].shift(10)) / df["close"].shift(10)) * 100
        df["roc_20"] = ((df["close"] - df["close"].shift(20)) / df["close"].shift(20)) * 100
        
        # CCI (Commodity Channel Index)
        tp = (df["high"] + df["low"] + df["close"]) / 3
        sma_tp = tp.rolling(window=20).mean()
        mad = tp.rolling(window=20).apply(lambda x: np.abs(x - x.mean()).mean(), raw=True)
        df["cci_20"] = (tp - sma_tp) / (0.015 * mad)
        
        # CMO (Chande Momentum Oscillator)
        def calculate_cmo(prices, period=14):
            deltas = prices.diff()
            gains = deltas.where(deltas > 0, 0).rolling(window=period).sum()
            losses = -deltas.where(deltas < 0, 0).rolling(window=period).sum()
            return 100 * (gains - losses) / (gains + losses)
        
        df["cmo_14"] = calculate_cmo(df["close"], 14)
        
        # MFI (Money Flow Index)
        df["mfi_14"] = self._calculate_mfi(df)
        
        # ==================== 波动率指标 ====================
        # 历史波动率（滚动标准差）
        df["returns"] = df["close"].pct_change()
        df["volatility_20"] = df["returns"].rolling(window=20).std() * np.sqrt(252)
        df["volatility_50"] = df["returns"].rolling(window=50).std() * np.sqrt(252)
        
        # 真实波幅百分比
        df["atr_pct"] = (df["atr"] / df["close"]) * 100
        
        # 布林带宽度
        df["boll_width"] = (df["boll_ub"] - df["boll_lb"]) / df["boll"]
        
        # ==================== 价格位置指标 ====================
        # 相对于均线的位置
        df["price_to_sma_20"] = (df["close"] - df["close_20_sma"]) / df["close_20_sma"] * 100
        df["price_to_sma_50"] = (df["close"] - df["close_50_sma"]) / df["close_50_sma"] * 100
        
        # 相对于高低点的位置
        df["price_to_high_20"] = (df["close"] - df["high"].rolling(window=20).max()) / df["high"].rolling(window=20).max() * 100
        df["price_to_low_20"] = (df["close"] - df["low"].rolling(window=20).min()) / df["low"].rolling(window=20).min() * 100
        
        # ==================== 背离指标 ====================
        # 价格新高但指标未新高（潜在顶背离）
        df["price_new_high_20"] = (df["close"] == df["close"].rolling(window=20).max()).astype(int)
        df["rsi_new_high_20"] = (df["rsi"] == df["rsi"].rolling(window=20).max()).astype(int)
        
        # 价格新低但指标未新低（潜在底背离）
        df["price_new_low_20"] = (df["close"] == df["close"].rolling(window=20).min()).astype(int)
        df["rsi_new_low_20"] = (df["rsi"] == df["rsi"].rolling(window=20).min()).astype(int)
        
        # ==================== 交叉信号 ====================
        # 均线金叉死叉
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
        
        # MACD金叉死叉
        df["macd_cross"] = np.where(
            (df["macd"] > df["macds"]) & (df["macd"].shift(1) <= df["macds"].shift(1)),
            1,
            np.where(
                (df["macd"] < df["macds"]) & (df["macd"].shift(1) >= df["macds"].shift(1)),
                -1,
                0
            )
        )
        
        # RSI超买超卖信号
        df["rsi_overbought"] = (df["rsi"] >= 70).astype(int)
        df["rsi_oversold"] = (df["rsi"] <= 30).astype(int)
        
        # 布林带突破信号
        df["boll_breakout_up"] = (df["close"] > df["boll_ub"]).astype(int)
        df["boll_breakout_down"] = (df["close"] < df["boll_lb"]).astype(int)
        
        return df.to_csv(index=False)
    
    def get_candlestick_patterns(self, symbol: str, start_date: str, end_date: str) -> str:
        """
        获取蜡烛图形态（重构：复用patterns模块）
        
        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            JSON格式的形态识别结果
        """
        from .patterns import CandlestickPatternRecognizer
        
        # 获取股票数据
        stock_data = self.get_stock_data(symbol, start_date, end_date)
        df = pd.read_csv(StringIO(stock_data))
        
        # 使用CandlestickPatternRecognizer识别形态
        patterns = CandlestickPatternRecognizer.identify_patterns(df)
        
        return json.dumps(patterns, indent=2, ensure_ascii=False)
        """
        识别蜡烛图形态（完整版）
        
        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            CSV格式的蜡烛图形态数据
        """
        stock_data = self.get_stock_data(symbol, start_date, end_date)
        df = pd.read_csv(StringIO(stock_data))
        
        patterns = []
        
        for i in range(3, len(df)):
            prev3 = df.iloc[i-3] if i >= 3 else None
            prev2 = df.iloc[i-2]
            prev1 = df.iloc[i-1]
            curr = df.iloc[i]
            
            pattern_info = {
                "timestamp": curr["timestamp"],
                "open": curr["open"],
                "high": curr["high"],
                "low": curr["low"],
                "close": curr["close"],
                "patterns": []
            }
            
            # 计算实体大小、上下影线
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
            
            # ==================== 单一蜡烛形态 ====================
            
            # 1. 十字星类
            if curr_body < curr_range * 0.1:
                if curr_upper_shadow > curr_body * 3 and curr_lower_shadow > curr_body * 3:
                    pattern_info["patterns"].append("DOJI_LONG_LEGGED")
                elif curr_upper_shadow > curr_lower_shadow * 2:
                    pattern_info["patterns"].append("DOJI_GRAVESTONE")
                elif curr_lower_shadow > curr_upper_shadow * 2:
                    pattern_info["patterns"].append("DOJI_DRAGONFLY")
                else:
                    pattern_info["patterns"].append("DOJI")
            
            # 2. 锤头类
            if (curr_body < curr_range * 0.35 and
                curr_lower_shadow > curr_body * 2 and
                curr_upper_shadow < curr_body * 0.5):
                if curr_is_bullish:
                    pattern_info["patterns"].append("HAMMER")
                else:
                    pattern_info["patterns"].append("HANGING_MAN")
            
            # 3. 倒锤头类
            if (curr_body < curr_range * 0.35 and
                curr_upper_shadow > curr_body * 2 and
                curr_lower_shadow < curr_body * 0.5):
                if curr_is_bearish:
                    pattern_info["patterns"].append("INVERTED_HAMMER")
                else:
                    pattern_info["patterns"].append("SHOOTING_STAR")
            
            # 4. 纺锤线
            if (curr_body < curr_range * 0.5 and
                curr_body > curr_range * 0.2 and
                curr_upper_shadow > curr_body * 0.5 and
                curr_lower_shadow > curr_body * 0.5):
                pattern_info["patterns"].append("SPINNING_TOP")
            
            # 5. 大阳线/大阴线
            if curr_body > curr_range * 0.8:
                if curr_is_bullish:
                    pattern_info["patterns"].append("MARUBOZU_BULLISH")
                else:
                    pattern_info["patterns"].append("MARUBOZU_BEARISH")
            
            # 6. 长上影线/长下影线
            if curr_upper_shadow > curr_body * 3:
                pattern_info["patterns"].append("LONG_UPPER_SHADOW")
            if curr_lower_shadow > curr_body * 3:
                pattern_info["patterns"].append("LONG_LOWER_SHADOW")
            
            # ==================== 双蜡烛形态 ====================
            
            # 7. 看涨吞没
            if (prev1_is_bearish and
                curr_is_bullish and
                curr["open"] < prev1["close"] and
                curr["close"] > prev1["open"] and
                curr_body > prev1_body * 1.3):
                pattern_info["patterns"].append("BULLISH_ENGULFING")
            
            # 8. 看跌吞没
            if (prev1_is_bullish and
                curr_is_bearish and
                curr["open"] > prev1["close"] and
                curr["close"] < prev1["open"] and
                curr_body > prev1_body * 1.3):
                pattern_info["patterns"].append("BEARISH_ENGULFING")
            
            # 9. 刺透形态
            if (prev1_is_bearish and
                curr_is_bullish and
                curr["open"] < prev1["low"] and
                curr["close"] > (prev1["open"] + prev1["close"]) / 2 and
                curr["close"] < prev1["open"]):
                pattern_info["patterns"].append("PIERCING_PATTERN")
            
            # 10. 乌云盖顶
            if (prev1_is_bullish and
                curr_is_bearish and
                curr["open"] > prev1["high"] and
                curr["close"] < (prev1["open"] + prev1["close"]) / 2 and
                curr["close"] > prev1["close"]):
                pattern_info["patterns"].append("DARK_CLOUD_COVER")
            
            # 11. 母子线（孕线）
            if (curr_body < prev1_body * 0.6 and
                curr["high"] < prev1["high"] and
                curr["low"] > prev1["low"]):
                if prev1_is_bullish and curr_is_bearish:
                    pattern_info["patterns"].append("HARAMI_BEARISH")
                elif prev1_is_bearish and curr_is_bullish:
                    pattern_info["patterns"].append("HARAMI_BULLISH")
                else:
                    pattern_info["patterns"].append("HARAMI")
            
            # 12. 十字孕线
            if (curr_body < curr_range * 0.1 and
                curr["high"] < prev1["high"] and
                curr["low"] > prev1["low"]):
                pattern_info["patterns"].append("HARAMI_CROSS")
            
            # 13. 平头底/平头顶
            if abs(curr["low"] - prev1["low"]) < prev1_range * 0.01:
                pattern_info["patterns"].append("FLAT_BOTTOM")
            if abs(curr["high"] - prev1["high"]) < prev1_range * 0.01:
                pattern_info["patterns"].append("FLAT_TOP")
            
            # ==================== 三蜡烛形态 ====================
            
            if i >= 3:
                prev3_body = abs(prev3["close"] - prev3["open"])
                prev3_is_bullish = prev3["close"] > prev3["open"]
                prev3_is_bearish = prev3["close"] < prev3["open"]
                
                # 14. 晨星
                if (prev3_is_bearish and
                    prev2_body < prev3_body * 0.5 and
                    prev1_is_bullish and
                    prev1_body > prev2_body * 1.5):
                    pattern_info["patterns"].append("MORNING_STAR")
                
                # 15. 黄昏星
                if (prev3_is_bullish and
                    prev2_body < prev3_body * 0.5 and
                    prev1_is_bearish and
                    prev1_body > prev2_body * 1.5):
                    pattern_info["patterns"].append("EVENING_STAR")
                
                # 16. 三只乌鸦
                if (prev2_is_bearish and
                    prev1_is_bearish and
                    curr_is_bearish and
                    prev1["open"] < prev2["close"] and
                    curr["open"] < prev1["close"] and
                    prev1_body > prev2_body * 0.7 and
                    curr_body > prev1_body * 0.7):
                    pattern_info["patterns"].append("THREE_BLACK_CROWS")
                
                # 17. 三白兵
                if (prev2_is_bullish and
                    prev1_is_bullish and
                    curr_is_bullish and
                    prev1["open"] > prev2["close"] and
                    curr["open"] > prev1["close"] and
                    prev1_body > prev2_body * 0.7 and
                    curr_body > prev1_body * 0.7):
                    pattern_info["patterns"].append("THREE_WHITE_SOLDIERS")
                
                # 18. 上升三法
                if (prev3_is_bullish and
                    prev3_body > prev2_body * 2 and
                    prev2_is_bearish and
                    prev1_is_bearish and
                    curr_is_bullish and
                    curr["close"] > prev3["close"] and
                    prev2["low"] > prev3["low"] and
                    prev1["low"] > prev3["low"]):
                    pattern_info["patterns"].append("THREE_RISING_METHODS")
                
                # 19. 下降三法
                if (prev3_is_bearish and
                    prev3_body > prev2_body * 2 and
                    prev2_is_bullish and
                    prev1_is_bullish and
                    curr_is_bearish and
                    curr["close"] < prev3["close"] and
                    prev2["high"] < prev3["high"] and
                    prev1["high"] < prev3["high"]):
                    pattern_info["patterns"].append("THREE_FALLING_METHODS")
                
                # 20. 红三兵受阻
                if (prev2_is_bullish and
                    prev1_is_bullish and
                    curr_is_bullish and
                    prev1_body > prev2_body and
                    curr_body < prev1_body * 0.7):
                    pattern_info["patterns"].append("THREE_ADVANCING_BLOCKS")
                
                # 21. 白三兵受阻
                if (prev2_is_bearish and
                    prev1_is_bearish and
                    curr_is_bearish and
                    prev1_body > prev2_body and
                    curr_body < prev1_body * 0.7):
                    pattern_info["patterns"].append("THREE_DECLINING_BLOCKS")
            
            # ==================== 趋势确认形态 ====================
            
            # 22. 连续上涨/下跌
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
            
            # 23. 新高/新低
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
        return result_df.to_csv(index=False) if len(result_df) > 0 else "timestamp,open,high,low,close,patterns\n"
    
    def _identify_swing_highs(self, df, lookback=2):
        """识别高点"""
        swing_highs = []
        for i in range(lookback, len(df) - lookback):
            is_swing_high = True
            for j in range(1, lookback + 1):
                if df["high"].iloc[i] <= df["high"].iloc[i - j] or df["high"].iloc[i] <= df["high"].iloc[i + j]:
                    is_swing_high = False
                    break
            swing_highs.append(df["high"].iloc[i] if is_swing_high else np.nan)
        return pd.Series([np.nan] * lookback + swing_highs + [np.nan] * lookback, index=df.index)
    
    def _identify_swing_lows(self, df, lookback=2):
        """识别低点"""
        swing_lows = []
        for i in range(lookback, len(df) - lookback):
            is_swing_low = True
            for j in range(1, lookback + 1):
                if df["low"].iloc[i] >= df["low"].iloc[i - j] or df["low"].iloc[i] >= df["low"].iloc[i + j]:
                    is_swing_low = False
                    break
            swing_lows.append(df["low"].iloc[i] if is_swing_low else np.nan)
        return pd.Series([np.nan] * lookback + swing_lows + [np.nan] * lookback, index=df.index)
    
    def get_fundamentals(self, symbol: str, curr_date: str = None, *args, **kwargs) -> str:
        """获取基本面数据
        
        使用长桥 API 的 static_info() 方法获取部分基本面数据
        
        Raises:
            ValueError: 如果股票代码无效
        """
        from tradingagents.utils.validators import validate_symbol
        validate_symbol(symbol)
        
        self._initialize()
        
        if self.quote_ctx is None:
            raise Exception("长桥 API 未正确初始化")
        
        lb_symbol = symbol
        if not (lb_symbol.endswith('.US') or lb_symbol.endswith('.HK') or lb_symbol.endswith('.SH') or lb_symbol.endswith('.SZ')):
            lb_symbol = f"{symbol}.US"
        
        info_list = self.quote_ctx.static_info([lb_symbol])
        
        if not info_list:
            raise Exception(f"长桥 API 返回空数据: {lb_symbol}")
        
        info = info_list[0]
        
        fields = [
            ("Name (CN)", info.name_cn),
            ("Name (EN)", info.name_en),
            ("Symbol", info.symbol),
            ("Exchange", info.exchange),
            ("Currency", info.currency),
            ("Lot Size", info.lot_size),
            ("Total Shares", info.total_shares),
            ("Circulating Shares", info.circulating_shares),
            ("EPS", float(info.eps) if info.eps else None),
            ("EPS (TTM)", float(info.eps_ttm) if info.eps_ttm else None),
            ("BPS (Net Assets per Share)", float(info.bps) if info.bps else None),
            ("Dividend Yield", float(info.dividend_yield) if info.dividend_yield else None),
            ("Board", str(info.board)),
        ]
        
        lines = []
        for label, value in fields:
            if value is not None:
                lines.append(f"{label}: {value}")
        
        header = f"# Company Fundamentals for {symbol.upper()}\n"
        header += f"# Data source: Longbridge API\n"
        header += f"# Data retrieved on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        return header + "\n".join(lines)
    
    def get_balance_sheet(self, symbol: str, freq: str = "quarterly", curr_date: str = None, *args, **kwargs) -> str:
        """获取资产负债表
        
        注意: 长桥 API 不提供完整的资产负债表数据
        此方法会抛出 NotImplementedError，让系统回退到其他数据源
        """
        raise NotImplementedError("长桥 API 不提供完整的资产负债表数据，请使用 Yahoo Finance 或 Alpha Vantage")
    
    def get_cashflow(self, symbol: str, freq: str = "quarterly", curr_date: str = None, *args, **kwargs) -> str:
        """获取现金流量表
        
        注意: 长桥 API 不提供完整的现金流量表数据
        此方法会抛出 NotImplementedError，让系统回退到其他数据源
        """
        raise NotImplementedError("长桥 API 不提供完整的现金流量表数据，请使用 Yahoo Finance 或 Alpha Vantage")
    
    def get_income_statement(self, symbol: str, freq: str = "quarterly", curr_date: str = None, *args, **kwargs) -> str:
        """获取损益表
        
        注意: 长桥 API 不提供完整的损益表数据
        此方法会抛出 NotImplementedError，让系统回退到其他数据源
        """
        raise NotImplementedError("长桥 API 不提供完整的损益表数据，请使用 Yahoo Finance 或 Alpha Vantage")
    
    def get_news(self, symbol: str, limit: int = 10) -> str:
        """获取新闻数据
        
        注意: 长桥 API 不提供新闻数据
        此方法会抛出 NotImplementedError，让系统回退到其他数据源
        """
        raise NotImplementedError("长桥 API 不提供新闻数据，请使用 Yahoo Finance 或 Alpha Vantage")
    
    def get_global_news(self, limit: int = 10) -> str:
        """获取全球新闻
        
        注意: 长桥 API 不提供新闻数据
        此方法会抛出 NotImplementedError，让系统回退到其他数据源
        """
        raise NotImplementedError("长桥 API 不提供全球新闻数据，请使用 Yahoo Finance 或 Alpha Vantage")
    
    def get_insider_transactions(self, symbol: str, limit: int = 10) -> str:
        """获取内幕交易数据
        
        注意: 长桥 API 不提供内幕交易数据
        此方法会抛出 NotImplementedError，让系统回退到其他数据源
        """
        raise NotImplementedError("长桥 API 不提供内幕交易数据，请使用 Yahoo Finance 或 Alpha Vantage")


# 全局实例
_longbridge_api = None


def get_longbridge_api() -> LongbridgeAPI:
    """获取长桥API实例（单例）"""
    global _longbridge_api
    if _longbridge_api is None:
        _longbridge_api = LongbridgeAPI()
    return _longbridge_api


# ==================== 导出函数 ====================

@cached
def get_stock(symbol: str, start_date: str, end_date: str) -> str:
    """获取股票数据
    
    Args:
        symbol: 股票代码
        start_date: 开始日期 (yyyy-mm-dd)
        end_date: 结束日期 (yyyy-mm-dd)
        
    Raises:
        ValueError: 如果输入参数无效
    """
    from tradingagents.utils.validators import validate_symbol, validate_date_range
    
    # 输入验证
    validate_symbol(symbol)
    validate_date_range(start_date, end_date)
    
    api = get_longbridge_api()
    return api.get_stock_data(symbol, start_date, end_date)


@cached
def get_indicator(symbol: str, indicator: str, curr_date: str, look_back_days: int = 120) -> str:
    """获取技术指标（兼容 yfinance 和 alpha_vantage 的签名）
    
    Args:
        symbol: 股票代码
        indicator: 指标名称（单个字符串，不是列表）
        curr_date: 当前日期
        look_back_days: 回看天数
        
    Raises:
        ValueError: 如果输入参数无效
    """
    from tradingagents.utils.validators import validate_symbol, validate_date
    
    # 输入验证
    validate_symbol(symbol)
    validate_date(curr_date)
    if look_back_days < 1 or look_back_days > 1000:
        raise ValueError(f"look_back_days必须在1-1000之间，当前值：{look_back_days}")
    from datetime import datetime
    from dateutil.relativedelta import relativedelta
    from .indicator_groups import get_indicator_columns
    
    api = get_longbridge_api()
    
    curr_date_dt = datetime.strptime(curr_date, "%Y-%m-%d")
    start_date_dt = curr_date_dt - relativedelta(days=look_back_days + 60)
    
    # 获取所有指标
    all_indicators_csv = api.get_indicators(
        symbol, 
        [],  # 传入空列表，会计算所有指标
        start_date_dt.strftime("%Y-%m-%d"), 
        curr_date
    )
    
    # 解析CSV，只保留需要的指标
    df = pd.read_csv(StringIO(all_indicators_csv))
    
    # 使用统一的指标组配置来确定需要保留的列
    keep_cols = get_indicator_columns(indicator, list(df.columns))
    
    # 只保留需要的列
    result_df = df[[col for col in keep_cols if col in df.columns]]
    
    # 只返回最近look_back_days天的数据
    result_df = result_df.tail(look_back_days + 10)
    
    return result_df.to_csv(index=False)


@cached
def get_fundamentals(symbol: str, curr_date: str = None, *args, **kwargs) -> str:
    """获取基本面数据
    
    Raises:
        ValueError: 如果股票代码无效
    """
    from tradingagents.utils.validators import validate_symbol
    validate_symbol(symbol)
    
    api = get_longbridge_api()
    return api.get_fundamentals(symbol)


@cached
def get_balance_sheet(symbol: str, freq: str = "quarterly", curr_date: str = None, *args, **kwargs) -> str:
    """获取资产负债表
    
    Raises:
        ValueError: 如果股票代码无效
    """
    from tradingagents.utils.validators import validate_symbol
    validate_symbol(symbol)
    
    api = get_longbridge_api()
    return api.get_balance_sheet(symbol)


@cached
def get_cashflow(symbol: str, freq: str = "quarterly", curr_date: str = None, *args, **kwargs) -> str:
    """获取现金流量表
    
    Raises:
        ValueError: 如果股票代码无效
    """
    from tradingagents.utils.validators import validate_symbol
    validate_symbol(symbol)
    
    api = get_longbridge_api()
    return api.get_cashflow(symbol)


@cached
def get_income_statement(symbol: str, freq: str = "quarterly", curr_date: str = None, *args, **kwargs) -> str:
    """获取损益表
    
    Raises:
        ValueError: 如果股票代码无效
    """
    from tradingagents.utils.validators import validate_symbol
    validate_symbol(symbol)
    
    api = get_longbridge_api()
    return api.get_income_statement(symbol)


def get_news(symbol: str, limit: int = 10) -> str:
    """获取新闻
    
    Raises:
        ValueError: 如果股票代码无效或limit超出范围
    """
    from tradingagents.utils.validators import validate_symbol
    validate_symbol(symbol)
    if limit < 1 or limit > 100:
        raise ValueError(f"limit必须在1-100之间，当前值：{limit}")
    
    api = get_longbridge_api()
    return api.get_news(symbol, limit)


def get_global_news(limit: int = 10) -> str:
    """获取全球新闻
    
    Raises:
        ValueError: 如果limit超出范围
    """
    if limit < 1 or limit > 100:
        raise ValueError(f"limit必须在1-100之间，当前值：{limit}")
    
    api = get_longbridge_api()
    return api.get_global_news(limit)

@cached
def get_insider_transactions(symbol: str, limit: int = 10) -> str:
    """获取内幕交易
    
    Raises:
        ValueError: 如果股票代码无效或limit超出范围
    """
    from tradingagents.utils.validators import validate_symbol
    validate_symbol(symbol)
    if limit < 1 or limit > 100:
        raise ValueError(f"limit必须在1-100之间，当前值：{limit}")
    api = get_longbridge_api()
    return api.get_insider_transactions(symbol, limit)


@cached
def get_candlestick_patterns(symbol: str, start_date: str, end_date: str) -> str:
    """获取蜡烛图形态"""
    api = get_longbridge_api()
    return api.get_candlestick_patterns(symbol, start_date, end_date)
