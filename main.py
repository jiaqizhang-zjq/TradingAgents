from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG
from datetime import datetime, timedelta

from dotenv import load_dotenv

import sys

# Load environment variables from .env file
load_dotenv()

# 使用命令行参数或默认日期
if len(sys.argv) >= 3:
    trade_date = sys.argv[2]
else:
    trade_date = "2026-02-24"

if len(sys.argv) >= 2:
    ticker = sys.argv[1]
else:
    ticker = "LMND"

# Initialize with default config (已配置 Opencode minimax-m2.5-free 和 longbridge)
ta = TradingAgentsGraph(
    debug=True, 
    config=DEFAULT_CONFIG,
    selected_analysts=["market", "social", "news", "fundamentals", "candlestick"]
)

# forward propagate
_, decision = ta.propagate(ticker, trade_date)
print(decision)

# Memorize mistakes and reflect
# ta.reflect_and_remember(1000) # parameter is the position returns
