#!/usr/bin/env python3
"""
运行 LangGraph 链路并显示详细的工具调用和API来源
"""

import sys
import os
from datetime import datetime
from dotenv import load_dotenv

from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG

# Load environment variables
load_dotenv()

# 创建输出目录
OUTPUT_DIR = "langgraph_outputs_detailed"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def save_full_log(content: str, filename: str):
    """保存完整日志"""
    filepath = os.path.join(OUTPUT_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"💾 日志已保存: {filepath}")


def main():
    print("🚀 TradingAgents LangGraph 详细运行模式")
    print("=" * 120)
    
    trade_date = datetime.today().strftime("%Y-%m-%d")
    target_symbol = "LMND"
    
    print(f"📅 交易日期: {trade_date}")
    print(f"📊 目标股票: {target_symbol}")
    print(f"📁 输出目录: {os.path.abspath(OUTPUT_DIR)}")
    print("=" * 120)
    
    print("\n⚙️  正在初始化 TradingAgentsGraph...")
    
    ta = TradingAgentsGraph(
        debug=True,
        config=DEFAULT_CONFIG,
        selected_analysts=["market", "social", "news", "fundamentals", "candlestick"]
    )
    
    print("✅ 初始化完成")
    print("\n" + "=" * 120)
    print("🚀 开始执行 LangGraph 链路 (debug模式)...")
    print("=" * 120)
    
    try:
        init_state = ta.propagator.create_initial_state(target_symbol, trade_date)
        args = ta.propagator.get_graph_args()
        
        step_count = 0
        full_trace = []
        
        for chunk in ta.graph.stream(init_state, **args):
            step_count += 1
            node_name = list(chunk.keys())[0] if chunk else "Unknown"
            
            print(f"\n{'='*120}")
            print(f"📊 步骤 {step_count}: 节点 '{node_name}'")
            print(f"{'='*120}")
            
            # 保存此步骤
            step_info = {
                "step": step_count,
                "node": node_name,
                "chunk": str(chunk)[:5000]
            }
            full_trace.append(step_info)
            
            # 显示消息
            if isinstance(chunk, dict) and "messages" in chunk and chunk["messages"]:
                for i, msg in enumerate(chunk["messages"]):
                    msg_type = type(msg).__name__
                    print(f"\n📝 Message {i+1} ({msg_type}):")
                    print("-" * 120)
                    if hasattr(msg, "content"):
                        content = msg.content
                        if len(content) > 3000:
                            print(content[:3000])
                            print("\n... [内容已截断，请查看保存的完整日志]")
                        else:
                            print(content)
                    print("-" * 120)
            
            # 显示报告字段
            report_fields = [
                "market_report", "fundamentals_report", "candlestick_report",
                "sentiment_report", "news_report",
                "investment_plan", "trader_investment_plan", "final_trade_decision"
            ]
            
            for field in report_fields:
                if isinstance(chunk, dict) and field in chunk and chunk[field]:
                    print(f"\n📄 {field}:")
                    print("-" * 120)
                    report_content = str(chunk[field])
                    if len(report_content) > 2000:
                        print(report_content[:2000])
                        print("\n... [内容已截断，请查看保存的完整日志]")
                    else:
                        print(report_content)
                    print("-" * 120)
            
            # 保存当前步骤
            step_filename = f"step_{step_count:02d}_{node_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            save_full_log(str(chunk), step_filename)
            
            # 询问是否继续
            print("\n" + "-" * 120)
            while True:
                response = input("\n是否继续执行下一个节点? (y/n): ").strip().lower()
                if response in ["y", "yes", "是"]:
                    break
                elif response in ["n", "no", "否"]:
                    print("\n👋 用户取消执行")
                    return
        
        print("\n" + "=" * 120)
        print("🎉 所有节点执行完成!")
        print("=" * 120)
        
    except Exception as e:
        print(f"\n❌ 执行出错: {e}")
        import traceback
        error_log = traceback.format_exc()
        print(error_log)
        
        error_filename = f"error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        save_full_log(error_log, error_filename)
        return


if __name__ == "__main__":
    main()
