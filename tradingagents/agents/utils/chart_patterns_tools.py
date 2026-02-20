from langchain_core.tools import tool
from typing import Annotated
from tradingagents.dataflows.interface import get_data_manager
from tradingagents.agents.utils.agent_utils import log_tool_call


@tool
def get_chart_patterns(
    symbol: Annotated[str, "ticker symbol of the company"],
    start_date: Annotated[str, "Start date (YYYY-mm-dd)"],
    end_date: Annotated[str, "End date (YYYY-mm-dd)"],
    lookback: Annotated[int, "Lookback period for pattern detection (default: 60)"] = 60,
    stock_data: Annotated[str, "Optional: pre-fetched stock data in table format"] = "",
) -> str:
    """
    Identify Western chart patterns for a given ticker symbol.
    Returns recognized patterns like:
    - HEAD_AND_SHOULDERS_TOP, HEAD_AND_SHOULDERS_BOTTOM
    - DOUBLE_TOP, DOUBLE_BOTTOM
    - ASCENDING_TRIANGLE, DESCENDING_TRIANGLE, SYMMETRICAL_TRIANGLE
    - BULL_FLAG, BEAR_FLAG
    - RISING_WEDGE, FALLING_WEDGE
    - ROUNDING_TOP, ROUNDING_BOTTOM
    - RECTANGLE
    
    All patterns include volume confirmation and breakout confirmation checks.
    
    Args:
        symbol (str): Ticker symbol of the company, e.g. AAPL, TSM
        start_date (str): Start date (YYYY-mm-dd)
        end_date (str): End date (YYYY-mm-dd)
        lookback (int): Lookback period for pattern detection (default: 60)
        stock_data (str): Optional: pre-fetched stock data in table format
    
    Returns:
        str: A formatted report containing the chart patterns for the specified ticker symbol.
    """
    print(f"\n🔧 Calling get_chart_patterns for {symbol} ({start_date} to {end_date})...")
    
    manager = get_data_manager()
    
    result = manager.fetch("get_chart_patterns", symbol, start_date, end_date, lookback)
    
    vendor_used = "local"
    if hasattr(manager, 'get_stats'):
        stats = manager.get_stats()
        vendor_used = stats.get('last_vendor_used', 'local')
    
    log_tool_call("get_chart_patterns", vendor_used, result)
    
    return result
