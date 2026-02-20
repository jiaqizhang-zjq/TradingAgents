#!/usr/bin/env python3

import sys
import os
from datetime import datetime

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 测试数据
test_stock_data = """
| Date       | Open   | High   | Low    | Close  | Adj Close | Volume   |
|------------|--------|--------|--------|--------|-----------|----------|
| 2026-01-22 | 95.00  | 99.90  | 94.50  | 96.57  | 96.57     | 6470000  |
| 2026-01-23 | 96.00  | 97.20  | 88.50  | 89.10  | 89.10     | 5230000  |
| 2026-01-24 | 88.50  | 90.20  | 85.00  | 86.30  | 86.30     | 4810000  |
| 2026-01-27 | 85.50  | 87.80  | 82.10  | 83.20  | 83.20     | 4250000  |
| 2026-01-28 | 82.50  | 85.00  | 79.80  | 80.50  | 80.50     | 4520000  |
| 2026-01-29 | 80.00  | 82.50  | 78.20  | 79.10  | 79.10     | 3980000  |
| 2026-01-30 | 78.50  | 80.80  | 76.50  | 77.30  | 77.30     | 3750000  |
| 2026-01-31 | 77.00  | 78.90  | 75.20  | 76.50  | 76.50     | 3420000  |
| 2026-02-03 | 76.00  | 77.50  | 74.10  | 75.20  | 75.20     | 3200000  |
| 2026-02-04 | 74.50  | 76.20  | 72.50  | 73.80  | 73.80     | 3050000  |
| 2026-02-05 | 73.00  | 75.10  | 69.50  | 70.20  | 70.20     | 4120000  |
| 2026-02-06 | 70.00  | 72.50  | 68.20  | 69.50  | 69.50     | 3850000  |
| 2026-02-07 | 69.00  | 71.20  | 66.50  | 67.80  | 67.80     | 3520000  |
| 2026-02-10 | 67.00  | 69.50  | 64.80  | 66.20  | 66.20     | 4280000  |
| 2026-02-11 | 65.50  | 68.20  | 63.50  | 64.50  | 64.50     | 4050000  |
| 2026-02-12 | 64.00  | 65.80  | 59.80  | 61.20  | 61.20     | 5870000  |
| 2026-02-13 | 61.00  | 63.50  | 60.20  | 62.80  | 62.80     | 4520000  |
| 2026-02-14 | 62.50  | 65.00  | 61.80  | 63.50  | 63.50     | 4280000  |
| 2026-02-17 | 63.00  | 66.20  | 62.10  | 64.80  | 64.80     | 4050000  |
| 2026-02-18 | 64.50  | 67.80  | 63.20  | 65.20  | 65.20     | 3920000  |
| 2026-02-19 | 64.80  | 74.85  | 61.29  | 62.06  | 62.06     | 7850000  |
"""

print("=" * 80)
print("Testing Full Candlestick Workflow")
print("=" * 80)

# 测试1: 测试直接使用我们的函数
print("\n1. Testing candlestick_tools functions directly...")
from tradingagents.agents.utils.candlestick_tools import (
    identify_candlestick_patterns,
    parse_stock_data_to_dataframe,
    format_patterns_result
)

df = parse_stock_data_to_dataframe(test_stock_data)
if df is not None:
    print("✓ Successfully parsed stock data to DataFrame")
    print(f"  - Number of records: {len(df)}")
    
    patterns = identify_candlestick_patterns(df)
    print(f"✓ Identified {len(patterns)} dates with candlestick patterns")
    
    result = format_patterns_result(patterns, "LMND", "2026-01-01", "2026-02-20")
    print("\n" + "=" * 80)
    print("Formatted result:")
    print(result)
else:
    print("✗ Failed to parse stock data")

# 测试2: 测试使用get_candlestick_patterns工具，传入预获取的stock_data
print("\n" + "=" * 80)
print("2. Testing get_candlestick_patterns tool with pre-fetched stock_data...")
from tradingagents.agents.utils.candlestick_tools import get_candlestick_patterns

try:
    result = get_candlestick_patterns.invoke({
        "symbol": "LMND",
        "start_date": "2026-01-01",
        "end_date": "2026-02-20",
        "stock_data": test_stock_data
    })
    print("✓ get_candlestick_patterns tool worked successfully!")
    print("\n" + "=" * 80)
    print("Tool output:")
    print(result)
except Exception as e:
    print(f"✗ Error: {e}")

print("\n" + "=" * 80)
print("All tests completed!")
print("=" * 80)
