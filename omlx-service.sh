#!/bin/bash
# OMLX 服务管理脚本
# 使用方法: ./omlx-service.sh {start|stop|restart|status|logs}

PLIST_PATH="$HOME/Library/LaunchAgents/com.omlx.server.plist"
SERVICE_NAME="com.omlx.server"
LOG_PATH="$HOME/.omlx/logs/omlx-server.log"
ERROR_LOG_PATH="$HOME/.omlx/logs/omlx-server-error.log"

case "$1" in
    start)
        echo "🚀 启动 OMLX 服务..."
        launchctl load "$PLIST_PATH"
        echo "✅ 服务已启动"
        sleep 2
        launchctl list | grep -q "$SERVICE_NAME" && echo "✅ 服务运行中" || echo "❌ 服务启动失败"
        ;;

    stop)
        echo "🛑 停止 OMLX 服务..."
        launchctl unload "$PLIST_PATH"
        echo "✅ 服务已停止"
        ;;

    restart)
        echo "🔄 重启 OMLX 服务..."
        launchctl unload "$PLIST_PATH"
        sleep 1
        launchctl load "$PLIST_PATH"
        echo "✅ 服务已重启"
        sleep 2
        launchctl list | grep -q "$SERVICE_NAME" && echo "✅ 服务运行中" || echo "❌ 服务启动失败"
        ;;

    status)
        echo "📊 OMLX 服务状态:"
        if launchctl list | grep -q "$SERVICE_NAME"; then
            echo "✅ 服务已加载"
            PID=$(pgrep -f "omlx serve")
            if [ -n "$PID" ]; then
                echo "📍 进程 PID: $PID"
            else
                echo "⚠️  未找到运行中的进程"
            fi
        else
            echo "❌ 服务未加载"
        fi

        # 测试服务端点
        echo ""
        echo "🔍 测试服务端点:"
        if curl -s http://127.0.0.1:8000/v1/models > /dev/null 2>&1; then
            echo "✅ API 端点响应正常 (http://127.0.0.1:8000)"
        else
            echo "❌ API 端点无响应"
        fi
        ;;

    logs)
        echo "📋 最近的日志:"
        echo "==================================="
        tail -50 "$LOG_PATH"
        echo ""
        echo "📋 错误日志 (如果有):"
        echo "==================================="
        if [ -s "$ERROR_LOG_PATH" ]; then
            tail -20 "$ERROR_LOG_PATH"
        else
            echo "无错误日志"
        fi
        ;;

    *)
        echo "OMLX 服务管理脚本"
        echo ""
        echo "使用方法:"
        echo "  $0 {start|stop|restart|status|logs}"
        echo ""
        echo "命令说明:"
        echo "  start   - 启动服务"
        echo "  stop    - 停止服务"
        echo "  restart - 重启服务"
        echo "  status  - 查看服务状态"
        echo "  logs    - 查看服务日志"
        exit 1
        ;;
esac
