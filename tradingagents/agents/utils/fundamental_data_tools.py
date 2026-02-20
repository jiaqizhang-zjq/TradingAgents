from langchain_core.tools import tool
from typing import Annotated
from tradingagents.dataflows.interface import get_data_manager
from tradingagents.agents.utils.agent_utils import log_tool_call


@tool
def get_fundamentals(
    ticker: Annotated[str, "ticker symbol"],
    curr_date: Annotated[str, "current date you are trading at, yyyy-mm-dd"],
) -> str:
    """
    Retrieve comprehensive fundamental data for a given ticker symbol.
    Uses the configured fundamental_data vendor.
    Args:
        ticker (str): Ticker symbol of the company
        curr_date (str): Current date you are trading at, yyyy-mm-dd
    Returns:
        str: A formatted report containing comprehensive fundamental data
    """
    print(f"\n🔧 Calling get_fundamentals for {ticker}, date={curr_date}...")
    
    manager = get_data_manager()
    
    result = manager.fetch("get_fundamentals", ticker, curr_date)
    
    vendor_used = "unknown"
    if hasattr(manager, 'get_stats'):
        stats = manager.get_stats()
        vendor_used = stats.get('last_vendor_used', 'unknown')
    
    log_tool_call("get_fundamentals", vendor_used, result)
    
    return result


@tool
def get_balance_sheet(
    ticker: Annotated[str, "ticker symbol"],
    freq: Annotated[str, "reporting frequency: annual/quarterly"] = "quarterly",
    curr_date: Annotated[str, "current date you are trading at, yyyy-mm-dd"] = None,
) -> str:
    """
    Retrieve balance sheet data for a given ticker symbol.
    Uses the configured fundamental_data vendor.
    Args:
        ticker (str): Ticker symbol of the company
        freq (str): Reporting frequency: annual/quarterly (default quarterly)
        curr_date (str): Current date you are trading at, yyyy-mm-dd
    Returns:
        str: A formatted report containing balance sheet data
    """
    print(f"\n🔧 Calling get_balance_sheet for {ticker}, freq={freq}...")
    
    manager = get_data_manager()
    
    result = manager.fetch("get_balance_sheet", ticker, freq, curr_date)
    
    vendor_used = "unknown"
    if hasattr(manager, 'get_stats'):
        stats = manager.get_stats()
        vendor_used = stats.get('last_vendor_used', 'unknown')
    
    log_tool_call("get_balance_sheet", vendor_used, result)
    
    return result


@tool
def get_cashflow(
    ticker: Annotated[str, "ticker symbol"],
    freq: Annotated[str, "reporting frequency: annual/quarterly"] = "quarterly",
    curr_date: Annotated[str, "current date you are trading at, yyyy-mm-dd"] = None,
) -> str:
    """
    Retrieve cash flow statement data for a given ticker symbol.
    Uses the configured fundamental_data vendor.
    Args:
        ticker (str): Ticker symbol of the company
        freq (str): Reporting frequency: annual/quarterly (default quarterly)
        curr_date (str): Current date you are trading at, yyyy-mm-dd
    Returns:
        str: A formatted report containing cash flow statement data
    """
    print(f"\n🔧 Calling get_cashflow for {ticker}, freq={freq}...")
    
    manager = get_data_manager()
    
    result = manager.fetch("get_cashflow", ticker, freq, curr_date)
    
    vendor_used = "unknown"
    if hasattr(manager, 'get_stats'):
        stats = manager.get_stats()
        vendor_used = stats.get('last_vendor_used', 'unknown')
    
    log_tool_call("get_cashflow", vendor_used, result)
    
    return result


@tool
def get_income_statement(
    ticker: Annotated[str, "ticker symbol"],
    freq: Annotated[str, "reporting frequency: annual/quarterly"] = "quarterly",
    curr_date: Annotated[str, "current date you are trading at, yyyy-mm-dd"] = None,
) -> str:
    """
    Retrieve income statement data for a given ticker symbol.
    Uses the configured fundamental_data vendor.
    Args:
        ticker (str): Ticker symbol of the company
        freq (str): Reporting frequency: annual/quarterly (default quarterly)
        curr_date (str): Current date you are trading at, yyyy-mm-dd
    Returns:
        str: A formatted report containing income statement data
    """
    print(f"\n🔧 Calling get_income_statement for {ticker}, freq={freq}...")
    
    manager = get_data_manager()
    
    result = manager.fetch("get_income_statement", ticker, freq, curr_date)
    
    vendor_used = "unknown"
    if hasattr(manager, 'get_stats'):
        stats = manager.get_stats()
        vendor_used = stats.get('last_vendor_used', 'unknown')
    
    log_tool_call("get_income_statement", vendor_used, result)
    
    return result
