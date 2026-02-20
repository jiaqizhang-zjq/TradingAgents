#!/usr/bin/env python3
"""
从 LangGraph 输出提取数据并保存到数据库
"""

import os
import re
import json
from datetime import datetime
from pathlib import Path

from tradingagents.dataflows.database import AnalysisReport, get_db


def extract_report_from_file(filepath: str) -> dict:
    """
    从 LangGraph 输出文件中提取报告数据
    
    Args:
        filepath: 输出文件路径
        
    Returns:
        提取的报告字典
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 提取 symbol 和 trade_date
    symbol_match = re.search(r"'company_of_interest':\s*'([^']+)'", content)
    trade_date_match = re.search(r"'trade_date':\s*'([^']+)'", content)
    
    symbol = symbol_match.group(1) if symbol_match else "UNKNOWN"
    trade_date = trade_date_match.group(1) if trade_date_match else datetime.now().strftime("%Y-%m-%d")
    
    # 提取各个报告
    reports = {}
    
    # 市场报告
    market_match = re.search(r"'market_report':\s*'([^']*(?:\\.[^']*)*)'", content, re.DOTALL)
    if market_match:
        reports['market_report'] = market_match.group(1).replace('\\n', '\n').replace("\\'", "'")
    
    # 基本面报告
    fundamentals_match = re.search(r"'fundamentals_report':\s*'([^']*(?:\\.[^']*)*)'", content, re.DOTALL)
    if fundamentals_match:
        reports['fundamentals_report'] = fundamentals_match.group(1).replace('\\n', '\n').replace("\\'", "'")
    
    # 蜡烛图报告
    candlestick_match = re.search(r"'candlestick_report':\s*'([^']*(?:\\.[^']*)*)'", content, re.DOTALL)
    if candlestick_match:
        reports['candlestick_report'] = candlestick_match.group(1).replace('\\n', '\n').replace("\\'", "'")
    
    # 情绪报告
    sentiment_match = re.search(r"'sentiment_report':\s*'([^']*(?:\\.[^']*)*)'", content, re.DOTALL)
    if sentiment_match:
        reports['sentiment_report'] = sentiment_match.group(1).replace('\\n', '\n').replace("\\'", "'")
    
    # 新闻报告
    news_match = re.search(r"'news_report':\s*'([^']*(?:\\.[^']*)*)'", content, re.DOTALL)
    if news_match:
        reports['news_report'] = news_match.group(1).replace('\\n', '\n').replace("\\'", "'")
    
    # 投资计划
    investment_match = re.search(r"'investment_plan':\s*'([^']*(?:\\.[^']*)*)'", content, re.DOTALL)
    if investment_match:
        reports['investment_plan'] = investment_match.group(1).replace('\\n', '\n').replace("\\'", "'")
    
    # 交易员计划
    trader_match = re.search(r"'trader_investment_plan':\s*'([^']*(?:\\.[^']*)*)'", content, re.DOTALL)
    if trader_match:
        reports['trader_investment_plan'] = trader_match.group(1).replace('\\n', '\n').replace("\\'", "'")
    
    # 最终决策
    final_match = re.search(r"'final_trade_decision':\s*'([^']*(?:\\.[^']*)*)'", content, re.DOTALL)
    if final_match:
        reports['final_trade_decision'] = final_match.group(1).replace('\\n', '\n').replace("\\'", "'")
    
    return {
        'symbol': symbol,
        'trade_date': trade_date,
        'reports': reports,
        'raw_content': content
    }


def parse_tool_calls_from_log(log_filepath: str) -> list:
    """
    从工具调用日志中解析数据
    
    Args:
        log_filepath: 工具调用日志路径
        
    Returns:
        工具调用记录列表
    """
    if not os.path.exists(log_filepath):
        return []
    
    with open(log_filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    tool_calls = []
    
    # 分割每个工具调用记录
    entries = re.split(r'={80,}', content)
    
    for entry in entries:
        if not entry.strip():
            continue
        
        # 提取工具名称
        tool_match = re.search(r'\[.*?\]\s*🔧\s*Tool:\s*(\w+)', entry)
        if tool_match:
            tool_name = tool_match.group(1)
        else:
            continue
        
        # 提取 vendor
        vendor_match = re.search(r'Vendor Used:\s*(\S+)', entry)
        vendor_used = vendor_match.group(1) if vendor_match else "unknown"
        
        # 提取结果预览
        result_match = re.search(r'Result Preview:\s*\n(.*)', entry, re.DOTALL)
        result = result_match.group(1).strip() if result_match else ""
        
        tool_calls.append({
            'tool_name': tool_name,
            'vendor_used': vendor_used,
            'result': result
        })
    
    return tool_calls


def save_langgraph_output_to_db(output_dir: str = "langgraph_outputs_detailed",
                                 tool_calls_log: str = "langgraph_outputs/tool_calls.log"):
    """
    将 LangGraph 输出保存到数据库
    
    Args:
        output_dir: LangGraph 输出目录
        tool_calls_log: 工具调用日志路径
    """
    db = get_db()
    
    # 找到最新的 step 文件
    step_files = sorted(Path(output_dir).glob("step_*_messages_*.txt"))
    
    if not step_files:
        print(f"❌ 未找到输出文件: {output_dir}")
        return
    
    # 使用最后一个文件（包含完整结果）
    latest_file = step_files[-1]
    print(f"📄 正在处理文件: {latest_file}")
    
    # 提取报告数据
    data = extract_report_from_file(str(latest_file))
    
    symbol = data['symbol']
    trade_date = data['trade_date']
    reports = data['reports']
    
    print(f"📊 提取到报告: {symbol} @ {trade_date}")
    print(f"   - 市场报告: {'✅' if reports.get('market_report') else '❌'}")
    print(f"   - 基本面报告: {'✅' if reports.get('fundamentals_report') else '❌'}")
    print(f"   - 蜡烛图报告: {'✅' if reports.get('candlestick_report') else '❌'}")
    print(f"   - 情绪报告: {'✅' if reports.get('sentiment_report') else '❌'}")
    print(f"   - 新闻报告: {'✅' if reports.get('news_report') else '❌'}")
    print(f"   - 投资计划: {'✅' if reports.get('investment_plan') else '❌'}")
    print(f"   - 交易员计划: {'✅' if reports.get('trader_investment_plan') else '❌'}")
    print(f"   - 最终决策: {'✅' if reports.get('final_trade_decision') else '❌'}")
    
    # 解析工具调用
    tool_calls = parse_tool_calls_from_log(tool_calls_log)
    print(f"🔧 提取到 {len(tool_calls)} 条工具调用记录")
    
    # 保存工具调用到数据库
    for call in tool_calls:
        db.save_tool_call(
            symbol=symbol,
            trade_date=trade_date,
            tool_name=call['tool_name'],
            vendor_used=call['vendor_used'],
            input_params={},  # 可以从日志中提取
            result=call['result']
        )
    
    # 将工具调用转换为 JSONL 格式
    tool_calls_jsonl = '\n'.join([json.dumps(call, ensure_ascii=False) for call in tool_calls])
    
    # 创建报告对象
    report = AnalysisReport(
        symbol=symbol,
        trade_date=trade_date,
        created_at=datetime.now().isoformat(),
        market_report=reports.get('market_report', ''),
        fundamentals_report=reports.get('fundamentals_report', ''),
        candlestick_report=reports.get('candlestick_report', ''),
        sentiment_report=reports.get('sentiment_report', ''),
        news_report=reports.get('news_report', ''),
        investment_plan=reports.get('investment_plan', ''),
        trader_investment_plan=reports.get('trader_investment_plan', ''),
        final_trade_decision=reports.get('final_trade_decision', ''),
        tool_calls_jsonl=tool_calls_jsonl,
        metadata=json.dumps({
            'source_file': str(latest_file),
            'tool_calls_count': len(tool_calls)
        })
    )
    
    # 保存到数据库
    success = db.save_analysis_report(report)
    
    if success:
        print(f"\n✅ 数据已成功保存到数据库!")
        print(f"   Key: {symbol}_{trade_date}")
        
        # 导出 Markdown 和 JSONL
        print("\n📤 导出文件...")
        md_path = db.export_report_to_markdown(symbol, trade_date)
        jsonl_path = db.export_tool_calls_to_jsonl(symbol, trade_date)
        
        return {
            'symbol': symbol,
            'trade_date': trade_date,
            'db_saved': True,
            'markdown_path': md_path,
            'jsonl_path': jsonl_path
        }
    else:
        print(f"\n❌ 保存失败")
        return None


def main():
    """主函数"""
    print("=" * 80)
    print("🗄️  LangGraph 输出数据库存储工具")
    print("=" * 80)
    
    result = save_langgraph_output_to_db()
    
    if result:
        print("\n" + "=" * 80)
        print("📋 总结")
        print("=" * 80)
        print(f"股票: {result['symbol']}")
        print(f"日期: {result['trade_date']}")
        print(f"Markdown 报告: {result['markdown_path']}")
        print(f"JSONL 工具记录: {result['jsonl_path']}")
        print("=" * 80)


if __name__ == "__main__":
    main()
