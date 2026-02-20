#!/usr/bin/env python3
"""
测试长桥API基本面数据获取
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tradingagents.dataflows.longbridge import get_longbridge_api
from tradingagents.dataflows.interface import route_to_vendor


def test_longbridge_fundamentals():
    """测试长桥API基本面数据获取"""
    print("=" * 60)
    print("测试长桥API基本面数据获取")
    print("=" * 60)
    
    symbol = "AAPL"
    
    try:
        print(f"\n1. 测试获取 {symbol} 的基本面数据...")
        api = get_longbridge_api()
        result = api.get_fundamentals(symbol)
        print("✓ 成功获取基本面数据:")
        print(result)
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("测试统一数据管理器")
    print("=" * 60)
    
    try:
        print(f"\n2. 通过统一数据管理器获取 {symbol} 的基本面数据...")
        result = route_to_vendor("get_fundamentals", symbol)
        print("✓ 成功获取基本面数据:")
        print(result)
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_longbridge_fundamentals()
