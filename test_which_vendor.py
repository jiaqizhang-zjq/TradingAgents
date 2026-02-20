#!/usr/bin/env python3
"""
测试每个方法实际使用哪个数据源
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from tradingagents.dataflows.interface import get_data_manager

symbol = "LMND"
today = datetime.today()
end_date = today.strftime("%Y-%m-%d")
start_date = (today - timedelta(days=30)).strftime("%Y-%m-%d")
curr_date = end_date
indicator = "close_50_sma"
look_back_days = 30

print("="*80)
print("测试每个方法实际使用的数据源")
print("="*80)
print(f"股票: {symbol}")
print(f"日期范围: {start_date} ~ {end_date}")

from tradingagents.dataflows.unified_data_manager import VendorConfig
from tradingagents.dataflows.interface import _init_data_manager

# 获取配置信息
manager = _init_data_manager()

print("\n" + "="*80)
print("方法优先级配置:")
print("="*80)

methods = [
    "get_stock_data",
    "get_indicators",
    "get_fundamentals",
    "get_balance_sheet",
    "get_cashflow",
    "get_income_statement",
    "get_news",
    "get_global_news",
    "get_insider_transactions",
]

for method in methods:
    if method in manager.method_vendors:
        print(f"\n{method}:")
        print(f"  优先级: {manager.method_vendors[method]}")

print("\n" + "="*80)
print("实际测试结果:")
print("="*80)

# 重置统计
manager.reset_stats()

# 1. get_stock_data
print("\n1. get_stock_data...")
try:
    r = manager.fetch("get_stock_data", symbol, start_date, end_date)
    print("   ✅ 成功")
    # 通过返回格式判断
    if r.startswith("timestamp,"):
        print("   📊 数据源: longbridge (CSV格式)")
    elif isinstance(r, dict):
        print("   📊 数据源: alpha_vantage (JSON格式)")
except Exception as e:
    print(f"   ❌ 失败: {e}")

# 2. get_indicators
print("\n2. get_indicators...")
try:
    r = manager.fetch("get_indicators", symbol, indicator, curr_date, look_back_days)
    print("   ✅ 成功")
    # 通过返回格式判断
    if r.startswith("timestamp,"):
        print("   📊 数据源: longbridge (CSV格式)")
    elif "##" in r:
        print("   📊 数据源: yfinance/alpha_vantage (文本格式)")
except Exception as e:
    print(f"   ❌ 失败: {e}")

# 3. get_fundamentals
print("\n3. get_fundamentals...")
try:
    r = manager.fetch("get_fundamentals", symbol)
    print("   ✅ 成功")
    if isinstance(r, (dict, str)) and "Symbol" in str(r):
        print("   📊 数据源: alpha_vantage (JSON格式)")
except Exception as e:
    print(f"   ❌ 失败: {e}")

print("\n" + "="*80)
print("统计信息:")
print("="*80)
stats = manager.get_stats()
for vendor, v_stats in stats["vendors"].items():
    print(f"\n{vendor}:")
    print(f"  成功: {v_stats['successful_calls']}")
    print(f"  失败: {v_stats['failed_calls']}")
