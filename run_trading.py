#!/usr/bin/env python3
"""
TradingAgents 运行脚本
用法: python run_trading.py [股票代码] [日期] [选项]
示例: python run_trading.py LMND 2026-02-20
      python run_trading.py AAPL --llm-provider anthropic --deep-think claude-sonnet-4-20250514

日志输出: logs/{symbol}-{date}-h.log
"""

import sys
import os
import argparse
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

# 加载 .env 环境变量（优先使用项目内的配置）
env_path = os.path.join(BASE_DIR, ".env")
load_dotenv(env_path, override=True)

# 可用分析师列表
AVAILABLE_ANALYSTS = ["market", "social", "news", "fundamentals", "candlestick"]
# 可用 LLM 提供商
AVAILABLE_PROVIDERS = ["openai", "anthropic", "google", "xai", "openrouter", "ollama"]

def run_trading_analysis(
    symbol: str,
    date: str,
    debug: bool = True,  # 默认开启 debug
    llm_provider: str = None,
    deep_think_llm: str = None,
    quick_think_llm: str = None,
    backend_url: str = None,
    max_debate_rounds: int = 2,
    analysts: list = None,
    output_lang: str = None,
):
    """
    运行交易分析

    Args:
        symbol: 股票代码
        date: 分析日期
        debug: 是否开启 debug 模式 (默认 True)
        llm_provider: LLM 提供商 (从 .env 读取或指定)
        deep_think_llm: 深度思考模型
        quick_think_llm: 快速思考模型
        backend_url: API 端点
        max_debate_rounds: 辩论轮数
        analysts: 分析师列表
        output_lang: 输出语言
    """
    print(f"\n{'='*50}")
    print(f"TradingAgents 分析")
    print(f"股票: {symbol}")
    print(f"日期: {date}")
    print(f"Debug: {'开启' if debug else '关闭'}")
    print(f"{'='*50}\n")

    # 创建配置（默认关闭 debug）
    config = DEFAULT_CONFIG.copy()

    # Debug 配置
    config["debug"] = {
        "enabled": debug,
        "verbose": debug,
        "show_prompts": debug,
        "log_level": "INFO" if not debug else "DEBUG",
    }

    # LLM 配置（命令行参数优先，否则用 .env/默认值）
    if llm_provider:
        config["llm_provider"] = llm_provider
        print(f"📡 LLM 提供商: {llm_provider}")
    else:
        print(f"📡 LLM 提供商: {config['llm_provider']} (默认)")

    if deep_think_llm:
        config["deep_think_llm"] = deep_think_llm
        print(f"🧠 深度思考模型: {deep_think_llm}")
    else:
        print(f"🧠 深度思考模型: {config['deep_think_llm']} (默认)")

    if quick_think_llm:
        config["quick_think_llm"] = quick_think_llm
    elif config.get("quick_think_llm"):
        print(f"⚡ 快速思考模型: {config['quick_think_llm']} (默认)")

    if backend_url:
        config["backend_url"] = backend_url

    if max_debate_rounds is not None:
        config["max_debate_rounds"] = max_debate_rounds
        config["max_risk_discuss_rounds"] = max_debate_rounds
        print(f"🔄 辩论轮数: {max_debate_rounds}")

    if output_lang:
        config["output_language"] = output_lang
        print(f"🌐 输出语言: {output_lang}")
    else:
        print(f"🌐 输出语言: {config.get('output_language', 'zh')} (默认)")

    # 分析师选择
    if analysts:
        selected_analysts = analysts
    else:
        selected_analysts = ["market", "social", "news", "fundamentals", "candlestick"]
    print(f"📊 分析师: {', '.join(selected_analysts)}")

    print()

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
        print(f"✅ 分析完成！")
        print(f"最终决策: {decision}")
        print(f"{'='*50}\n")

        return graph_state, decision

    except Exception as e:
        print(f"\n❌ 运行出错: {e}")
        import traceback
        traceback.print_exc()
        return None, None


def main():
    """命令行主入口"""
    parser = argparse.ArgumentParser(
        description="TradingAgents 股票分析",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s LMND                        # 分析 LMND，今天日期
  %(prog)s AAPL 2026-02-20             # 指定日期
  %(prog)s NVDA --debug                 # 开启调试
  %(prog)s MSFT --analysts market news fundamentals  # 只选3个分析师
  %(prog)s TSLA --llm-provider anthropic --deep-think claude-sonnet-4-20250514

可用分析师: market, social, news, fundamentals, candlestick
可用提供商: openai, anthropic, google, xai, openrouter, ollama
        """
    )

    parser.add_argument("symbol", nargs="?", default="LMND", help="股票代码 (默认: LMND)")
    parser.add_argument("date", nargs="?", default=None, help="分析日期 YYYY-MM-DD (默认: 今天)")

    # 选项
    parser.add_argument("--debug", action="store_true", default=True, help="开启调试模式 (默认开启)")
    parser.add_argument("--analysts", nargs="+", help="选择的分析师 (如: market news fundamentals)")
    parser.add_argument("--llm-provider", "--provider", dest="llm_provider",
                        help="LLM 提供商 (openai/anthropic/google/xai/openrouter/ollama)")
    parser.add_argument("--deep-think", dest="deep_think_llm", help="深度思考模型")
    parser.add_argument("--quick-think", dest="quick_think_llm", help="快速思考模型")
    parser.add_argument("--backend-url", dest="backend_url", help="API 端点 URL")
    parser.add_argument("--debate-rounds", type=int, default=2, help="辩论轮数 (默认: 2)")
    parser.add_argument("--lang", choices=["zh", "en"], help="输出语言")

    args = parser.parse_args()

    # 默认日期
    date = args.date or datetime.now().strftime("%Y-%m-%d")

    run_trading_analysis(
        symbol=args.symbol,
        date=date,
        debug=args.debug,
        llm_provider=args.llm_provider,
        deep_think_llm=args.deep_think_llm,
        quick_think_llm=args.quick_think_llm,
        backend_url=args.backend_url,
        max_debate_rounds=args.debate_rounds,
        analysts=args.analysts,
        output_lang=args.lang,
    )


if __name__ == "__main__":
    main()
