# TradingAgents/dataflows/longbridge.py
"""
长桥（Longbridge）API 实现
提供股票数据、技术指标、基本面数据等功能
"""

import os
import json
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import pandas as pd

from .api_config import get_api_config
from .data_cache import cached

try:
    from longbridge.openapi import QuoteContext, Config
    HAS_LONGBRIDGE = True
except ImportError:
    HAS_LONGBRIDGE = False
    print("警告: 未安装 longbridge SDK，请运行: pip install longbridge")


class LongbridgeAPI:
    """长桥API封装类"""
    
    def __init__(self):
        """初始化长桥API"""
        self.config = None
        self.quote_ctx = None
        self.initialized = False
        
    def _initialize(self):
        """延迟初始化长桥连接"""
        if self.initialized:
            return
            
        if not HAS_LONGBRIDGE:
            raise ImportError("longbridge SDK 未安装")
            
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
        """
        self._initialize()
        
        # 转换日期
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        
        # 获取K线数据
        # 注意: 长桥API的具体调用需要根据实际SDK调整
        # 这里提供一个模拟实现，实际使用时需要替换为真实的API调用
        
        # 模拟数据 - 实际项目中替换为真实API调用
        data = self._generate_mock_stock_data(symbol, start_dt, end_dt)
        
        return data
    
    def _generate_mock_stock_data(self, symbol: str, start_dt: datetime, end_dt: datetime) -> str:
        """生成模拟股票数据（用于演示）"""
        dates = []
        current = start_dt
        while current <= end_dt:
            dates.append(current)
            current += timedelta(days=1)
        
        # 生成模拟数据
        data = []
        base_price = 100.0
        for i, date in enumerate(dates):
            # 周末跳过
            if date.weekday() >= 5:
                continue
                
            # 生成随机价格变化
            import random
            change = random.uniform(-0.05, 0.05)
            open_price = base_price * (1 + change)
            high = open_price * 1.02
            low = open_price * 0.98
            close = (open_price + high + low) / 3
            volume = random.randint(1000000, 10000000)
            
            data.append({
                "timestamp": date.strftime("%Y-%m-%d"),
                "open": round(open_price, 2),
                "high": round(high, 2),
                "low": round(low, 2),
                "close": round(close, 2),
                "volume": volume,
                "adjusted_close": round(close, 2)
            })
            
            base_price = close
        
        # 转换为CSV
        df = pd.DataFrame(data)
        return df.to_csv(index=False)
    
    def get_indicators(self, symbol: str, indicators: List[str], start_date: str, end_date: str) -> str:
        """
        获取技术指标数据
        
        Args:
            symbol: 股票代码
            indicators: 指标列表
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            CSV格式的指标数据
        """
        # 首先获取股票数据
        stock_data = self.get_stock_data(symbol, start_date, end_date)
        
        # 计算技术指标
        df = pd.read_csv(pd.compat.StringIO(stock_data))
        
        # 计算常用技术指标
        for indicator in indicators:
            # 移动平均线 - SMA
            if indicator == "close_5_sma":
                df["close_5_sma"] = df["close"].rolling(window=5).mean()
            elif indicator == "close_10_sma":
                df["close_10_sma"] = df["close"].rolling(window=10).mean()
            elif indicator == "close_20_sma":
                df["close_20_sma"] = df["close"].rolling(window=20).mean()
            elif indicator == "close_50_sma":
                df["close_50_sma"] = df["close"].rolling(window=50).mean()
            elif indicator == "close_100_sma":
                df["close_100_sma"] = df["close"].rolling(window=100).mean()
            elif indicator == "close_200_sma":
                df["close_200_sma"] = df["close"].rolling(window=200).mean()
            # 移动平均线 - EMA
            elif indicator == "close_5_ema":
                df["close_5_ema"] = df["close"].ewm(span=5, adjust=False).mean()
            elif indicator == "close_10_ema":
                df["close_10_ema"] = df["close"].ewm(span=10, adjust=False).mean()
            elif indicator == "close_20_ema":
                df["close_20_ema"] = df["close"].ewm(span=20, adjust=False).mean()
            elif indicator == "close_50_ema":
                df["close_50_ema"] = df["close"].ewm(span=50, adjust=False).mean()
            elif indicator == "close_100_ema":
                df["close_100_ema"] = df["close"].ewm(span=100, adjust=False).mean()
            elif indicator == "close_200_ema":
                df["close_200_ema"] = df["close"].ewm(span=200, adjust=False).mean()
            # MACD
            elif indicator == "macd":
                macd, signal, hist = self._calculate_macd(df["close"])
                df["macd"] = macd
                df["macds"] = signal
                df["macdh"] = hist
            # RSI
            elif indicator == "rsi":
                df["rsi"] = self._calculate_rsi(df["close"])
            # Stochastic Oscillator
            elif indicator == "stoch":
                k, d = self._calculate_stochastic(df)
                df["stoch_k"] = k
                df["stoch_d"] = d
            # Stochastic RSI
            elif indicator == "stochrsi":
                stochrsi_k, stochrsi_d = self._calculate_stochrsi(df["close"])
                df["stochrsi_k"] = stochrsi_k
                df["stochrsi_d"] = stochrsi_d
            # CCI
            elif indicator == "cci":
                df["cci"] = self._calculate_cci(df)
            # ROC
            elif indicator == "roc":
                df["roc"] = self._calculate_roc(df["close"])
            # MFI
            elif indicator == "mfi":
                df["mfi"] = self._calculate_mfi(df)
            # Bollinger Bands
            elif indicator.startswith("boll"):
                sma = df["close"].rolling(window=20).mean()
                std = df["close"].rolling(window=20).std()
                df["boll"] = sma
                df["boll_ub"] = sma + (std * 2)
                df["boll_lb"] = sma - (std * 2)
                df["boll_pct_b"] = (df["close"] - df["boll_lb"]) / (df["boll_ub"] - df["boll_lb"])
                df["boll_width"] = (df["boll_ub"] - df["boll_lb"]) / df["boll"]
            # ATR
            elif indicator == "atr":
                df["atr"] = self._calculate_atr(df)
            elif indicator == "natr":
                atr = self._calculate_atr(df)
                df["natr"] = atr / df["close"] * 100
            # Volume indicators
            elif indicator == "vwma":
                df["vwma"] = self._calculate_vwma(df)
            elif indicator == "volume":
                df["volume"] = df["volume"]
            elif indicator == "obv":
                df["obv"] = self._calculate_obv(df)
            elif indicator == "ad":
                df["ad"] = self._calculate_ad(df)
            # ADX
            elif indicator in ["adx", "plus_di", "minus_di"]:
                adx, plus_di, minus_di = self._calculate_adx(df)
                df["adx"] = adx
                df["plus_di"] = plus_di
                df["minus_di"] = minus_di
            # Swing highs/lows
            elif indicator == "swing_highs":
                df["swing_high"] = self._identify_swing_highs(df)
            elif indicator == "swing_lows":
                df["swing_low"] = self._identify_swing_lows(df)
            # Fibonacci levels (simplified)
            elif indicator in ["fib_382", "fib_500", "fib_618"]:
                fib_levels = self._calculate_fibonacci(df)
                df["fib_382"] = fib_levels["38.2%"]
                df["fib_500"] = fib_levels["50%"]
                df["fib_618"] = fib_levels["61.8%"]
            # Pivot points
            elif indicator in ["pivot", "r1", "r2", "s1", "s2"]:
                pivot_levels = self._calculate_pivot_points(df)
                df["pivot"] = pivot_levels["pivot"]
                df["r1"] = pivot_levels["r1"]
                df["r2"] = pivot_levels["r2"]
                df["s1"] = pivot_levels["s1"]
                df["s2"] = pivot_levels["s2"]
        
        return df.to_csv(index=False)
    
    def _calculate_rsi(self, prices, period=14):
        """计算RSI指标"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _calculate_macd(self, prices, fast=12, slow=26, signal=9):
        """计算MACD指标"""
        ema_fast = prices.ewm(span=fast, adjust=False).mean()
        ema_slow = prices.ewm(span=slow, adjust=False).mean()
        macd = ema_fast - ema_slow
        signal_line = macd.ewm(span=signal, adjust=False).mean()
        histogram = macd - signal_line
        return macd, signal_line, histogram
    
    def _calculate_atr(self, df, period=14):
        """计算ATR指标"""
        high_low = df["high"] - df["low"]
        high_close = abs(df["high"] - df["close"].shift())
        low_close = abs(df["low"] - df["close"].shift())
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        return atr
    
    def _calculate_stochastic(self, df, period=14, smooth_k=3, smooth_d=3):
        """计算随机振荡器"""
        low_min = df["low"].rolling(window=period).min()
        high_max = df["high"].rolling(window=period).max()
        k = 100 * ((df["close"] - low_min) / (high_max - low_min))
        d = k.rolling(window=smooth_k).mean()
        slow_k = d.rolling(window=smooth_d).mean()
        return slow_k, slow_k.rolling(window=smooth_d).mean()
    
    def _calculate_stochrsi(self, prices, period=14, smooth_k=3, smooth_d=3):
        """计算随机RSI"""
        rsi = self._calculate_rsi(prices, period)
        rsi_low = rsi.rolling(window=period).min()
        rsi_high = rsi.rolling(window=period).max()
        stochrsi = 100 * ((rsi - rsi_low) / (rsi_high - rsi_low))
        k = stochrsi.rolling(window=smooth_k).mean()
        d = k.rolling(window=smooth_d).mean()
        return k, d
    
    def _calculate_cci(self, df, period=20):
        """计算CCI指标"""
        typical_price = (df["high"] + df["low"] + df["close"]) / 3
        sma_tp = typical_price.rolling(window=period).mean()
        mad = typical_price.rolling(window=period).apply(lambda x: abs(x - x.mean()).mean(), raw=True)
        cci = (typical_price - sma_tp) / (0.015 * mad)
        return cci
    
    def _calculate_roc(self, prices, period=12):
        """计算ROC指标"""
        roc = ((prices - prices.shift(period)) / prices.shift(period)) * 100
        return roc
    
    def _calculate_mfi(self, df, period=14):
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
    
    def _calculate_vwma(self, df, period=20):
        """计算VWMA指标"""
        typical_price = (df["high"] + df["low"] + df["close"]) / 3
        vp = typical_price * df["volume"]
        vwma = vp.rolling(window=period).sum() / df["volume"].rolling(window=period).sum()
        return vwma
    
    def _calculate_obv(self, df):
        """计算OBV指标"""
        obv = (np.sign(df["close"].diff()) * df["volume"]).fillna(0).cumsum()
        return obv
    
    def _calculate_ad(self, df):
        """计算AD指标"""
        clv = ((df["close"] - df["low"]) - (df["high"] - df["close"])) / (df["high"] - df["low"])
        clv = clv.fillna(0)
        ad = (clv * df["volume"]).cumsum()
        return ad
    
    def _calculate_adx(self, df, period=14):
        """计算ADX指标"""
        high = df["high"]
        low = df["low"]
        close = df["close"]
        
        plus_dm = high.diff()
        minus_dm = low.diff() * (-1)
        
        plus_dm = plus_dm.where((plus_dm > minus_dm) & (plus_dm > 0), 0)
        minus_dm = minus_dm.where((minus_dm > plus_dm) & (minus_dm > 0), 0)
        
        tr = self._calculate_atr(df, period=1)
        
        plus_di = 100 * (plus_dm.rolling(window=period).mean() / tr.rolling(window=period).mean())
        minus_di = 100 * (minus_dm.rolling(window=period).mean() / tr.rolling(window=period).mean())
        
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.rolling(window=period).mean()
        
        return adx, plus_di, minus_di
    
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
    
    def _calculate_fibonacci(self, df):
        """计算斐波那契回调位（简化版）"""
        recent_high = df["high"].max()
        recent_low = df["low"].min()
        diff = recent_high - recent_low
        
        return {
            "38.2%": recent_high - diff * 0.382,
            "50%": recent_high - diff * 0.5,
            "61.8%": recent_high - diff * 0.618
        }
    
    def _calculate_pivot_points(self, df):
        """计算枢纽点（使用最新的一根K线）"""
        if len(df) < 1:
            return {"pivot": 0, "r1": 0, "r2": 0, "s1": 0, "s2": 0}
        
        latest = df.iloc[-1]
        high = latest["high"]
        low = latest["low"]
        close = latest["close"]
        
        pivot = (high + low + close) / 3
        r1 = 2 * pivot - low
        r2 = pivot + (high - low)
        s1 = 2 * pivot - high
        s2 = pivot - (high - low)
        
        return {
            "pivot": pivot,
            "r1": r1,
            "r2": r2,
            "s1": s1,
            "s2": s2
        }
    
    def get_fundamentals(self, symbol: str) -> str:
        """
        获取基本面数据
        
        Args:
            symbol: 股票代码
            
        Returns:
            JSON格式的基本面数据
        """
        # 模拟基本面数据
        fundamentals = {
            "symbol": symbol,
            "market_cap": "100000000000",
            "pe_ratio": 25.5,
            "pb_ratio": 3.2,
            "dividend_yield": 0.025,
            "eps": 5.25,
            "revenue_growth": 0.15,
            "profit_margin": 0.18
        }
        return json.dumps(fundamentals, indent=2)
    
    def get_balance_sheet(self, symbol: str) -> str:
        """获取资产负债表"""
        balance_sheet = {
            "symbol": symbol,
            "total_assets": "50000000000",
            "total_liabilities": "20000000000",
            "shareholder_equity": "30000000000",
            "cash_and_equivalents": "5000000000",
            "debt": "10000000000"
        }
        return json.dumps(balance_sheet, indent=2)
    
    def get_cashflow(self, symbol: str) -> str:
        """获取现金流量表"""
        cashflow = {
            "symbol": symbol,
            "operating_cashflow": "8000000000",
            "investing_cashflow": "-3000000000",
            "financing_cashflow": "-2000000000",
            "free_cashflow": "5000000000"
        }
        return json.dumps(cashflow, indent=2)
    
    def get_income_statement(self, symbol: str) -> str:
        """获取损益表"""
        income = {
            "symbol": symbol,
            "revenue": "25000000000",
            "cost_of_revenue": "15000000000",
            "gross_profit": "10000000000",
            "operating_income": "6000000000",
            "net_income": "4500000000"
        }
        return json.dumps(income, indent=2)
    
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
    """获取股票数据"""
    api = get_longbridge_api()
    return api.get_stock_data(symbol, start_date, end_date)


