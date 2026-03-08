#!/bin/bash
# reports-server.sh - 管理 reports.html HTTP 服务和 API 服务

# 配置
DIR="$(cd "$(dirname "$0")" && pwd)"
DEFAULT_PORT=8003
PID_FILE="$DIR/reports-server.pid"
API_PID_FILE="$DIR/api-server.pid"

start() {
    local port="${1:-$DEFAULT_PORT}"

    # 停止旧服务
    stop

    cd "$DIR" || return 1
    
    # 启动统一服务器 (端口 8001，同时处理 HTTP 和 API)
    nohup .venv/bin/python api_server.py > /dev/null 2>&1 &
    local api_pid=$!
    echo "$api_pid" > "$API_PID_FILE"
    sleep 0.5
    
    if kill -0 "$api_pid" 2>/dev/null; then
        echo "✅ 服务已启动"
        echo "   - HTTP: http://localhost:$port/reports.html (PID $api_pid)"
        echo "   - API:  http://localhost:$port/api/*"
    else
        echo "❌ 启动失败"
        rm -f "$PID_FILE" "$API_PID_FILE"
        return 1
    fi
}

stop() {
    # 停止 API 服务器
    if [ -f "$API_PID_FILE" ]; then
        local api_pid=$(cat "$API_PID_FILE" 2>/dev/null)
        if [ -n "$api_pid" ]; then
            kill -9 "$api_pid" 2>/dev/null
            echo "✅ API 服务已停止 (PID $api_pid)"
        fi
        rm -f "$API_PID_FILE"
    fi
    
    # 清理残留进程
    pkill -9 -f "api_server.py" 2>/dev/null
    pkill -9 -f "python -m http.server" 2>/dev/null
}

restart() {
    echo "重启服务..."
    stop
    sleep 1
    start "$@"
}

status() {
    local api_running=0
    
    # 检查 API
    if [ -f "$API_PID_FILE" ] && kill -0 "$(cat "$API_PID_FILE")" 2>/dev/null; then
        echo "🟢 服务运行中 (PID $(cat "$API_PID_FILE"), 端口 8001)"
        api_running=1
    fi
    
    if [ $api_running -eq 0 ]; then
        echo "🔴 服务未运行"
    fi
}

case "$1" in
    start)
        start "$2"
        ;;
    stop)
        stop
        ;;
    restart|reload)
        shift
        restart "$@"
        ;;
    status)
        status
        ;;
    *)
        echo "用法: $0 {start|stop|restart|status}"
        echo "示例:"
        echo "  $0 start          # 启动服务"
        echo "  $0 status         # 查看状态"
        echo "  $0 stop           # 停止服务"
        echo "  $0 restart        # 重启服务"
        exit 1
        ;;
esac
