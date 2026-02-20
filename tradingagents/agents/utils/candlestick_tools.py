from langchain_core.tools import tool
from typing import Annotated
from tradingagents.dataflows.interface import get_data_manager
from tradingagents.agents.utils.logging_utils import log_tool_call


@tool
def get_candlestick_patterns(
    symbol: Annotated[str, "ticker symbol of the company"],
    start_date: Annotated[str, "Start date (YYYY-mm-dd)"],
    end_date: Annotated[str, "End date (YYYY-mm-dd)"],
    stock_data: Annotated[str, "Optional: pre-fetched stock data in table format"] = "",
) -> str:
    """
    Identify candlestick patterns for a given ticker symbol.
    Returns recognized patterns like:
    - BULLISH_ENGULFING, BEARISH_ENGULFING
    - HAMMER, HANGING_MAN
    - DOJI
    - MORNING_STAR, EVENING_STAR
    - THREE_BLACK_CROWS, THREE_WHITE_SOLDIERS
    
    Args:
        symbol (str): Ticker symbol of the company, e.g. AAPL, TSM
        start_date (str): Start date (YYYY-mm-dd)
        end_date (str): End date (YYYY-mm-dd)
        stock_data (str): Optional: pre-fetched stock data in table format
    
    Returns:
        str: A formatted dataframe containing the candlestick patterns for the specified ticker symbol.
    """
    print(f"\n🔧 Calling get_candlestick_patterns for {symbol} ({start_date} to {end_date})...")
    
    manager = get_data_manager()
    
    result = manager.fetch("get_candlestick_patterns", symbol, start_date, end_date)
    
    vendor_used = "local"
    if hasattr(manager, 'get_stats'):
        stats = manager.get_stats()
        vendor_used = stats.get('last_vendor_used', 'local')
    
    log_tool_call("get_candlestick_patterns", vendor_used, result)
    
    return result
