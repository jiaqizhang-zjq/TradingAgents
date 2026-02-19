from typing import Annotated

# Import from vendor-specific modules
from .y_finance import (
    get_YFin_data_online,
    get_stock_stats_indicators_window,
    get_fundamentals as get_yfinance_fundamentals,
    get_balance_sheet as get_yfinance_balance_sheet,
    get_cashflow as get_yfinance_cashflow,
    get_income_statement as get_yfinance_income_statement,
    get_insider_transactions as get_yfinance_insider_transactions,
)
from .yfinance_news import get_news_yfinance, get_global_news_yfinance
from .alpha_vantage import (
    get_stock as get_alpha_vantage_stock,
    get_indicator as get_alpha_vantage_indicator,
    get_fundamentals as get_alpha_vantage_fundamentals,
    get_balance_sheet as get_alpha_vantage_balance_sheet,
    get_cashflow as get_alpha_vantage_cashflow,
    get_income_statement as get_alpha_vantage_income_statement,
    get_insider_transactions as get_alpha_vantage_insider_transactions,
    get_news as get_alpha_vantage_news,
    get_global_news as get_alpha_vantage_global_news,
)

# 长桥API模块（默认选项）
from .longbridge import (
    get_stock as get_longbridge_stock,
    get_indicator as get_longbridge_indicator,
    get_fundamentals as get_longbridge_fundamentals,
    get_balance_sheet as get_longbridge_balance_sheet,
    get_cashflow as get_longbridge_cashflow,
    get_income_statement as get_longbridge_income_statement,
    get_insider_transactions as get_longbridge_insider_transactions,
    get_news as get_longbridge_news,
    get_global_news as get_longbridge_global_news,
    get_candlestick_patterns as get_longbridge_candlestick_patterns,
)

# 导入统一数据管理器
from .unified_data_manager import (
    UnifiedDataManager,
    VendorPriority,
    DataFetchError,
)

# Configuration and routing logic
from .config import get_config

# 全局统一数据管理器实例
_data_manager: UnifiedDataManager = None

def get_data_manager() -> UnifiedDataManager:
    """获取全局数据管理器实例"""
    global _data_manager
    
    if _data_manager is None:
        _data_manager = _init_data_manager()
    
    return _data_manager

