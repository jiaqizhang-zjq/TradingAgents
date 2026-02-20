#!/usr/bin/env python3
"""调试 _parse_stock_data 函数"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from tradingagents.dataflows.interface import get_data_manager, _parse_stock_data

def test():
    print("="*80)
    print("测试 _parse_stock_data")
    print("="*80)
    
    manager = get_data_manager()
    stock_data = manager.fetch("get_stock_data", "LMND", "2025-08-04", "2026-02-20")
    
    print(f"\n股票数据长度: {len(stock_data)}")
    print(f"\n前500字符:\n{stock_data[:500]}")
    
    print("\n" + "="*80)
    print("调用 _parse_stock_data...")
    print("="*80)
    
    df = _parse_stock_data(stock_data)
    
    if df is not None:
        print(f"\n✅ 解析成功!")
        print(f"Shape: {df.shape}")
        print(f"Columns: {list(df.columns)}")
        print(f"\n前5行:\n{df.head()}")
    else:
        print(f"\n❌ 解析失败!")

if __name__ == "__main__":
    test()
