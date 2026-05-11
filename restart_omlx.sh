#!/bin/bash
# omlx 服务重启脚本

echo "🔄 正在重启 omlx 服务..."

# 激活 conda 环境
echo "📦 激活 conda 环境: Quant-3.11"
source ~/miniconda3/etc/profile.d/conda.sh
conda activate Quant-3.11

# 检查并停止现有进程
echo "🔍 检查现有 omlx 进程..."
OMLX_PID=$(pgrep -f "omlx serve")
if [ -n "$OMLX_PID" ]; then
    echo "🛑 停止进程 $OMLX_PID"
    kill $OMLX_PID
    sleep 2
    # 确认进程已停止
    if pgrep -f "omlx serve" > /dev/null; then
        echo "⚠️  进程仍在运行，强制停止..."
        pkill -9 -f "omlx serve"
        sleep 1
    fi
else
    echo "✅ 没有运行中的 omlx 进程"
fi

# 启动 omlx 服务（绑定到 0.0.0.0）
echo "🚀 启动 omlx 服务 (绑定到 0.0.0.0:8000)..."
cd /Users/berton/Github/omlx
omlx serve --model-dir ~/.omlx/models --host 0.0.0.0 --port 8000

