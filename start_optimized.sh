#!/bin/bash
# omlx 优化启动脚本
# 适用于 Apple M4 Pro 48GB RAM + Qwen3.6-35B-A3B-4bit

set -e

# 配置参数
MODEL_DIR="${MODEL_DIR:-$HOME/models}"
MAX_MODEL_MEMORY="${MAX_MODEL_MEMORY:-28GB}"
MAX_PROCESS_MEMORY="${MAX_PROCESS_MEMORY:-40GB}"
MAX_CONCURRENT_REQUESTS="${MAX_CONCURRENT_REQUESTS:-4}"
LOG_LEVEL="${LOG_LEVEL:-info}"
PORT="${PORT:-8000}"

# 缓存配置
ENABLE_SSD_CACHE="${ENABLE_SSD_CACHE:-true}"
SSD_CACHE_DIR="${SSD_CACHE_DIR:-$HOME/.omlx/cache}"
SSD_CACHE_MAX_SIZE="${SSD_CACHE_MAX_SIZE:-50GB}"
HOT_CACHE_MAX_SIZE="${HOT_CACHE_MAX_SIZE:-8GB}"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}═══════════════════════════════════════${NC}"
echo -e "${GREEN}   oMLX 优化启动脚本${NC}"
echo -e "${GREEN}═══════════════════════════════════════${NC}"
echo ""

# 显示配置
echo "配置参数："
echo "  模型目录: $MODEL_DIR"
echo "  最大模型内存: $MAX_MODEL_MEMORY"
echo "  最大进程内存: $MAX_PROCESS_MEMORY"
echo "  最大并发请求: $MAX_CONCURRENT_REQUESTS"
echo "  日志级别: $LOG_LEVEL"
echo "  端口: $PORT"
echo ""

if [ "$ENABLE_SSD_CACHE" = "true" ]; then
    echo "缓存配置："
    echo "  SSD 缓存: 启用"
    echo "  SSD 缓存目录: $SSD_CACHE_DIR"
    echo "  SSD 缓存大小: $SSD_CACHE_MAX_SIZE"
    echo "  热缓存大小: $HOT_CACHE_MAX_SIZE"
    echo ""
fi

# 检查模型目录
if [ ! -d "$MODEL_DIR" ]; then
    echo -e "${RED}错误: 模型目录不存在: $MODEL_DIR${NC}"
    exit 1
fi

# 创建缓存目录
if [ "$ENABLE_SSD_CACHE" = "true" ]; then
    mkdir -p "$SSD_CACHE_DIR"
    echo -e "${GREEN}✓ 缓存目录已创建${NC}"
fi

# 构建启动命令
CMD="omlx serve"
CMD="$CMD --model-dir $MODEL_DIR"
CMD="$CMD --max-model-memory $MAX_MODEL_MEMORY"
CMD="$CMD --max-process-memory $MAX_PROCESS_MEMORY"
CMD="$CMD --max-concurrent-requests $MAX_CONCURRENT_REQUESTS"
CMD="$CMD --log-level $LOG_LEVEL"
CMD="$CMD --port $PORT"

if [ "$ENABLE_SSD_CACHE" = "true" ]; then
    CMD="$CMD --paged-ssd-cache-dir $SSD_CACHE_DIR"
    CMD="$CMD --paged-ssd-cache-max-size $SSD_CACHE_MAX_SIZE"
    CMD="$CMD --hot-cache-max-size $HOT_CACHE_MAX_SIZE"
fi

echo -e "${GREEN}═══════════════════════════════════════${NC}"
echo -e "${GREEN}   启动 oMLX 服务器${NC}"
echo -e "${GREEN}═══════════════════════════════════════${NC}"
echo ""
echo "启动命令："
echo -e "${YELLOW}$CMD${NC}"
echo ""

# 启动服务器
exec $CMD
