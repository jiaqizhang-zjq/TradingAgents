import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from tradingagents.dataflows.interface import route_to_vendor
from tradingagents.dataflows.config import get_config
from tradingagents.dataflows.data_loader_mixin import DataLoaderMixin
from tradingagents.utils.logger import get_logger

logger = get_logger(__name__)


class DataPreloader(DataLoaderMixin):
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
    
    def _load_fundamentals(self):
        """加载基本面数据"""
        try:
            self.fundamentals = route_to_vendor("get_fundamentals", self.ticker)
        except (ValueError, ConnectionError, TimeoutError, NotImplementedError) as e:
            logger.warning("加载基本面数据失败 (%s): %s", self.ticker, e)
            self.fundamentals = f"Error loading fundamentals: {str(e)}"
        
        try:
            self.balance_sheet = route_to_vendor("get_balance_sheet", self.ticker)
        except (ValueError, ConnectionError, TimeoutError, NotImplementedError) as e:
            logger.warning("加载资产负债表失败 (%s): %s", self.ticker, e)
            self.balance_sheet = f"Error loading balance sheet: {str(e)}"
        
        try:
            self.cashflow = route_to_vendor("get_cashflow", self.ticker)
        except (ValueError, ConnectionError, TimeoutError, NotImplementedError) as e:
            logger.warning("加载现金流量表失败 (%s): %s", self.ticker, e)
            self.cashflow = f"Error loading cashflow: {str(e)}"
        
        try:
            self.income_statement = route_to_vendor("get_income_statement", self.ticker)
        except (ValueError, ConnectionError, TimeoutError, NotImplementedError) as e:
            logger.warning("加载损益表失败 (%s): %s", self.ticker, e)
            self.income_statement = f"Error loading income statement: {str(e)}"
    
    def _load_news(self):
        """加载新闻数据"""
        news_start = (datetime.strptime(self.end_date, "%Y-%m-%d") - timedelta(days=30)).strftime("%Y-%m-%d")
        
        try:
            self.news = route_to_vendor("get_news", self.ticker, news_start, self.end_date)
        except (ValueError, ConnectionError, TimeoutError, NotImplementedError) as e:
            logger.warning("加载新闻数据失败 (%s): %s", self.ticker, e)
            self.news = f"Error loading news: {str(e)}"
        
        try:
            self.global_news = route_to_vendor("get_global_news", self.end_date, 30, 20)
        except (ValueError, ConnectionError, TimeoutError, NotImplementedError) as e:
            logger.warning("加载全球新闻失败: %s", e)
            self.global_news = f"Error loading global news: {str(e)}"
        
        try:
            from tradingagents.agents.utils.news_data_tools import get_social_media_data
            self.social_media = get_social_media_data.invoke({"symbol": self.ticker})
        except (ValueError, ConnectionError, TimeoutError, ImportError) as e:
            logger.warning("加载社交媒体数据失败 (%s): %s", self.ticker, e)
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
