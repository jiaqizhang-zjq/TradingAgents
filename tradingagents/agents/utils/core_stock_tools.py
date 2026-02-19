from langchain_core.tools import tool
from typing import Annotated
from tradingagents.dataflows.interface import route_to_vendor, get_data_manager
import sys
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
def get_stock_data(
    symbol: Annotated[str, "ticker symbol of the company"],
    start_date: Annotated[str, "Start date in yyyy-mm-dd format"],
    end_date: Annotated[str, "End date in yyyy-mm-dd format"],
) -> str:
    """
    Retrieve stock price data (OHLCV) for a given ticker symbol.
    Uses the configured core_stock_apis vendor.
    Args:
        symbol (str): Ticker symbol of the company, e.g. AAPL, TSM
        start_date (str): Start date in yyyy-mm-dd format
        end_date (str): End date in yyyy-mm-dd format
    Returns:
        str: A formatted dataframe containing the stock price data for the specified ticker symbol in the specified date range.
    """
    print(f"\n🔧 Calling get_stock_data for {symbol} ({start_date} to {end_date})...")
    
    manager = get_data_manager()
    
    result = route_to_vendor("get_stock_data", symbol, start_date, end_date)
    
    vendor_used = "unknown"
    if hasattr(manager, 'get_stats'):
        stats = manager.get_stats()
        vendor_used = stats.get('last_vendor_used', 'unknown')
    
    log_tool_call("get_stock_data", vendor_used, result)
    
    return result
