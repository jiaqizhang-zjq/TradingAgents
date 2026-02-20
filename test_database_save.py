#!/usr/bin/env python3
"""
测试数据库保存功能
"""

from tradingagents.dataflows.database import AnalysisReport, get_db
from datetime import datetime
import json

def test_database():
    """测试数据库基本功能"""
    print("=" * 80)
    print("🗄️  数据库功能测试")
    print("=" * 80)
    
    db = get_db()
    
    # 测试数据
    symbol = "TEST"
    trade_date = "2025-03-20"
    
    # 创建测试报告
    report = AnalysisReport(
        symbol=symbol,
        trade_date=trade_date,
        created_at=datetime.now().isoformat(),
        market_report="# 市场分析报告\n\n这是一个测试报告。",
        fundamentals_report="# 基本面分析报告\n\n公司财务状况良好。",
        candlestick_report="# 蜡烛图分析报告\n\n技术形态看涨。",
        sentiment_report="# 情绪分析报告\n\n市场情绪积极。",
        news_report="# 新闻分析报告\n\n利好消息不断。",
        investment_plan="# 投资计划\n\n建议买入。",
        trader_investment_plan="# 交易员计划\n\n执行买入操作。",
        final_trade_decision="# 最终决策\n\nBUY",
        tool_calls_jsonl="",
        metadata=json.dumps({"test": True})
    )
    
    # 保存报告
    print(f"\n📝 正在保存测试报告: {symbol} @ {trade_date}")
    success = db.save_analysis_report(report)
    
    if success:
        print("✅ 保存成功!")
        
        # 读取报告
        print(f"\n📖 正在读取报告...")
        retrieved_report = db.get_report(symbol, trade_date)
        
        if retrieved_report:
            print("✅ 读取成功!")
            print(f"   股票代码: {retrieved_report.symbol}")
            print(f"   交易日期: {retrieved_report.trade_date}")
            print(f"   市场报告: {retrieved_report.market_report[:50]}...")
            
        # 列出所有报告
        print(f"\n📋 列出所有报告...")
        reports = db.list_reports()
        print(f"✅ 找到 {len(reports)} 条报告")
        for r in reports:
            print(f"   - {r['symbol']} @ {r['trade_date']}")
        
        # 导出 Markdown
        print(f"\n📤 正在导出 Markdown...")
        md_path = db.export_report_to_markdown(symbol, trade_date)
        if md_path:
            print(f"✅ Markdown 已导出: {md_path}")
        
    else:
        print("❌ 保存失败!")
    
    print("\n" + "=" * 80)
    print("✅ 测试完成")
    print("=" * 80)

if __name__ == "__main__":
    test_database()
