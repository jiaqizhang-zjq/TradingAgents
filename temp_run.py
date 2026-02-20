#!/usr/bin/env python3
"""
交互式逐步运行 LangGraph 链路
每执行完一个节点，先告诉用户，等用户同意后再往下继续
每步结果保存到文件中供人工检查
"""

import sys
import os
import json
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG

# Load environment variables
load_dotenv()

# 创建输出目录
OUTPUT_DIR = Path("langgraph_outputs")
OUTPUT_DIR.mkdir(exist_ok=True)


def save_step_output(step_count: int, node_name: str, chunk: Any):
    """
    保存步骤输出到文件
    
    Args:
        step_count: 步骤编号
        node_name: 节点名称
        chunk: 节点输出
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = OUTPUT_DIR / f"step_{step_count:02d}_{node_name.replace(' ', '_')}_{timestamp}.json"
    
    output_data = {
        "step_count": step_count,
        "node_name": node_name,
        "timestamp": timestamp,
        "chunk": {}
    }
    
    if isinstance(chunk, dict):
        for key, value in chunk.items():
            if key == "messages":
                output_data["chunk"]["messages"] = []
                for msg in value:
                    msg_dict = {
                        "type": type(msg).__name__,
                        "content": msg.content if hasattr(msg, "content") else str(msg),
                    }
                    if hasattr(msg, "tool_calls"):
                        msg_dict["tool_calls"] = str(msg.tool_calls)
                    output_data["chunk"]["messages"].append(msg_dict)
            elif key in ["investment_debate_state", "risk_debate_state"]:
                output_data["chunk"][key] = dict(value) if hasattr(value, "items") else str(value)
            else:
                output_data["chunk"][key] = str(value)[:5000] if isinstance(value, str) else str(value)
    
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 结果已保存到: {filename}")
    
    # 同时保存一份纯文本格式
    txt_filename = OUTPUT_DIR / f"step_{step_count:02d}_{node_name.replace(' ', '_')}_{timestamp}.txt"
    with open(txt_filename, "w", encoding="utf-8") as f:
        f.write(f"=== Step {step_count}: {node_name} ===\n")
        f.write(f"Timestamp: {timestamp}\n\n")
        
        if isinstance(chunk, dict):
            for key, value in chunk.items():
                if key == "messages" and value:
                    f.write(f"--- Messages ---\n")
                    for i, msg in enumerate(value):
                        f.write(f"\nMessage {i+1} ({type(msg).__name__}):\n")
                        if hasattr(msg, "content"):
                            f.write(msg.content)
                            f.write("\n")
                elif key in ["market_report", "fundamentals_report", "candlestick_report", 
                           "investment_plan", "trader_investment_plan", "final_trade_decision",
                           "sentiment_report", "news_report"]:
                    f.write(f"\n--- {key} ---\n")
                    f.write(str(value))
                    f.write("\n")
    
    print(f"💾 文本格式已保存到: {txt_filename}")


def step_prompt(step_count: int, node_name: str, chunk: Any = None) -> bool:
    """
    询问用户是否继续执行下一步
    
    Args:
        step_count: 步骤编号
        node_name: 节点名称
        chunk: 节点输出
        
    Returns:
        True 表示继续，False 表示停止
    """
    print("\n" + "=" * 120)
    print(f"✅ 步骤 {step_count} - 节点执行完成: {node_name}")
    print("=" * 120)
    
    # 保存输出
    save_step_output(step_count, node_name, chunk)
    
    if chunk and isinstance(chunk, dict):
        # 显示关键信息
        if "messages" in chunk and chunk["messages"]:
            last_msg = chunk["messages"][-1]
            print(f"\n📝 最后一条消息预览:")
            print("-" * 120)
            if hasattr(last_msg, "content"):
                content = last_msg.content
                if len(content) > 2000:
                    print(content[:2000] + "\n...\n[内容已截断，请查看保存的文件]")
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
            if field in chunk and chunk[field]:
                print(f"\n📄 {field} 已生成")
    
    print("\n" + "-" * 120)
    
    while True:
        return True  # 自动继续
        response = input("\n是否继续执行下一个节点? (y/n): ").strip().lower()
        if response in ["y", "yes", "是"]:
            return True
        elif response in ["n", "no", "否"]:
            return False
        else:
            print("请输入 y (继续) 或 n (停止)")


def run_interactive_steps():
    """交互式逐步运行 LangGraph 链路"""
    print("🚀 TradingAgents LangGraph 交互式逐步运行")
    print("=" * 120)
    
    # 使用今天的日期
    trade_date = datetime.today().strftime("%Y-%m-%d")
    target_symbol = "LMND"
    
    print(f"📅 交易日期: {trade_date}")
    print(f"📊 目标股票: {target_symbol}")
    print(f"📁 输出目录: {OUTPUT_DIR.absolute()}")
    print("=" * 120)
    
    # 初始化
    print("\n⚙️  正在初始化 TradingAgentsGraph...")
    ta = TradingAgentsGraph(
        debug=True,
        config=DEFAULT_CONFIG,
        selected_analysts=["market", "social", "news", "fundamentals", "candlestick"]
    )
    print("✅ 初始化完成")
    
    # 创建初始状态
    init_agent_state = ta.propagator.create_initial_state(target_symbol, trade_date)
    args = ta.propagator.get_graph_args()
    
    print("\n" + "=" * 120)
    print("🚀 开始逐步执行 LangGraph 链路...")
    print("=" * 120)
    
    try:
        final_state = None
        step_count = 0
        
        # 使用 stream() 逐节点执行
        for chunk in ta.graph.stream(init_agent_state, **args):
            step_count += 1
            
            # 获取节点名称
            node_name = list(chunk.keys())[0] if chunk else "Unknown"
            
            print(f"\n📊 步骤 {step_count}: 执行节点 '{node_name}'")
            
            # 显示节点输出并询问是否继续
            if not step_prompt(step_count, node_name, chunk):
                print("\n👋 用户取消执行")
                return
            
            final_state = chunk
        
        # 执行完成
        print("\n" + "=" * 120)
        print("🎉 所有节点执行完成!")
        print("=" * 120)
        
        if final_state:
            # 保存最终状态
            final_filename = OUTPUT_DIR / f"final_state_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(final_filename, "w", encoding="utf-8") as f:
                save_dict = {}
                for key, value in final_state.items():
                    if key == "messages":
                        save_dict[key] = []
                        for msg in value:
                            save_dict[key].append({
                                "type": type(msg).__name__,
                                "content": msg.content if hasattr(msg, "content") else str(msg)
                            })
                    elif key in ["investment_debate_state", "risk_debate_state"]:
                        save_dict[key] = dict(value)
                    else:
                        save_dict[key] = str(value)
                json.dump(save_dict, f, indent=2, ensure_ascii=False)
            print(f"\n💾 最终状态已保存到: {final_filename}")
            
            # 处理最终信号
            decision = ta.process_signal(final_state.get("final_trade_decision", ""))
            print(f"\n📊 最终决策:")
            print(decision)
            
            # 显示关键报告
            print("\n" + "=" * 120)
            print("📋 关键报告摘要:")
            print("=" * 120)
            
            for field in ["market_report", "fundamentals_report", "candlestick_report", 
                         "sentiment_report", "news_report"]:
                if final_state.get(field):
                    print(f"\n📄 {field}:")
                    print("-" * 120)
                    report = final_state[field]
                    print(report[:1000] + "..." if len(report) > 1000 else report)
            
            if final_state.get("investment_plan"):
                print("\n💰 投资计划:")
                print("-" * 120)
                print(final_state["investment_plan"])
            
            if final_state.get("final_trade_decision"):
                print("\n🎯 最终交易决策:")
                print("-" * 120)
                print(final_state["final_trade_decision"])
        
    except Exception as e:
        print(f"\n❌ 执行出错: {e}")
        import traceback
        traceback.print_exc()
        
        # 保存错误信息
        error_filename = OUTPUT_DIR / f"error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(error_filename, "w", encoding="utf-8") as f:
            f.write(f"Error: {e}\n\n")
            f.write(traceback.format_exc())
        print(f"\n💾 错误信息已保存到: {error_filename}")
        
        return


if __name__ == "__main__":
    run_interactive_steps()
