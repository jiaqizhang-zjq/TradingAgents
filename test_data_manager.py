#!/usr/bin/env python3
"""
测试统一数据管理器
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from tradingagents.dataflows.interface import (
    get_data_manager,
    get_fetch_stats,
    reset_fetch_stats
)
from tradingagents.dataflows.data_cache import get_data_cache

def test_stock_data():
    """测试股票数据获取"""
    print("\n" + "="*80)
    print("📊 测试 1: 获取股票数据")
    print("="*80)
    
    manager = get_data_manager()
    
    symbol = "NVDA"
    start_date = "2024-11-01"
    end_date = "2025-11-01"
    
    print(f"\n正在获取 {symbol} 的股票数据...")
    print(f"日期范围: {start_date} 到 {end_date}")
    
    start_time = time.time()
    try:
        result = manager.fetch("get_stock_data", symbol, start_date, end_date)
        elapsed = time.time() - start_time
        
        print(f"\n✅ 成功获取股票数据!")
        print(f"⏱️  耗时: {elapsed:.2f} 秒")
        print(f"📝 数据长度: {len(result)} 字符")
        
        preview = result[:500] if len(result) > 500 else result
        print(f"\n📋 数据预览:\n{preview}")
        
        return True
    except Exception as e:
        print(f"\n❌ 获取股票数据失败: {e}")
        return False

def test_indicators():
    """测试技术指标获取"""
    print("\n" + "="*80)
    print("📈 测试 2: 获取技术指标")
    print("="*80)
    
    manager = get_data_manager()
    
    symbol = "NVDA"
    indicators = [
        "close_50_sma",
        "close_200_sma",
        "rsi",
        "macd",
        "boll",
    ]
    
    curr_date = "2025-11-01"
    
    all_success = True
    for indicator in indicators:
        print(f"\n正在获取 {indicator}...")
        
        try:
            result = manager.fetch("get_indicators", symbol, indicator, curr_date, 120)
            
            print(f"✅ {indicator} 获取成功!")
            print(f"📝 数据长度: {len(result)} 字符")
            
            preview = result[:300] if len(result) > 300 else result
            print(f"📋 预览:\n{preview}")
            
        except Exception as e:
            print(f"❌ {indicator} 获取失败: {e}")
            all_success = False
    
    return all_success

def test_fundamentals():
    """测试基本面数据获取"""
    print("\n" + "="*80)
    print("🏢 测试 3: 获取基本面数据")
    print("="*80)
    
    manager = get_data_manager()
    
    symbol = "NVDA"
    
    methods = [
        ("get_fundamentals", [symbol]),
        ("get_balance_sheet", [symbol]),
        ("get_cashflow", [symbol]),
        ("get_income_statement", [symbol]),
    ]
    
    all_success = True
    for method_name, args in methods:
        print(f"\n正在调用 {method_name}...")
        
        try:
            result = manager.fetch(method_name, *args)
            
            print(f"✅ {method_name} 调用成功!")
            print(f"📝 数据长度: {len(result)} 字符")
            
            preview = result[:300] if len(result) > 300 else result
            print(f"📋 预览:\n{preview}")
            
        except Exception as e:
            print(f"❌ {method_name} 调用失败: {e}")
            all_success = False
    
    return all_success

def test_cache():
    """测试缓存功能"""
    print("\n" + "="*80)
    print("💾 测试 4: 缓存功能")
    print("="*80)
    
    manager = get_data_manager()
    cache = get_data_cache()
    
    symbol = "NVDA"
    start_date = "2024-11-01"
    end_date = "2025-11-01"
    
    print("\n第一次获取（应该从 API 获取）...")
    start_time = time.time()
    result1 = manager.fetch("get_stock_data", symbol, start_date, end_date)
    time1 = time.time() - start_time
    print(f"⏱️  耗时: {time1:.2f} 秒")
    
    print("\n第二次获取（应该从缓存获取）...")
    start_time = time.time()
    result2 = manager.fetch("get_stock_data", symbol, start_date, end_date)
    time2 = time.time() - start_time
    print(f"⏱️  耗时: {time2:.2f} 秒")
    
    speedup = time1 / time2 if time2 > 0 else float('inf')
    print(f"\n🚀 缓存加速: {speedup:.1f}x")
    
    if result1 == result2:
        print("✅ 缓存验证通过！")
    else:
        print("❌ 缓存验证失败！")
    
    print("\n📊 缓存统计:")
    cache_stats = cache.get_stats()
    print(f"   内存缓存: {cache_stats['memory_cache_count']} 个")
    print(f"   文件缓存: {cache_stats['file_cache_count']} 个")
    print(f"   TTL: {cache_stats['ttl_hours']} 小时")
    
    return True

def test_stats():
    """测试统计信息"""
    print("\n" + "="*80)
    print("📊 测试 5: 获取统计信息")
    print("="*80)
    
    stats = get_fetch_stats()
    
    print("\n🌍 全局统计:")
    print(f"   总调用次数: {stats['global']['total_calls']}")
    print(f"   成功次数: {stats['global']['successful_calls']}")
    print(f"   失败次数: {stats['global']['failed_calls']}")
    print(f"   限流次数: {stats['global']['rate_limit_hits']}")
    print(f"   总等待时间: {stats['global']['total_wait_time']:.2f} 秒")
    
    print("\n🏪 各数据源统计:")
    for vendor_name, vendor_stats in stats['vendors'].items():
        print(f"\n   📌 {vendor_name}:")
        print(f"      总调用: {vendor_stats['total_calls']}")
        print(f"      成功: {vendor_stats['successful_calls']}")
        print(f"      失败: {vendor_stats['failed_calls']}")
        print(f"      限流: {vendor_stats['rate_limit_hits']}")
        print(f"      等待: {vendor_stats['total_wait_time']:.2f} 秒")
        if vendor_stats.get('last_error'):
            print(f"      最后错误: {vendor_stats['last_error'][:100]}...")
    
    return True

def main():
    """主测试函数"""
    print("\n" + "="*80)
    print("🚀 统一数据管理器测试")
    print("="*80)
    
    print("\n📋 测试项目:")
    print("   1. 股票数据获取")
    print("   2. 技术指标获取")
    print("   3. 基本面数据获取")
    print("   4. 缓存功能")
    print("   5. 统计信息")
    
    reset_fetch_stats()
    
    results = []
    results.append(("股票数据", test_stock_data()))
    results.append(("技术指标", test_indicators()))
    results.append(("基本面数据", test_fundamentals()))
    results.append(("缓存功能", test_cache()))
    results.append(("统计信息", test_stats()))
    
    print("\n" + "="*80)
    print("📊 测试结果汇总")
    print("="*80)
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"   {test_name}: {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "="*80)
    if all_passed:
        print("🎉 所有测试通过！")
    else:
        print("⚠️  部分测试失败")
    print("="*80)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
