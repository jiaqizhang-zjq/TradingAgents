#!/usr/bin/env python3
"""
长桥（Longbridge）API客户端
负责与Longbridge API的交互和数据获取
"""

import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import pandas as pd
from io import StringIO

try:
    from longbridge.openapi import QuoteContext, Config, Period, AdjustType
    HAS_LONGBRIDGE = True
except ImportError:
    HAS_LONGBRIDGE = False


class LongbridgeClient:
    """长桥API客户端（仅负责API调用）"""
    
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
            raise ImportError("longbridge SDK 未安装，请运行: pip install longbridge")
            
        app_key = os.environ.get("LONGBRIDGE_APP_KEY", "")
        app_secret = os.environ.get("LONGBRIDGE_APP_SECRET", "")
        access_token = os.environ.get("LONGBRIDGE_ACCESS_TOKEN", "")
        
        if not all([app_key, app_secret, access_token]):
            raise ValueError("缺少Longbridge配置，请设置环境变量：LONGBRIDGE_APP_KEY, LONGBRIDGE_APP_SECRET, LONGBRIDGE_ACCESS_TOKEN")
        
        self.config = Config(app_key=app_key, app_secret=app_secret, access_token=access_token)
        self.quote_ctx = QuoteContext(self.config)
        self.initialized = True
    
    def get_candlesticks(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        获取K线数据
        
        Args:
            symbol: 股票代码
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            
        Returns:
            包含OHLCV数据的DataFrame
        """
        self._initialize()
        
        # 调用Longbridge API获取K线数据
        resp = self.quote_ctx.candlesticks(
            symbol=symbol,
            period=Period.Day,
            count=1000,  # 最多获取1000根K线
            adjust_type=AdjustType.ForwardAdjust
        )
        
        # 转换为DataFrame
        data = []
        for candle in resp:
            data.append({
                "timestamp": candle.timestamp,
                "open": candle.open,
                "high": candle.high,
                "low": candle.low,
                "close": candle.close,
                "volume": candle.volume,
            })
        
        df = pd.DataFrame(data)
        
        # 过滤日期范围
        if not df.empty:
            df['date'] = pd.to_datetime(df['timestamp']).dt.date
            start = datetime.strptime(start_date, '%Y-%m-%d').date()
            end = datetime.strptime(end_date, '%Y-%m-%d').date()
            df = df[(df['date'] >= start) & (df['date'] <= end)]
        
        return df
    
    def get_quote(self, symbol: str) -> Dict[str, Any]:
        """
        获取实时行情
        
        Args:
            symbol: 股票代码
            
        Returns:
            行情数据字典
        """
        self._initialize()
        
        resp = self.quote_ctx.quote([symbol])
        if not resp:
            return {}
        
        quote = resp[0]
        return {
            "symbol": quote.symbol,
            "last_done": quote.last_done,
            "prev_close": quote.prev_close,
            "open": quote.open,
            "high": quote.high,
            "low": quote.low,
            "volume": quote.volume,
            "turnover": quote.turnover,
        }
