from typing import Annotated
import pandas as pd
import io

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

# 导入本地计算模块
from .complete_indicators import (
    CompleteTechnicalIndicators,
    CompleteCandlestickPatterns,
    ChartPatterns
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

# ========== LOCAL VENDOR 实现 ==========
def _parse_stock_data(stock_data_str):
    """解析股票数据字符串为DataFrame"""
    try:
        if 'Date' in stock_data_str and 'Open' in stock_data_str:
            lines = stock_data_str.strip().split('\n')
            filtered_lines = [line for line in lines if not line.strip().startswith('|-') and line.strip()]
            cleaned_data = '\n'.join(filtered_lines)
            
            df = pd.read_csv(io.StringIO(cleaned_data), sep='\\s*\\|\\s*', engine='python')
            
            df.columns = [col.strip() for col in df.columns if col.strip()]
            
            if 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'])
                df = df.set_index('Date')
                
                for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                
                return df
    except Exception:
        pass
    return None

def _local_get_indicators(symbol, indicator, curr_date, look_back_days, *args, **kwargs):
    """本地计算技术指标"""
    from datetime import datetime, timedelta
    
    stock_data = kwargs.get('stock_data', '')
    manager = get_data_manager()
    
    if not stock_data:
        end_date = curr_date
        start_date = (datetime.strptime(end_date, "%Y-%m-%d") - timedelta(days=look_back_days + 60)).strftime("%Y-%m-%d")
        stock_data = manager.fetch("get_stock_data", symbol, start_date, end_date)
    
    df = _parse_stock_data(stock_data)
    
    if df is None:
        raise DataFetchError("Failed to parse stock data")
    
    df_renamed = df.rename(columns={
        'Open': 'open',
        'High': 'high',
        'Low': 'low',
        'Close': 'close',
        'Volume': 'volume'
    })
    
    df_renamed.reset_index(inplace=True)
    if 'Date' in df_renamed.columns:
        df_renamed['timestamp'] = df_renamed['Date']
    elif df.index.name == 'Date':
        df_renamed['timestamp'] = df.index.strftime('%Y-%m-%d')
    
    df_with_indicators = CompleteTechnicalIndicators.calculate_all_indicators(df_renamed)
    result_df = CompleteTechnicalIndicators.get_indicator_group(df_with_indicators, indicator, look_back_days)
    
    return result_df.to_csv(index=False)


def _local_get_all_indicators(symbol, curr_date, look_back_days, *args, **kwargs):
    """本地计算所有技术指标，一次性返回所有分组"""
    from datetime import datetime, timedelta
    
    stock_data = kwargs.get('stock_data', '')
    manager = get_data_manager()
    
    if not stock_data:
        end_date = curr_date
        start_date = (datetime.strptime(end_date, "%Y-%m-%d") - timedelta(days=look_back_days + 60)).strftime("%Y-%m-%d")
        stock_data = manager.fetch("get_stock_data", symbol, start_date, end_date)
    
    df = _parse_stock_data(stock_data)
    
    if df is None:
        raise DataFetchError("Failed to parse stock data")
    
    df_renamed = df.rename(columns={
        'Open': 'open',
        'High': 'high',
        'Low': 'low',
        'Close': 'close',
        'Volume': 'volume'
    })
    
    df_renamed.reset_index(inplace=True)
    if 'Date' in df_renamed.columns:
        df_renamed['timestamp'] = df_renamed['Date']
    elif df.index.name == 'Date':
        df_renamed['timestamp'] = df.index.strftime('%Y-%m-%d')
    
    df_with_indicators = CompleteTechnicalIndicators.calculate_all_indicators(df_renamed)
    result = CompleteTechnicalIndicators.get_all_indicator_groups(df_with_indicators, look_back_days)
    
    return result

def _local_get_candlestick_patterns(symbol, start_date, end_date, *args, **kwargs):
    """本地识别蜡烛图形态"""
    from datetime import datetime, timedelta
    
    stock_data = kwargs.get('stock_data', '')
    manager = get_data_manager()
    
    if not stock_data:
        stock_data = manager.fetch("get_stock_data", symbol, start_date, end_date)
    
    df = _parse_stock_data(stock_data)
    
    if df is None:
        raise DataFetchError("Failed to parse stock data")
    
    df_renamed = df.rename(columns={
        'Open': 'open',
        'High': 'high',
        'Low': 'low',
        'Close': 'close',
        'Volume': 'volume'
    })
    
    df_renamed.reset_index(inplace=True)
    if 'Date' in df_renamed.columns:
        df_renamed['timestamp'] = df_renamed['Date']
    elif df.index.name == 'Date':
        df_renamed['timestamp'] = df.index.strftime('%Y-%m-%d')
    
    result_df = CompleteCandlestickPatterns.identify_patterns(df_renamed)
    
    if len(result_df) == 0:
        return f"No candlestick patterns identified for {symbol} in the date range {start_date} to {end_date}"
    
    patterns_result = []
    for _, row in result_df.iterrows():
        date_str = row.get('timestamp', '')
        patterns_str = row.get('patterns', '')
        volume_confirmed = row.get('volume_confirmed', False)
        
        if volume_confirmed and patterns_str:
            patterns_list = patterns_str.split('|')
            patterns_with_confirmation = [f"{p}(VOL_CONFIRMED)" for p in patterns_list]
            patterns_str = '|'.join(patterns_with_confirmation)
        elif volume_confirmed:
            patterns_str = "(VOL_CONFIRMED)"
        
        patterns_result.append({
            'Date': date_str,
            'Patterns': patterns_str.replace('|', ', '),
            'Open': round(row.get('open', 0), 2),
            'High': round(row.get('high', 0), 2),
            'Low': round(row.get('low', 0), 2),
            'Close': round(row.get('close', 0), 2)
        })
    
    result = f"# Candlestick Patterns for {symbol} ({start_date} to {end_date})\n\n"
    result += "| Date       | Patterns                                      | Open   | High   | Low    | Close  |\n"
    result += "|------------|-----------------------------------------------|--------|--------|--------|--------|\n"
    
    for p in patterns_result:
        patterns_str = p['Patterns']
        if len(patterns_str) > 45:
            patterns_str = patterns_str[:42] + "..."
        result += f"| {p['Date']} | {patterns_str:<45} | {p['Open']:>6} | {p['High']:>6} | {p['Low']:>6} | {p['Close']:>6} |\n"
    
    all_patterns = []
    for p in patterns_result:
        all_patterns.extend(p['Patterns'].split(', '))
    
    pattern_counts = {}
    for pat in all_patterns:
        pattern_counts[pat] = pattern_counts.get(pat, 0) + 1
    
    result += f"\n## Pattern Summary\n"
    result += "| Pattern                | Count |\n"
    result += "|------------------------|-------|\n"
    for pat, cnt in sorted(pattern_counts.items(), key=lambda x: -x[1]):
        result += f"| {pat:<22} | {cnt:>5} |\n"
    
    return result

def _local_get_chart_patterns(symbol, start_date, end_date, lookback=60, *args, **kwargs):
    """本地识别西方图表形态"""
    from datetime import datetime, timedelta
    
    stock_data = kwargs.get('stock_data', '')
    manager = get_data_manager()
    
    if not stock_data:
        stock_data = manager.fetch("get_stock_data", symbol, start_date, end_date)
    
    df = _parse_stock_data(stock_data)
    
    if df is None:
        raise DataFetchError("Failed to parse stock data")
    
    df_renamed = df.rename(columns={
        'Open': 'open',
        'High': 'high',
        'Low': 'low',
        'Close': 'close',
        'Volume': 'volume'
    })
    
    df_renamed.reset_index(inplace=True)
    if 'Date' in df_renamed.columns:
        df_renamed['timestamp'] = df_renamed['Date']
    elif df.index.name == 'Date':
        df_renamed['timestamp'] = df.index.strftime('%Y-%m-%d')
    
    patterns = ChartPatterns.identify_all_patterns(df_renamed, lookback)
    
    result_lines = [
        f"# Chart Patterns for {symbol}",
        "",
        "| Pattern Type | Detected | Confidence | Volume Confirmed | Breakout Confirmed | Description |",
        "|--------------|----------|------------|------------------|-------------------|-------------|"
    ]
    
    for pattern_name, pattern_info in patterns.items():
        detected = "✅" if pattern_info.get("detected", False) else "❌"
        confidence = f"{pattern_info.get('confidence', 0):.2%}"
        volume_confirmed = "✅" if pattern_info.get("volume_confirmed", False) else "❌"
        breakout_confirmed = "✅" if pattern_info.get("breakout_confirmed", False) else "❌"
        description = pattern_info.get("description", "")
        result_lines.append(f"| {pattern_name:<12} | {detected:<8} | {confidence:<10} | {volume_confirmed:<16} | {breakout_confirmed:<17} | {description} |")
    
    result_lines.extend(["", "## Detailed Pattern Information", ""])
    for pattern_name, pattern_info in patterns.items():
        if pattern_info.get("detected", False):
            result_lines.append(f"### {pattern_name}")
            for key, value in pattern_info.items():
                if key not in ["detected", "description"]:
                    result_lines.append(f"- {key}: {value}")
            result_lines.append("")
    
    return "\n".join(result_lines)

# ========== 数据管理器初始化 ==========
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
        "local",
        priority=VendorPriority.PRIMARY,
        max_retries=1,
        rate_limit_wait=0.0,
    )
    
    manager.register_vendor(
        "longbridge",
        priority=VendorPriority.SECONDARY,
        max_retries=3,
        rate_limit_wait=2.0,
    )
    
    manager.register_vendor(
        "yfinance",
        priority=VendorPriority.FALLBACK,
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
    get_indicators_impls["local"] = _local_get_indicators
    get_indicators_impls["longbridge"] = get_longbridge_indicator
    get_indicators_impls["yfinance"] = get_stock_stats_indicators_window
    get_indicators_impls["alpha_vantage"] = get_alpha_vantage_indicator
    
    manager.register_method(
        "get_indicators",
        get_indicators_impls,
        ["local", "longbridge", "yfinance", "alpha_vantage"]
    )
    
    get_all_indicators_impls = {}
    get_all_indicators_impls["local"] = _local_get_all_indicators
    
    manager.register_method(
        "get_all_indicators",
        get_all_indicators_impls,
        ["local"]
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
    
    # 蜡烛图形态工具
    get_candlestick_patterns_impls = {}
    get_candlestick_patterns_impls["local"] = _local_get_candlestick_patterns
    get_candlestick_patterns_impls["longbridge"] = get_longbridge_candlestick_patterns
    
    manager.register_method(
        "get_candlestick_patterns",
        get_candlestick_patterns_impls,
        ["local", "longbridge"]
    )
    
    # 西方图表形态工具
    get_chart_patterns_impls = {}
    get_chart_patterns_impls["local"] = _local_get_chart_patterns
    
    manager.register_method(
        "get_chart_patterns",
        get_chart_patterns_impls,
        ["local"]
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
