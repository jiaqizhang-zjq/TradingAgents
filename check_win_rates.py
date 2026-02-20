#!/usr/bin/env python3
"""
查看研究员胜率统计
"""

import sys
from tradingagents.dataflows.research_tracker import get_research_tracker

def check_win_rates(symbol: str = None, researcher_type: str = None):
    """
    查看胜率统计
    
    Args:
        symbol: 按股票筛选
        researcher_type: 按研究员类型筛选
    """
    print("=" * 80)
    print("📊 研究员胜率统计")
    print("=" * 80)
    
    tracker = get_research_tracker()
    
    # 获取研究员统计
    stats_list = tracker.get_researcher_stats(
        symbol=symbol,
        researcher_type=researcher_type
    )
    
    if not stats_list:
        print("\n❌ 没有找到统计数据")
        return
    
    print(f"\n📈 找到 {len(stats_list)} 位研究员\n")
    
    for stats in stats_list:
        print("─" * 80)
        print(f"👤 {stats.researcher_name}")
        print(f"   类型: {stats.researcher_type}")
        print()
        print(f"📊 预测统计:")
        print(f"   总预测: {stats.total_predictions}")
        print(f"   ✅ 正确: {stats.correct_predictions}")
        print(f"   ❌ 错误: {stats.incorrect_predictions}")
        print(f"   ⚠️  部分正确: {stats.partial_predictions}")
        print(f"   ⏳ 待验证: {stats.pending_predictions}")
        print()
        
        verified = stats.correct_predictions + stats.incorrect_predictions + stats.partial_predictions
        if verified > 0:
            print(f"🏆 胜率统计:")
            print(f"   总胜率: {stats.win_rate:.2%}")
            print()
            print(f"💰 收益统计:")
            print(f"   平均收益: {stats.avg_return:.2%}")
            print(f"   最大收益: {stats.max_return:.2%}")
            print(f"   最小收益: {stats.min_return:.2%}")
        else:
            print(f"⚠️  暂无已验证的预测")
        
        if stats.symbols_traded:
            print()
            print(f"📈 交易过的股票: {', '.join(stats.symbols_traded)}")
    
    # 如果指定了股票，显示股票统计
    if symbol:
        print("\n" + "=" * 80)
        print(f"📊 股票 {symbol} 统计")
        print("=" * 80)
        
        symbol_stats = tracker.get_symbol_stats(symbol, researcher_type)
        if symbol_stats:
            print(f"\n   总预测: {symbol_stats.get('total_predictions', 0)}")
            print(f"   正确: {symbol_stats.get('correct_predictions', 0)}")
            print(f"   胜率: {symbol_stats.get('win_rate', 0):.2%}")
            print(f"   平均收益: {symbol_stats.get('avg_return', 0):.2%}")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    symbol = sys.argv[1] if len(sys.argv) > 1 else None
    researcher_type = sys.argv[2] if len(sys.argv) > 2 else None
    
    check_win_rates(symbol, researcher_type)
