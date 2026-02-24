#!/bin/bash
# reports-server.sh - 管理 reports.html HTTP 服务

# 配置
DIR="$(cd "$(dirname "$0")" && pwd)"
DEFAULT_PORT=8001
PID_FILE="$DIR/reports-server.pid"

start() {
    local port="${1:-$DEFAULT_PORT}"

    # 检查是否已在运行
    if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
        echo "❌ 服务已在运行 (PID $(cat "$PID_FILE"), 端口 $port)"
        return 1
    fi

    # 停止可能存在的旧进程（端口可能被占用）
    if lsof -i :"$port" >/dev/null 2>&1; then
        echo "⚠️  端口 $port 被占用，尝试释放..."
        pkill -f "python -m http.server $port" 2>/dev/null
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
    if [ ! -f "$PID_FILE" ]; then
        echo "⚠️  PID 文件不存在，服务可能未运行"
        # 尝试根据端口查找
        local pids=$(pgrep -f "python -m http.server $DEFAULT_PORT" 2>/dev/null)
        if [ -n "$pids" ]; then
            echo "发现运行中的进程: $pids"
            kill $pids 2>/dev/null
            sleep 1
        fi
        return 0
    fi

    local pid=$(cat "$PID_FILE")
    if kill -0 "$pid" 2>/dev/null; then
        kill "$pid"
        sleep 1
        if kill -0 "$pid" 2>/dev/null; then
            echo "⚠️  进程 $pid 未停止，强制杀死..."
            kill -9 "$pid"
        fi
        echo "✅ 服务已停止 (PID $pid)"
    else
        echo "⚠️  进程 $pid 不存在"
    fi
    rm -f "$PID_FILE"
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
        local port=$(lsof -i -n -P | grep "$pid" | grep LISTEN | awk '{print $9}' | sed 's/.*://')
        echo "🟢 服务运行中 (PID $pid, 端口 ${port:-unknown})"
    else
        # 尝试查找
        local pids=$(pgrep -f "python -m http.server $DEFAULT_PORT" 2>/dev/null)
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
