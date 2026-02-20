from langchain_core.tools import tool
from typing import Annotated
from tradingagents.dataflows.interface import get_data_manager
from tradingagents.agents.utils.agent_utils import log_tool_call


@tool
def get_indicators(
    symbol: Annotated[str, "ticker symbol of the company"],
    indicator: Annotated[str, "technical indicator to get the analysis and report of"],
    curr_date: Annotated[str, "The current trading date you are trading on, YYYY-mm-dd"],
    look_back_days: Annotated[int, "how many days to look back"] = 30,
    stock_data: Annotated[str, "Optional: pre-fetched stock data in table format"] = "",
) -> str:
    """
    Retrieve technical indicators for a given ticker symbol.
    Uses UnifiedDataManager for consistent data management.
    Args:
        symbol (str): Ticker symbol of the company, e.g. AAPL, TSM
        indicator (str): Technical indicator to get the analysis and report of
        curr_date (str): The current trading date you are trading on, YYYY-mm-dd
        look_back_days (int): How many days to look back, default is 30
        stock_data (str): Optional: pre-fetched stock data in table format
    Returns:
        str: A formatted dataframe containing the technical indicators for the specified ticker symbol and indicator.
    """
    print(f"\n🔧 Calling get_indicators for {symbol}, indicator={indicator}, date={curr_date}...")
    
    manager = get_data_manager()
    
    result = manager.fetch("get_indicators", symbol, indicator, curr_date, look_back_days, stock_data)
    
    vendor_used = "local"
    if hasattr(manager, 'get_stats'):
        stats = manager.get_stats()
        vendor_used = stats.get('last_vendor_used', 'local')
    
    log_tool_call("get_indicators", vendor_used, result)
    
    return result


@tool
def get_all_indicators(
    symbol: Annotated[str, "ticker symbol of the company"],
    curr_date: Annotated[str, "The current trading date you are trading on, YYYY-mm-dd"],
    look_back_days: Annotated[int, "how many days to look back"] = 120,
    stock_data: Annotated[str, "Optional: pre-fetched stock data in table format"] = "",
) -> str:
    """
    Retrieve all technical indicator groups for a given ticker symbol.
    Uses UnifiedDataManager for consistent data management.
    Args:
        symbol (str): Ticker symbol of the company, e.g. AAPL, TSM
        curr_date (str): The current trading date you are trading on, YYYY-mm-dd
        look_back_days (int): How many days to look back, default is 120
        stock_data (str): Optional: pre-fetched stock data in table format
    Returns:
        str: A formatted string containing all technical indicator groups
    """
    print(f"\n🔧 Calling get_all_indicators for {symbol}, date={curr_date}...")
    
    manager = get_data_manager()
    
    result = manager.fetch("get_all_indicators", symbol, curr_date, look_back_days, stock_data)
    
    vendor_used = "local"
    if hasattr(manager, 'get_stats'):
        stats = manager.get_stats()
        vendor_used = stats.get('last_vendor_used', 'local')
    
    log_tool_call("get_all_indicators", vendor_used, result)
    
    return result