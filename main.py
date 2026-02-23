from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG
from datetime import datetime, timedelta

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# 使用2026-02-23的日期
trade_date = "2026-02-23"

# Initialize with default config (已配置 Opencode minimax-m2.5-free 和 longbridge)
ta = TradingAgentsGraph(
    debug=True, 
    config=DEFAULT_CONFIG,
    selected_analysts=["market", "social", "news", "fundamentals", "candlestick"]
)

# forward propagate
_, decision = ta.propagate("LMND", trade_date)
print(decision)

# Memorize mistakes and reflect
# ta.reflect_and_remember(1000) # parameter is the position returns
