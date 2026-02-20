#!/usr/bin/env python3

import json
import pandas as pd
import io
from tradingagents.agents.utils.candlestick_tools import identify_candlestick_patterns

# 读取已保存的完整状态文件
with open("eval_results/LMND/TradingAgentsStrategy_logs/full_states_log_2026-02-20.json", "r") as f:
    data = json.load(f)

print("=" * 80)
print("Testing candlestick pattern identification with saved data")
print("=" * 80)

# 首先，让我们查看一下 get_stock_data 工具返回的格式
# 让我们创建一个测试用的DataFrame
test_data = """
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

print("\n" + "=" * 80)
print("Test data:")
print(test_data)
print("=" * 80)

# 解析数据
lines = test_data.strip().split('\n')
# 过滤掉分隔线
filtered_lines = [line for line in lines if not line.strip().startswith('|-') and line.strip()]
cleaned_data = '\n'.join(filtered_lines)

df = pd.read_csv(io.StringIO(cleaned_data), sep='\s*\|\s*', engine='python')

# 清理列名
df.columns = [col.strip() for col in df.columns if col.strip()]

# 转换日期列为datetime并设为索引
if 'Date' in df.columns:
    df['Date'] = pd.to_datetime(df['Date'], format='%Y-%m-%d')
    df = df.set_index('Date')
    
    # 确保OHLC列是数值类型
    for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    print("\n" + "=" * 80)
    print("DataFrame parsed successfully:")
    print(df)
    print("=" * 80)
    
    # 识别蜡烛图形态
    patterns = identify_candlestick_patterns(df)
    
    print("\n" + "=" * 80)
    print("Identified candlestick patterns:")
    print("=" * 80)
    
    if patterns:
        result = "| Date       | Patterns                                      | Open   | High   | Low    | Close  |\n"
        result += "|------------|-----------------------------------------------|--------|--------|--------|--------|\n"
        
        for p in patterns:
            patterns_str = p['Patterns']
            if len(patterns_str) > 45:
                patterns_str = patterns_str[:42] + "..."
            result += f"| {p['Date']} | {patterns_str:<45} | {p['Open']:>6} | {p['High']:>6} | {p['Low']:>6} | {p['Close']:>6} |\n"
        
        # 汇总所有发现的形态
        all_patterns = []
        for p in patterns:
            all_patterns.extend(p['Patterns'].split(', '))
        
        pattern_counts = {}
        for pat in all_patterns:
            pattern_counts[pat] = pattern_counts.get(pat, 0) + 1
        
        result += f"\n## Pattern Summary\n"
        result += "| Pattern                | Count |\n"
        result += "|------------------------|-------|\n"
        for pat, cnt in sorted(pattern_counts.items(), key=lambda x: -x[1]):
            result += f"| {pat:<22} | {cnt:>5} |\n"
        
        print(result)
    else:
        print("No candlestick patterns identified")

print("\n" + "=" * 80)
print("Test completed!")
print("=" * 80)
