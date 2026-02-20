#!/bin/bash
# TradingAgents 运行脚本
# 用法: ./run_trading.sh [股票代码] [日期]
# 示例: ./run_trading.sh LMND
#       ./run_trading.sh RKLB 2026-02-20

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# 默认参数
SYMBOL="${1:-LMND}"
DATE="${2:-$(date +%Y-%m-%d)}"

# 使用项目的虚拟环境运行
.venv/bin/python run_trading.py "$SYMBOL" "$DATE"
