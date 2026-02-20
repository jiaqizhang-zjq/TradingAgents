#!/bin/bash
# TradingAgents 运行脚本
# 用法: ./run_trading.sh [股票代码] [日期]
# 示例: ./run_trading.sh LMND
#       ./run_trading.sh RKLB 2026-02-20

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# 创建 logs 目录
mkdir -p logs

# 默认参数
SYMBOL="${1:-LMND}"
DATE="${2:-$(date +%Y-%m-%d)}"
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
LOG_FILE="logs/${SYMBOL}-${DATE}-${TIMESTAMP}.log"

# 前台运行
if [ -t 1 ]; then
    .venv/bin/python run_trading.py "$SYMBOL" "$DATE" 2>&1 | tee "$LOG_FILE"
else
    # 后台运行（无终端）
    .venv/bin/python run_trading.py "$SYMBOL" "$DATE" > "$LOG_FILE" 2>&1
fi

echo "日志: $LOG_FILE"
