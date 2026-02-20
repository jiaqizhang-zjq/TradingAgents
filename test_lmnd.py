#!/usr/bin/env python3
"""
用LMND股票测试所有工具接口
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from tradingagents.dataflows.interface import get_data_manager

def print_result(title, result, max_lines=15):
    """打印结果"""
    print(f"\n{'='*60}")
    print(f"📊 {title}")
    print(f"{'='*60}")
    if result is None:
        print("(None)")
    elif isinstance(result, str):
        lines = result.split('\n')
        if len(lines) > max_lines:
            print('\n'.join(lines[:max_lines]))
            print(f"\n... (truncated, total {len(lines)} lines)")
        else:
            print(result)
    else:
        print(repr(result))

manager = get_data_manager()

print("="*80)
print("用 LMND 测试所有工具接口")
print("="*80)

symbol = "LMND"
today = datetime.today()
end_date = today.strftime("%Y-%m-%d")
start_date = (today - timedelta(days=30)).strftime("%Y-%m-%d")
curr_date = end_date
indicator = "close_50_sma"
look_back_days = 30

print(f"\n股票: {symbol}")
print(f"日期范围: {start_date} ~ {end_date}")

tests = [
    ("get_stock_data", [symbol, start_date, end_date], {}),
    ("get_indicators", [symbol, indicator, curr_date, look_back_days], {}),
    ("get_fundamentals", [symbol], {}),
    ("get_balance_sheet", [symbol], {}),
    ("get_cashflow", [symbol], {}),
    ("get_income_statement", [symbol], {}),
    ("get_news", [symbol, start_date, end_date], {}),
    ("get_global_news", [curr_date], {}),
    ("get_insider_transactions", [symbol], {}),
]

for method_name, args, kwargs in tests:
    print(f"\n{'='*80}")
    print(f"🔍 测试: {method_name}")
    print(f"{'='*80}")
    try:
        r = manager.fetch(method_name, *args, **kwargs)
        print(f"✅ 成功")
        print_result(f"{method_name} 结果", r)
    except Exception as e:
        print(f"❌ 失败: {e}")
        import traceback
        print(f"堆栈信息:\n{traceback.format_exc()}")

print("\n" + "="*80)
print("测试完成")
print("="*80)
