"""
数据加载器共享逻辑 Mixin

将 DataPreloader 和 AsyncDataLoader 中完全重复的
_load_stock_data / _calculate_indicators / _format_indicator
提取为可复用的 mixin，消除 ~93 行重复代码。
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional

from tradingagents.dataflows.interface import route_to_vendor
from tradingagents.utils.logger import get_logger

logger = get_logger(__name__)


class DataLoaderMixin:
    """数据加载器共享逻辑 Mixin

    子类需提供以下属性：
    - ticker: str
    - start_date: str
    - end_date: str
    - stock_data_df: Optional[pd.DataFrame]
    - stock_data_str: str
    - indicators: Dict[str, Any]
    """

    # ------------------------------------------------------------------ #
    #  股票数据加载（CSV 解析）
    # ------------------------------------------------------------------ #
    def _load_stock_data(self) -> None:
        """加载股票价格数据并解析为 DataFrame"""
        try:
            self.stock_data_str = route_to_vendor(
                "get_stock_data", self.ticker, self.start_date, self.end_date
            )

            lines = self.stock_data_str.split("\n")
            if len(lines) > 1:
                header = lines[0].split(",")
                data = [
                    line.split(",") for line in lines[1:] if line.strip()
                ]

                if data and len(data[0]) == len(header):
                    self.stock_data_df = pd.DataFrame(data, columns=header)
                    for col in ["open", "high", "low", "close", "volume"]:
                        if col in self.stock_data_df.columns:
                            self.stock_data_df[col] = pd.to_numeric(
                                self.stock_data_df[col], errors="coerce"
                            )
                    if "date" in self.stock_data_df.columns:
                        self.stock_data_df["date"] = pd.to_datetime(
                            self.stock_data_df["date"]
                        )
                        self.stock_data_df = (
                            self.stock_data_df.set_index("date").sort_index()
                        )
        except (ValueError, KeyError, ConnectionError, TimeoutError, OSError) as e:
            logger.warning("加载股票数据失败 (%s): %s", self.ticker, e)
            self.stock_data_str = f"Error loading stock data: {str(e)}"

    # ------------------------------------------------------------------ #
    #  技术指标计算
    # ------------------------------------------------------------------ #
    def _calculate_indicators(self) -> None:
        """在线计算所有技术指标"""
        if self.stock_data_df is None or len(self.stock_data_df) < 20:
            return

        df = self.stock_data_df.copy()

        # 移动平均线
        periods = [5, 10, 20, 50, 100, 200]
        for period in periods:
            if len(df) >= period:
                self.indicators[f"close_{period}_sma"] = self._format_indicator(
                    f"close_{period}_sma",
                    df["close"].rolling(window=period).mean(),
                )
                self.indicators[f"close_{period}_ema"] = self._format_indicator(
                    f"close_{period}_ema",
                    df["close"].ewm(span=period, adjust=False).mean(),
                )

        # MACD
        if len(df) >= 26:
            ema12 = df["close"].ewm(span=12, adjust=False).mean()
            ema26 = df["close"].ewm(span=26, adjust=False).mean()
            macd_line = ema12 - ema26
            signal_line = macd_line.ewm(span=9, adjust=False).mean()
            histogram = macd_line - signal_line

            self.indicators["macd"] = self._format_indicator("macd", macd_line)
            self.indicators["macds"] = self._format_indicator("macds", signal_line)
            self.indicators["macdh"] = self._format_indicator("macdh", histogram)

        # RSI
        if len(df) >= 14:
            delta = df["close"].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            self.indicators["rsi"] = self._format_indicator("rsi", rsi)

        # 布林带
        if len(df) >= 20:
            sma20 = df["close"].rolling(window=20).mean()
            std20 = df["close"].rolling(window=20).std()
            boll_ub = sma20 + (std20 * 2)
            boll_lb = sma20 - (std20 * 2)

            self.indicators["boll"] = self._format_indicator("boll", sma20)
            self.indicators["boll_ub"] = self._format_indicator("boll_ub", boll_ub)
            self.indicators["boll_lb"] = self._format_indicator("boll_lb", boll_lb)

        # ATR
        if len(df) >= 14:
            high_low = df["high"] - df["low"]
            high_close = np.abs(df["high"] - df["close"].shift())
            low_close = np.abs(df["low"] - df["close"].shift())
            true_range = pd.concat(
                [high_low, high_close, low_close], axis=1
            ).max(axis=1)
            atr = true_range.rolling(window=14).mean()
            self.indicators["atr"] = self._format_indicator("atr", atr)

        # 成交量指标
        if "volume" in df.columns:
            self.indicators["volume"] = self._format_indicator("volume", df["volume"])

            if len(df) >= 14:
                obv = (
                    (np.sign(df["close"].diff()) * df["volume"]).fillna(0).cumsum()
                )
                self.indicators["obv"] = self._format_indicator("obv", obv)

    # ------------------------------------------------------------------ #
    #  格式化
    # ------------------------------------------------------------------ #
    @staticmethod
    def _format_indicator(name: str, series: pd.Series) -> str:
        """格式化指标为 CSV 字符串"""
        recent = series.tail(30)
        lines = [f"date,{name}"]
        for idx, val in recent.items():
            if pd.notna(val):
                lines.append(f"{idx.strftime('%Y-%m-%d')},{val:.4f}")
        return "\n".join(lines)
