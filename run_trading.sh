#!/bin/bash
# TradingAgents 运行脚本
# 用法: ./run_trading.sh [股票代码] [日期]
# 示例: ./run_trading.sh LMND
#       ./run_trading.sh RKLB 2026-02-20

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# 删除缓存，强制获取最新数据
rm -rf tradingagents/dataflows/data_cache/*.json

# 创建 logs 目录
mkdir -p logs

# 默认参数
SYMBOL="${1:-LMND}"

# 计算分析日期：自动跳过周末，找到最近的前一个交易日
# 逻辑：从昨天开始，如果是周六(6)或周日(7)，继续往前推到周五
ANALYSIS_DATE="${2:-}"
if [ -z "$ANALYSIS_DATE" ]; then
    # 初始日期：昨天
    ANALYSIS_DATE=$(date -v-1d +%Y-%m-%d)
    # 检查是否是周末（1=周一, 7=周日），6=周六, 7=周日
    while [ $(date -j -f "%Y-%m-%d" "$ANALYSIS_DATE" +%u 2>/dev/null) -ge 6 ]; do
        ANALYSIS_DATE=$(date -j -v-1d -f "%Y-%m-%d" "$ANALYSIS_DATE" +%Y-%m-%d 2>/dev/null)
    done
fi

DATE="$ANALYSIS_DATE"
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
