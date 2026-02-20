#!/bin/bash

# TradingAgents 运行脚本（非 debug 模式）
# 用法: ./run_trading.sh [股票代码] [日期] [--debug]
# 示例: ./run_trading.sh LMND 2026-02-20
#      ./run_trading.sh AAPL          # 使用默认日期（今天）

# 设置颜色
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}TradingAgents 运行脚本${NC}"
echo -e "${BLUE}========================================${NC}"

# 脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 检查虚拟环境
VENV_PYTHON="$SCRIPT_DIR/.venv/bin/python"
if [ ! -f "$VENV_PYTHON" ]; then
    echo -e "${RED}错误: 未找到 .venv 虚拟环境${NC}"
    echo "请先运行: python -m venv .venv && pip install -r requirements.txt"
    exit 1
fi

# 默认参数
SYMBOL=${1:-"LMND"}
DATE=${2:-"$(date +%Y-%m-%d)"}
DEBUG_FLAG=""

# 检查是否有 --debug 参数
for arg in "$@"; do
    if [ "$arg" == "--debug" ]; then
        DEBUG_FLAG="--debug"
        break
    fi
done

# 运行程序（直接使用 venv 的 python）
echo -e "${GREEN}开始分析 ${SYMBOL} (${DATE})...${NC}"
echo ""

"$VENV_PYTHON" run_trading.py "$SYMBOL" "$DATE" $DEBUG_FLAG

EXIT_CODE=$?

echo ""
echo -e "${BLUE}========================================${NC}"
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}运行完成！${NC}"
    echo -e "报告目录: $SCRIPT_DIR/reports/${SYMBOL}/${DATE}"
else
    echo -e "${RED}运行失败，退出码: $EXIT_CODE${NC}"
fi
echo -e "${BLUE}========================================${NC}"

exit $EXIT_CODE
