#!/bin/bash
# reports-server.sh - 管理 reports.html HTTP 服务

# 配置
DIR="$(cd "$(dirname "$0")" && pwd)"
DEFAULT_PORT=8001
PID_FILE="$DIR/reports-server.pid"

start() {
    local port="${1:-$DEFAULT_PORT}"

    # 检查是否已在运行（通过 PID 文件）
    if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
        echo "❌ 服务已在运行 (PID $(cat "$PID_FILE"), 端口 $port)"
        return 1
    fi

    # 检查端口占用（用 pgrep，不用 lsof）
    if pgrep -f "python -m http.server $port" >/dev/null 2>&1; then
        echo "⚠️  端口 $port 被占用，释放旧进程..."
        pkill -9 -f "python -m http.server $port" 2>/dev/null
        sleep 1
    fi

    cd "$DIR" || return 1
    nohup python3 -m http.server "$port" > /dev/null 2>&1 &
    local pid=$!
    echo "$pid" > "$PID_FILE"
    sleep 0.5
    if kill -0 "$pid" 2>/dev/null; then
        echo "✅ 服务已启动 - http://localhost:$port/reports.html (PID $pid)"
    else
        echo "❌ 启动失败"
        rm -f "$PID_FILE"
        return 1
    fi
}

stop() {
    local killed=0

    # 1. 尝试通过 PID 文件
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE" 2>/dev/null)
        if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
            kill "$pid" 2>/dev/null
            sleep 0.5
            if kill -0 "$pid" 2>/dev/null; then
                echo "⚠️  进程 $pid 未停止，强制杀死..."
                kill -9 "$pid" 2>/dev/null
            fi
            echo "✅ 服务已停止 (PID $pid)"
            killed=1
        fi
        rm -f "$PID_FILE"
    fi

    # 2. 强杀所有匹配的 http.server 进程（防止 PID 文件丢失）
    local pids=$(pgrep -f "python -m http.server" 2>/dev/null)
    if [ -n "$pids" ]; then
        echo "⚠️  清理残留进程: $pids"
        kill -9 $pids 2>/dev/null
        killed=1
    fi

    if [ $killed -eq 0 ]; then
        echo "🔴 服务未运行"
    fi
}

restart() {
    echo "重启服务..."
    stop
    sleep 1
    start "$@"
}

status() {
    if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
        local pid=$(cat "$PID_FILE")
        # 尝试获取端口（多种方式）
        local port=""
        if command -v ss >/dev/null 2>&1; then
            port=$(ss -ltn 2>/dev/null | awk -v pid="$pid" '$6 ~ /^pid=/ {print $4}' | sed 's/.*://' | head -1)
        elif command -v netstat >/dev/null 2>&1; then
            port=$(netstat -an 2>/dev/null | grep "$pid" | grep LISTEN | awk '{print $4}' | sed 's/.*://' | head -1)
        fi
        echo "🟢 服务运行中 (PID $pid, 端口 ${port:-unknown})"
    else
        # 查找运行中的 http.server 进程
        local pids=$(pgrep -f "python -m http.server" 2>/dev/null)
        if [ -n "$pids" ]; then
            echo "🟡 服务运行中但 PID 文件丢失 (PID $pids)"
        else
            echo "🔴 服务未运行"
        fi
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
        echo "用法: $0 {start|stop|restart|status} [port]"
        echo "示例:"
        echo "  $0 start          # 启动在端口 $DEFAULT_PORT"
        echo "  $0 start 8080     # 启动在端口 8080"
        echo "  $0 status"
        echo "  $0 stop"
        echo "  $0 restart"
        exit 1
        ;;
esac
