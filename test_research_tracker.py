#!/usr/bin/env python3
"""
测试 Research Tracker 胜率追踪功能
"""

from tradingagents.dataflows.research_tracker import get_research_tracker, ResearcherStats
from datetime import datetime

def test_research_tracker():
    """测试 Research Tracker 功能"""
    print("=" * 80)
    print("📊 Research Tracker 胜率追踪测试")
    print("=" * 80)
    
    tracker = get_research_tracker()
    
    # 测试数据
    symbol = "TEST"
    trade_date = "2025-03-20"
    
    # 记录 bull 研究员预测
    print(f"\n📝 记录 bull 研究员预测...")
    tracker.record_research(
        researcher_name="bull_researcher",
        researcher_type="bull",
        symbol=symbol,
        trade_date=trade_date,
        prediction="BUY",
        confidence=0.85,
        reasoning="公司业绩好，技术形态看涨"
    )
    
    # 记录 bear 研究员预测
    print(f"📝 记录 bear 研究员预测...")
    tracker.record_research(
        researcher_name="bear_researcher",
        researcher_type="bear",
        symbol=symbol,
        trade_date=trade_date,
        prediction="SELL",
        confidence=0.75,
        reasoning="市场风险高，建议观望"
    )
    
    # 记录交易员预测
    print(f"📝 记录交易员预测...")
    tracker.record_research(
        researcher_name="trader",
        researcher_type="trader",
        symbol=symbol,
        trade_date=trade_date,
        prediction="BUY",
        confidence=0.9,
        reasoning="综合分析后决定买入"
    )
    
    # 验证一些预测（模拟实际收益）
    print(f"\n✅ 验证预测结果...")
    tracker.verify_prediction(
        researcher_name="bull_researcher",
        symbol=symbol,
        trade_date=trade_date,
        actual_return=0.08  # 8% 收益
    )
    
    tracker.verify_prediction(
        researcher_name="bear_researcher",
        symbol=symbol,
        trade_date=trade_date,
        actual_return=0.08  # 8% 收益（bear 预测错误）
    )
    
    # 获取统计信息
    print(f"\n📈 获取研究员统计...")
    stats_list = tracker.get_researcher_stats()
    
    for stats in stats_list:
        print(f"\n👤 {stats.researcher_name} ({stats.researcher_type})")
        print(f"   总预测: {stats.total_predictions}")
        print(f"   正确: {stats.correct_predictions}")
        print(f"   错误: {stats.incorrect_predictions}")
        print(f"   胜率: {stats.win_rate:.2%}")
        print(f"   平均收益: {stats.avg_return:.2%}")
    
    # 获取特定股票统计
    print(f"\n📊 获取股票 {symbol} 统计...")
    symbol_stats = tracker.get_symbol_stats(symbol)
    print(f"   总预测: {symbol_stats.get('total_predictions', 0)}")
    print(f"   正确: {symbol_stats.get('correct_predictions', 0)}")
    print(f"   胜率: {symbol_stats.get('win_rate', 0):.2%}")
    
    print("\n" + "=" * 80)
    print("✅ 测试完成")
    print("=" * 80)

if __name__ == "__main__":
    test_research_tracker()
