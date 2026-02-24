from langchain_core.messages import HumanMessage, RemoveMessage
from datetime import datetime, timedelta


def is_market_open(symbol: str = "AAPL", target_date: str = None) -> bool:
    """通过获取股票数据判断是否开盘"""
    from tradingagents.dataflows.interface import get_data_manager
    from tradingagents.dataflows.unified_data_manager import UnifiedDataManager
    data_manager = get_data_manager()
    
    target = datetime.strptime(target_date, "%Y-%m-%d") if target_date else datetime.now()
    start_date = (target - timedelta(days=5)).strftime("%Y-%m-%d")
    end_date = target.strftime("%Y-%m-%d")
    
    try:
        if isinstance(data_manager, UnifiedDataManager):
            result = data_manager.fetch("get_stock_data", symbol, start_date, end_date, no_cache=True)
        else:
            result = data_manager.get_stock_data(symbol, start_date=start_date, end_date=end_date)
        
        if result is None:
            return False
        # result 可能是字符串或DataFrame
        import pandas as pd
        if isinstance(result, str):
            from io import StringIO
            df = pd.read_csv(StringIO(result))
        else:
            df = result
            
        if df is None or len(df) == 0:
            return False
        # 检查最新日期 (CSV返回的需要排序)
        df = df.sort_values('timestamp')
        latest_date = str(df['timestamp'].iloc[-1])[:10]
        return latest_date == end_date
    except Exception as e:
        print(f"is_market_open error: {e}")
        return False


# Import tools from separate utility files
from tradingagents.agents.utils.core_stock_tools import (
    get_stock_data
)
from tradingagents.agents.utils.technical_indicators_tools import (
    get_indicators,
    get_all_indicators
)
from tradingagents.agents.utils.fundamental_data_tools import (
    get_fundamentals,
    get_balance_sheet,
    get_cashflow,
    get_income_statement
)
from tradingagents.agents.utils.news_data_tools import (
    get_news,
    get_insider_transactions,
    get_global_news,
    get_social_media_data
)
from tradingagents.agents.utils.candlestick_tools import (
    get_candlestick_patterns
)
from tradingagents.agents.utils.chart_patterns_tools import (
    get_chart_patterns
)
from tradingagents.agents.utils.logging_utils import log_tool_call

def create_msg_delete():
    def delete_messages(state):
        """Clear messages and add placeholder for Anthropic compatibility"""
        messages = state["messages"]

        # Remove all messages
        removal_operations = [RemoveMessage(id=m.id) for m in messages]

        # Add a minimal placeholder message
        placeholder = HumanMessage(content="Continue")

        return {"messages": removal_operations + [placeholder]}

    return delete_messages


        