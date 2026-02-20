#!/usr/bin/env python3

from tradingagents.agents.utils.candlestick_tools import get_candlestick_patterns
from datetime import datetime, timedelta

# 测试LMND的蜡烛图形态
symbol = "LMND"
end_date = "2026-02-20"
start_date = "2025-08-01"

print(f"Testing candlestick pattern detection for {symbol}...")
print(f"Date range: {start_date} to {end_date}")
print("=" * 80)

result = get_candlestick_patterns.invoke({
    "symbol": symbol,
    "start_date": start_date,
    "end_date": end_date
})

print(result)
