from langchain_core.tools import tool
from typing import Annotated
from tradingagents.dataflows.interface import route_to_vendor, get_data_manager
from datetime import datetime


def log_tool_call(tool_name: str, vendor_used: str, result: str):
    """记录工具调用信息"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_file = "langgraph_outputs/tool_calls.log"
    
    log_entry = f"\n{'='*100}\n"
    log_entry += f"[{timestamp}] 🔧 Tool: {tool_name}\n"
    log_entry += f"          📊 Vendor Used: {vendor_used}\n"
    log_entry += f"          📄 Result Preview:\n"
    log_entry += f"{result[:500]}{'...' if len(result) > 500 else ''}\n"
    log_entry += f"{'='*100}\n"
    
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(log_entry)
    
    print(f"\n🔧 [TOOL CALL] {tool_name} (Vendor: {vendor_used})")


@tool
def get_indicators(
    symbol: Annotated[str, "ticker symbol of the company"],
    indicator: Annotated[str, "technical indicator to get the analysis and report of"],
    curr_date: Annotated[str, "The current trading date you are trading on, YYYY-mm-dd"],
    look_back_days: Annotated[int, "how many days to look back"] = 30,
) -> str:
    """
    Retrieve technical indicators for a given ticker symbol.
    Uses the configured technical_indicators vendor.
    Args:
        symbol (str): Ticker symbol of the company, e.g. AAPL, TSM
        indicator (str): Technical indicator to get the analysis and report of
        curr_date (str): The current trading date you are trading on, YYYY-mm-dd
        look_back_days (int): How many days to look back, default is 30
    Returns:
        str: A formatted dataframe containing the technical indicators for the specified ticker symbol and indicator.
    """
    print(f"\n🔧 Calling get_indicators for {symbol}, indicator={indicator}, date={curr_date}...")
    
    manager = get_data_manager()
    
    result = route_to_vendor("get_indicators", symbol, indicator, curr_date, look_back_days)
    
    vendor_used = "unknown"
    if hasattr(manager, 'get_stats'):
        stats = manager.get_stats()
        vendor_used = stats.get('last_vendor_used', 'unknown')
    
    log_tool_call("get_indicators", vendor_used, result)
    
    return result