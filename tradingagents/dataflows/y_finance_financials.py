"""Yahoo Finance financial data retrieval functions.

Provides functions to fetch fundamentals, balance sheets, cash flow,
income statements, and insider transactions via yfinance.
"""

from typing import Annotated
from datetime import datetime
import yfinance as yf


def get_fundamentals(
    ticker: Annotated[str, "ticker symbol of the company"],
    curr_date: Annotated[str, "current date (not used for yfinance)"] = None
):
    """Get company fundamentals overview from yfinance."""
    try:
        ticker_obj = yf.Ticker(ticker.upper())
        info = ticker_obj.info

        if not info:
            raise Exception(f"No fundamentals data found for symbol '{ticker}'")

        fields = [
            ("Name", info.get("longName")),
            ("Sector", info.get("sector")),
            ("Industry", info.get("industry")),
            ("Market Cap", info.get("marketCap")),
            ("PE Ratio (TTM)", info.get("trailingPE")),
            ("Forward PE", info.get("forwardPE")),
            ("PEG Ratio", info.get("pegRatio")),
            ("Price to Book", info.get("priceToBook")),
            ("EPS (TTM)", info.get("trailingEps")),
            ("Forward EPS", info.get("forwardEps")),
            ("Dividend Yield", info.get("dividendYield")),
            ("Beta", info.get("beta")),
            ("52 Week High", info.get("fiftyTwoWeekHigh")),
            ("52 Week Low", info.get("fiftyTwoWeekLow")),
            ("50 Day Average", info.get("fiftyDayAverage")),
            ("200 Day Average", info.get("twoHundredDayAverage")),
            ("Revenue (TTM)", info.get("totalRevenue")),
            ("Gross Profit", info.get("grossProfits")),
            ("EBITDA", info.get("ebitda")),
            ("Net Income", info.get("netIncomeToCommon")),
            ("Profit Margin", info.get("profitMargins")),
            ("Operating Margin", info.get("operatingMargins")),
            ("Return on Equity", info.get("returnOnEquity")),
            ("Return on Assets", info.get("returnOnAssets")),
            ("Debt to Equity", info.get("debtToEquity")),
            ("Current Ratio", info.get("currentRatio")),
            ("Book Value", info.get("bookValue")),
            ("Free Cash Flow", info.get("freeCashflow")),
        ]

        lines = []
        for label, value in fields:
            if value is not None:
                lines.append(f"{label}: {value}")

        header = f"# Company Fundamentals for {ticker.upper()}\n"
        header += f"# Data retrieved on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

        return header + "\n".join(lines)

    except Exception as e:
        raise Exception(f"Error retrieving fundamentals for {ticker}: {str(e)}")


def _fetch_financial_statement(ticker: str, data_type: str, freq: str = "quarterly") -> str:
    """Generic helper to fetch financial statement data from yfinance.
    
    Args:
        ticker: Stock ticker symbol
        data_type: One of 'balance_sheet', 'cashflow', 'income_stmt'
        freq: 'annual' or 'quarterly'
        
    Returns:
        Formatted CSV string with header
    """
    type_labels = {
        "balance_sheet": "Balance Sheet",
        "cashflow": "Cash Flow",
        "income_stmt": "Income Statement",
    }
    
    ticker_obj = yf.Ticker(ticker.upper())
    
    attr_map = {
        ("balance_sheet", "quarterly"): "quarterly_balance_sheet",
        ("balance_sheet", "annual"): "balance_sheet",
        ("cashflow", "quarterly"): "quarterly_cashflow",
        ("cashflow", "annual"): "cashflow",
        ("income_stmt", "quarterly"): "quarterly_income_stmt",
        ("income_stmt", "annual"): "income_stmt",
    }
    
    attr_name = attr_map.get((data_type, freq.lower()))
    if attr_name is None:
        raise Exception(f"Invalid data_type '{data_type}' or freq '{freq}'")
    
    data = getattr(ticker_obj, attr_name)
    
    if data.empty:
        label = type_labels.get(data_type, data_type)
        raise Exception(f"No {label} data found for symbol '{ticker}'")
    
    csv_string = data.to_csv()
    label = type_labels.get(data_type, data_type)
    header = f"# {label} data for {ticker.upper()} ({freq})\n"
    header += f"# Data retrieved on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    
    return header + csv_string


def get_balance_sheet(
    ticker: Annotated[str, "ticker symbol of the company"],
    freq: Annotated[str, "frequency of data: 'annual' or 'quarterly'"] = "quarterly",
    curr_date: Annotated[str, "current date (not used for yfinance)"] = None
):
    """Get balance sheet data from yfinance."""
    try:
        return _fetch_financial_statement(ticker, "balance_sheet", freq)
    except Exception as e:
        raise Exception(f"Error retrieving balance sheet for {ticker}: {str(e)}")


def get_cashflow(
    ticker: Annotated[str, "ticker symbol of the company"],
    freq: Annotated[str, "frequency of data: 'annual' or 'quarterly'"] = "quarterly",
    curr_date: Annotated[str, "current date (not used for yfinance)"] = None
):
    """Get cash flow data from yfinance."""
    try:
        return _fetch_financial_statement(ticker, "cashflow", freq)
    except Exception as e:
        raise Exception(f"Error retrieving cash flow for {ticker}: {str(e)}")


def get_income_statement(
    ticker: Annotated[str, "ticker symbol of the company"],
    freq: Annotated[str, "frequency of data: 'annual' or 'quarterly'"] = "quarterly",
    curr_date: Annotated[str, "current date (not used for yfinance)"] = None
):
    """Get income statement data from yfinance."""
    try:
        return _fetch_financial_statement(ticker, "income_stmt", freq)
    except Exception as e:
        raise Exception(f"Error retrieving income statement for {ticker}: {str(e)}")


def get_insider_transactions(
    ticker: Annotated[str, "ticker symbol of the company"]
):
    """Get insider transactions data from yfinance."""
    try:
        ticker_obj = yf.Ticker(ticker.upper())
        data = ticker_obj.insider_transactions
        
        if data is None or data.empty:
            raise Exception(f"No insider transactions data found for symbol '{ticker}'")
            
        csv_string = data.to_csv()
        
        header = f"# Insider Transactions data for {ticker.upper()}\n"
        header += f"# Data retrieved on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        return header + csv_string
        
    except Exception as e:
        raise Exception(f"Error retrieving insider transactions for {ticker}: {str(e)}")