@cached
def get_indicator(symbol: str, indicators: List[str], start_date: str, end_date: str) -> str:
    """获取技术指标"""
    api = get_longbridge_api()
    return api.get_indicators(symbol, indicators, start_date, end_date)


@cached
def get_fundamentals(symbol: str) -> str:
    """获取基本面数据"""
    api = get_longbridge_api()
    return api.get_fundamentals(symbol)


@cached
def get_balance_sheet(symbol: str) -> str:
    """获取资产负债表"""
    api = get_longbridge_api()
    return api.get_balance_sheet(symbol)


@cached
def get_cashflow(symbol: str) -> str:
    """获取现金流量表"""
    api = get_longbridge_api()
    return api.get_cashflow(symbol)


@cached
def get_income_statement(symbol: str) -> str:
    """获取损益表"""
    api = get_longbridge_api()
    return api.get_income_statement(symbol)


def get_news(symbol: str, limit: int = 10) -> str:
    """获取新闻"""
    api = get_longbridge_api()
    return api.get_news(symbol, limit)


def get_global_news(limit: int = 10) -> str:
    """获取全球新闻"""
    api = get_longbridge_api()
    return api.get_global_news(limit)


def get_insider_transactions(symbol: str, limit: int = 10) -> str:
    """获取内幕交易"""
    api = get_longbridge_api()
    return api.get_insider_transactions(symbol, limit)