def _init_data_manager() -> UnifiedDataManager:
    """初始化数据管理器"""
    manager = UnifiedDataManager(
        default_max_retries=3,
        default_retry_delay_base=1.0,
        default_retry_delay_max=10.0,
        default_rate_limit_wait=5.0,
        default_rate_limit_max_retries=5,
    )
    
    config = get_config()
    
    manager.register_vendor(
        "longbridge",
        priority=VendorPriority.PRIMARY,
        max_retries=3,
        rate_limit_wait=2.0,
    )
    
    manager.register_vendor(
        "yfinance",
        priority=VendorPriority.SECONDARY,
        max_retries=3,
        rate_limit_wait=1.0,
    )
    
    manager.register_vendor(
        "alpha_vantage",
        priority=VendorPriority.FALLBACK,
        max_retries=2,
        rate_limit_wait=12.0,
    )
    
    get_stock_data_impls = {}
    get_stock_data_impls["longbridge"] = get_longbridge_stock
    get_stock_data_impls["yfinance"] = get_YFin_data_online
    get_stock_data_impls["alpha_vantage"] = get_alpha_vantage_stock
    
    manager.register_method(
        "get_stock_data",
        get_stock_data_impls,
        ["longbridge", "yfinance", "alpha_vantage"]
    )
    
    get_indicators_impls = {}
    get_indicators_impls["longbridge"] = get_longbridge_indicator
    get_indicators_impls["yfinance"] = get_stock_stats_indicators_window
    get_indicators_impls["alpha_vantage"] = get_alpha_vantage_indicator
    
    manager.register_method(
        "get_indicators",
        get_indicators_impls,
        ["longbridge", "yfinance", "alpha_vantage"]
    )
    
    get_fundamentals_impls = {}
    get_fundamentals_impls["longbridge"] = get_longbridge_fundamentals
    get_fundamentals_impls["yfinance"] = get_yfinance_fundamentals
    get_fundamentals_impls["alpha_vantage"] = get_alpha_vantage_fundamentals
    
    manager.register_method(
        "get_fundamentals",
        get_fundamentals_impls,
        ["longbridge", "yfinance", "alpha_vantage"]
    )
    
    get_balance_sheet_impls = {}
    get_balance_sheet_impls["alpha_vantage"] = get_alpha_vantage_balance_sheet
    get_balance_sheet_impls["yfinance"] = get_yfinance_balance_sheet
    get_balance_sheet_impls["longbridge"] = get_longbridge_balance_sheet
    
    manager.register_method(
        "get_balance_sheet",
        get_balance_sheet_impls,
        ["alpha_vantage", "yfinance", "longbridge"]
    )
    
    get_cashflow_impls = {}
    get_cashflow_impls["alpha_vantage"] = get_alpha_vantage_cashflow
    get_cashflow_impls["yfinance"] = get_yfinance_cashflow
    get_cashflow_impls["longbridge"] = get_longbridge_cashflow
    
    manager.register_method(
        "get_cashflow",
        get_cashflow_impls,
        ["alpha_vantage", "yfinance", "longbridge"]
    )
    
    get_income_statement_impls = {}
    get_income_statement_impls["alpha_vantage"] = get_alpha_vantage_income_statement
    get_income_statement_impls["yfinance"] = get_yfinance_income_statement
    get_income_statement_impls["longbridge"] = get_longbridge_income_statement
    
    manager.register_method(
        "get_income_statement",
        get_income_statement_impls,
        ["alpha_vantage", "yfinance", "longbridge"]
    )
    
    get_news_impls = {}
    get_news_impls["alpha_vantage"] = get_alpha_vantage_news
    get_news_impls["yfinance"] = get_news_yfinance
    
    manager.register_method(
        "get_news",
        get_news_impls,
        ["alpha_vantage", "yfinance"]
    )
    
    get_global_news_impls = {}
    get_global_news_impls["alpha_vantage"] = get_alpha_vantage_global_news
    get_global_news_impls["yfinance"] = get_global_news_yfinance
    
    manager.register_method(
        "get_global_news",
        get_global_news_impls,
        ["alpha_vantage", "yfinance"]
    )
    
    get_insider_transactions_impls = {}
    get_insider_transactions_impls["alpha_vantage"] = get_alpha_vantage_insider_transactions
    get_insider_transactions_impls["yfinance"] = get_yfinance_insider_transactions
    
    manager.register_method(
        "get_insider_transactions",
        get_insider_transactions_impls,
        ["alpha_vantage", "yfinance"]
    )
    
    # 蜡烛图形态工具 - 注册 yfinance 作为 fallback，虽然没有实现，但会触发 unified_data_manager 的 fallback
    get_candlestick_patterns_impls = {}
    get_candlestick_patterns_impls["longbridge"] = get_longbridge_candlestick_patterns
    get_candlestick_patterns_impls["yfinance"] = get_longbridge_candlestick_patterns  # dummy, will trigger fallback
    
    manager.register_method(
        "get_candlestick_patterns",
        get_candlestick_patterns_impls,
        ["longbridge", "yfinance"]
    )
    
    return manager

def route_to_vendor(method: str, *args, **kwargs):
    """路由方法调用到统一数据管理器
    
    这是兼容旧代码的接口，新代码应该直接使用 get_data_manager()
    
    Args:
        method: 方法名称
        *args: 位置参数
        **kwargs: 关键字参数
    
    Returns:
        获取的数据
    """
    from datetime import datetime, timedelta
    
    manager = get_data_manager()
    
    if method == "get_stock_data":
        args_list = list(args)
        if len(args_list) >= 3:
            symbol, start_date, end_date = args_list[:3]
            try:
                end_dt = datetime.strptime(end_date, "%Y-%m-%d")
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                days_diff = (end_dt - start_dt).days
                
                if days_diff < 200:
                    new_start_dt = end_dt - timedelta(days=200)
                    new_start_date = new_start_dt.strftime("%Y-%m-%d")
                    args_list[1] = new_start_date
                    args = tuple(args_list)
            except Exception:
                pass
    
    return manager.fetch(method, *args, **kwargs)

def get_fetch_stats():
    """获取数据获取统计信息"""
    manager = get_data_manager()
    return manager.get_stats()

def reset_fetch_stats():
    """重置数据获取统计信息"""
    manager = get_data_manager()
    manager.reset_stats()
