#!/bin/bash
#===============================================================================
# omlx 局域网服务器启动脚本
#
# 用途：启动 omlx 推理服务，允许局域网访问
# 用法：./start_server.sh [选项]
#
# 选项:
#   --model-dir     模型目录 (默认：~/Qwen3.5-35B-A3B-Uncensored-HauhauCS-Aggressive/models)
#   --port          服务端口 (默认：8000)
#   --api-key       API 密钥 (默认：从环境变量读取)
#   --model-type    模型类型 4bit/8bit/full (默认：4bit)
#   --help          显示帮助信息
#===============================================================================

set -e

# 默认配置
DEFAULT_MODEL_DIR="$HOME/Qwen3.5-35B-A3B-Uncensored-HauhauCS-Aggressive/models"
DEFAULT_PORT=8000
DEFAULT_HOST="0.0.0.0"
DEFAULT_MODEL_TYPE="4bit"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[OK]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 解析参数
MODEL_DIR=""
PORT=""
API_KEY=""
MODEL_TYPE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --model-dir)
            MODEL_DIR="$2"
            shift 2
            ;;
        --port)
            PORT="$2"
            shift 2
            ;;
        --api-key)
            API_KEY="$2"
            shift 2
            ;;
        --model-type)
            MODEL_TYPE="$2"
            shift 2
            ;;
        --help)
            head -20 "$0" | tail -15
            exit 0
            ;;
        *)
            log_error "未知参数：$1"
            exit 1
            ;;
    esac
done

# 使用默认值或环境变量
MODEL_DIR="${MODEL_DIR:-${OMLX_MODEL_DIR:-$DEFAULT_MODEL_DIR}}"
PORT="${PORT:-${OMLX_PORT:-$DEFAULT_PORT}}"
API_KEY="${API_KEY:-${OMLX_API_KEY:-}}"
MODEL_TYPE="${MODEL_TYPE:-${OMLX_MODEL_TYPE:-$DEFAULT_MODEL_TYPE}}"

# 根据模型类型确定子目录
case $MODEL_TYPE in
    4bit)
        MODEL_PATH="$MODEL_DIR/Qwen3.5-35B-A3B-mlx-4bit"
        MEMORY_GUARD_GB=24
        ;;
    8bit)
        MODEL_PATH="$MODEL_DIR/Qwen3.5-35B-A3B-mlx-8bit"
        MEMORY_GUARD_GB=40
        ;;
    full)
        MODEL_PATH="$MODEL_DIR/Qwen3.5-35B-A3B-mlx"
        MEMORY_GUARD_GB=64
        ;;
    *)
        log_error "不支持的模型类型：$MODEL_TYPE"
        exit 1
        ;;
esac

# 检查模型目录
if [ ! -d "$MODEL_PATH" ]; then
    log_error "模型目录不存在：$MODEL_PATH"
    exit 1
fi

# 检查 API Key
if [ -z "$API_KEY" ]; then
    log_warning "未设置 API_KEY，将使用空密钥（仅限内网测试）"
    log_warning "生产环境请设置：export OMLX_API_KEY=\"your-secret-key\""
fi

# 获取本机 IP
LOCAL_IP=$(ipconfig getifaddr en0 2>/dev/null || echo "unknown")

# 打印启动信息
echo ""
echo "==============================================================================="
echo "  omlx 局域网服务器"
echo "==============================================================================="
echo ""
echo "  服务器信息:"
echo "  ├─ 绑定地址：$DEFAULT_HOST:$PORT"
echo "  ├─ 局域网地址：http://$LOCAL_IP:$PORT"
echo "  ├─ 管理面板：http://$LOCAL_IP:$PORT/admin"
echo "  └─ API 端点：http://$LOCAL_IP:$PORT/v1"
echo ""
echo "  模型配置:"
echo "  ├─ 模型类型：$MODEL_TYPE"
echo "  ├─ 模型路径：$MODEL_PATH"
echo "  ├─ 内存保护上限：${MEMORY_GUARD_GB}GB"
echo "  └─ API Key: ${API_KEY:-[未设置]}"
echo ""
echo "  客户端连接示例:"
echo "  ┌─────────────────────────────────────────────────────────────────────────┐"
echo "  │ Python:                                                                 │"
echo "  │   from openai import OpenAI                                             │"
echo "  │   client = OpenAI(                                                      │"
echo "  │       base_url=\"http://$LOCAL_IP:$PORT/v1\",                              │"
echo "  │       api_key=\"$API_KEY\"                                                │"
echo "  │   )                                                                     │"
echo "  └─────────────────────────────────────────────────────────────────────────┘"
echo ""
echo "==============================================================================="
echo ""

# 检查 omlx 是否可用
if ! command -v omlx &> /dev/null; then
    log_warning "omlx 命令未找到，尝试使用 Python 模块方式启动..."
    OMLX_CMD="python3 -m omlx"
else
    OMLX_CMD="omlx"
fi

# 启动服务器
log_info "启动 omlx 服务器..."
echo ""

exec $OMLX_CMD serve \
    --model-dir "$MODEL_PATH" \
    --host "$DEFAULT_HOST" \
    --port "$PORT" \
    --api-key "$API_KEY" \
    --memory-guard-gb "$MEMORY_GUARD_GB" \
    --paged-ssd-cache-dir "$HOME/.omlx/cache" \
    --paged-ssd-cache-max-size "50GB" \
    --hot-cache-max-size "4GB" \
    --log-level info
