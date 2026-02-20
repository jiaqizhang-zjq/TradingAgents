#!/usr/bin/env python3
"""
TradingAgents 运行脚本 - 非 debug 模式
用法: python run_trading.py [股票代码] [日期]
示例: python run_trading.py LMND 2026-02-20
"""

import sys
import os
from datetime import datetime
from pathlib import Path

# 添加项目路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

# 尝试使用项目自带的 .venv
VENV_PYTHON = os.path.join(BASE_DIR, ".venv", "bin", "python")
if os.path.exists(VENV_PYTHON):
    # 如果运行的是系统 python，重新用 venv 的 python 执行
    if sys.executable != VENV_PYTHON:
        print(f"检测到项目虚拟环境，正在切换...")
        os.execv(VENV_PYTHON, [VENV_PYTHON] + sys.argv)

from dotenv import load_dotenv
from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG

# 加载环境变量
load_dotenv()

def run_trading_analysis(symbol: str, date: str, debug: bool = False):
    """
    运行交易分析

    Args:
        symbol: 股票代码 (如 LMND, AAPL, NVDA)
        date: 分析日期 (YYYY-MM-DD)，默认为今天
        debug: 是否开启 debug 模式，默认 False
    """
    print(f"\n{'='*50}")
    print(f"TradingAgents 分析")
    print(f"股票: {symbol}")
    print(f"日期: {date}")
    print(f"Debug: {'开启' if debug else '关闭'}")
    print(f"{'='*50}\n")

    # 创建配置（关闭 debug）
    config = DEFAULT_CONFIG.copy()
    config["debug"] = {
        "enabled": debug,
        "verbose": debug,
        "show_prompts": debug,
        "log_level": "INFO" if not debug else "DEBUG",
    }

    # 选择分析师（可根据需要调整）
    selected_analysts = ["market", "social", "news", "fundamentals", "candlestick"]

    # 初始化图
    print("正在初始化 TradingAgents...")
    ta = TradingAgentsGraph(
        selected_analysts=selected_analysts,
        debug=debug,
        config=config,
    )

    # 运行分析
    print(f"\n开始分析 {symbol} ({date})...\n")
    try:
        graph_state, decision = ta.propagate(symbol, date)

        print(f"\n{'='*50}")
        print(f"分析完成！")
        print(f"最终决策: {decision}")
        print(f"{'='*50}\n")

        # 可选：反思和学习
        # ta.reflect_and_remember(returns)

        return graph_state, decision

    except Exception as e:
        print(f"\n❌ 运行出错: {e}")
        import traceback
        traceback.print_exc()
        return None, None


if __name__ == "__main__":
    # 解析命令行参数
    symbol = sys.argv[1] if len(sys.argv) > 1 else "LMND"
    date = sys.argv[2] if len(sys.argv) > 2 else datetime.now().strftime("%Y-%m-%d")
    debug = "--debug" in sys.argv  # 可选 --debug 参数开启 debug

    run_trading_analysis(symbol, date, debug=debug)
