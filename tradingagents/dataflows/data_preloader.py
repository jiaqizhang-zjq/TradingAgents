import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from tradingagents.dataflows.interface import route_to_vendor
from tradingagents.dataflows.config import get_config


class DataPreloader:
    """统一数据预加载器，避免重复API请求"""
    
    def __init__(self, ticker: str, end_date: str, lookback_days: int = 180):
        self.ticker = ticker
        self.end_date = end_date
        self.lookback_days = lookback_days
        self.start_date = (datetime.strptime(end_date, "%Y-%m-%d") - timedelta(days=lookback_days)).strftime("%Y-%m-%d")
        
        self.stock_data_df: Optional[pd.DataFrame] = None
        self.stock_data_str: str = ""
        self.indicators: Dict[str, Any] = {}
        self.fundamentals: str = ""
        self.balance_sheet: str = ""
        self.cashflow: str = ""
        self.income_statement: str = ""
        self.news: str = ""
        self.global_news: str = ""
        self.social_media: str = ""
        
    def load_all_data(self):
        """加载所有需要的数据"""
        self._load_stock_data()
        self._calculate_indicators()
        self._load_fundamentals()
        self._load_news()
        
    def _load_stock_data(self):
        """加载股票价格数据"""
        try:
            self.stock_data_str = route_to_vendor("get_stock_data", self.ticker, self.start_date, self.end_date)
            
            lines = self.stock_data_str.split('\n')
            if len(lines) > 1:
                header = lines[0].split(',')
                data = []
                for line in lines[1:]:
                    if line.strip():
                        data.append(line.split(','))
                
                if data and len(data[0]) == len(header):
                    self.stock_data_df = pd.DataFrame(data, columns=header)
                    for col in ['open', 'high', 'low', 'close', 'volume']:
                        if col in self.stock_data_df.columns:
                            self.stock_data_df[col] = pd.to_numeric(self.stock_data_df[col], errors='coerce')
                    if 'date' in self.stock_data_df.columns:
                        self.stock_data_df['date'] = pd.to_datetime(self.stock_data_df['date'])
                        self.stock_data_df = self.stock_data_df.set_index('date').sort_index()
        except Exception as e:
            self.stock_data_str = f"Error loading stock data: {str(e)}"
    
    def _calculate_indicators(self):
        """在线计算所有技术指标"""
        if self.stock_data_df is None or len(self.stock_data_df) < 20:
            return
        
        df = self.stock_data_df.copy()
        
        periods = [5, 10, 20, 50, 100, 200]
        for period in periods:
            if len(df) >= period:
                self.indicators[f'close_{period}_sma'] = self._format_indicator(
                    f"close_{period}_sma", 
                    df['close'].rolling(window=period).mean()
                )
                self.indicators[f'close_{period}_ema'] = self._format_indicator(
                    f'close_{period}_ema',
                    df['close'].ewm(span=period, adjust=False).mean()
                )
        
        if len(df) >= 26:
            ema12 = df['close'].ewm(span=12, adjust=False).mean()
            ema26 = df['close'].ewm(span=26, adjust=False).mean()
            macd_line = ema12 - ema26
            signal_line = macd_line.ewm(span=9, adjust=False).mean()
            histogram = macd_line - signal_line
            
            self.indicators['macd'] = self._format_indicator('macd', macd_line)
            self.indicators['macds'] = self._format_indicator('macds', signal_line)
            self.indicators['macdh'] = self._format_indicator('macdh', histogram)
        
        if len(df) >= 14:
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            self.indicators['rsi'] = self._format_indicator('rsi', rsi)
        
        if len(df) >= 20:
            sma20 = df['close'].rolling(window=20).mean()
            std20 = df['close'].rolling(window=20).std()
            boll_ub = sma20 + (std20 * 2)
            boll_lb = sma20 - (std20 * 2)
            
            self.indicators['boll'] = self._format_indicator('boll', sma20)
            self.indicators['boll_ub'] = self._format_indicator('boll_ub', boll_ub)
            self.indicators['boll_lb'] = self._format_indicator('boll_lb', boll_lb)
        
        if len(df) >= 14:
            high_low = df['high'] - df['low']
            high_close = np.abs(df['high'] - df['close'].shift())
            low_close = np.abs(df['low'] - df['close'].shift())
            true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            atr = true_range.rolling(window=14).mean()
            self.indicators['atr'] = self._format_indicator('atr', atr)
        
        if 'volume' in df.columns:
            self.indicators['volume'] = self._format_indicator('volume', df['volume'])
            
            if len(df) >= 14:
                obv = (np.sign(df['close'].diff()) * df['volume']).fillna(0).cumsum()
                self.indicators['obv'] = self._format_indicator('obv', obv)
    
    def _format_indicator(self, name: str, series: pd.Series) -> str:
        """格式化指标为字符串"""
        recent = series.tail(30)
        lines = [f"date,{name}"]
        for idx, val in recent.items():
            if pd.notna(val):
                lines.append(f"{idx.strftime('%Y-%m-%d')},{val:.4f}")
        return "\n".join(lines)
    
    def _load_fundamentals(self):
        """加载基本面数据"""
        try:
            self.fundamentals = route_to_vendor("get_fundamentals", self.ticker)
        except Exception as e:
            self.fundamentals = f"Error loading fundamentals: {str(e)}"
        
        try:
            self.balance_sheet = route_to_vendor("get_balance_sheet", self.ticker)
        except Exception as e:
            self.balance_sheet = f"Error loading balance sheet: {str(e)}"
        
        try:
            self.cashflow = route_to_vendor("get_cashflow", self.ticker)
        except Exception as e:
            self.cashflow = f"Error loading cashflow: {str(e)}"
        
        try:
            self.income_statement = route_to_vendor("get_income_statement", self.ticker)
        except Exception as e:
            self.income_statement = f"Error loading income statement: {str(e)}"
    
    def _load_news(self):
        """加载新闻数据"""
        news_start = (datetime.strptime(self.end_date, "%Y-%m-%d") - timedelta(days=30)).strftime("%Y-%m-%d")
        
        try:
            self.news = route_to_vendor("get_news", self.ticker, news_start, self.end_date)
        except Exception as e:
            self.news = f"Error loading news: {str(e)}"
        
        try:
            self.global_news = route_to_vendor("get_global_news", self.end_date, 30, 20)
        except Exception as e:
            self.global_news = f"Error loading global news: {str(e)}"
        
        try:
            from tradingagents.agents.utils.news_data_tools import get_social_media_data
            self.social_media = get_social_media_data.invoke({"symbol": self.ticker})
        except Exception as e:
            self.social_media = f"Error loading social media: {str(e)}"
    
    def get_stock_data(self) -> str:
        """获取股票数据"""
        return self.stock_data_str
    
    def get_indicator(self, name: str) -> str:
        """获取指定指标"""
        return self.indicators.get(name, f"Indicator {name} not available")
    
    def get_all_indicators_str(self) -> str:
        """获取所有指标的字符串表示"""
        result = ""
        for name, data in self.indicators.items():
            result += f"\n--- {name} ---\n{data}\n"
        return result
    
    def get_fundamentals(self) -> str:
        return self.fundamentals
    
    def get_balance_sheet(self) -> str:
        return self.balance_sheet
    
    def get_cashflow(self) -> str:
        return self.cashflow
    
    def get_income_statement(self) -> str:
        return self.income_statement
    
    def get_news(self) -> str:
        return self.news
    
    def get_global_news(self) -> str:
        return self.global_news
    
    def get_social_media(self) -> str:
        return self.social_media
