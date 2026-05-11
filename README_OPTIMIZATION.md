# omlx 性能优化工具包

## 📋 问题诊断

你遇到的问题是 **omlx 运行 Qwen3.6-35B-A3B-4bit 时**:
- 内存占用过高 (45GB/48GB)
- 速度极慢 (网络搜索 20 分钟)
- 系统可能发生交换

## 🛠️ 可用工具

本目录包含以下优化工具：

| 文件 | 用途 | 使用方法 |
|------|------|----------|
| `QUICK_START.md` | 快速修复指南 | 首先阅读此文件 |
| `OMLX_OPTIMIZATION_GUIDE.md` | 详细优化指南 | 深入了解优化原理 |
| `start_optimized.sh` | 优化启动脚本 | `./start_optimized.sh` |
| `diagnose.sh` | 诊断脚本 | `./diagnose.sh` |
| `apply_optimized_config.py` | 配置应用工具 | `python3 apply_optimized_config.py` |
| `qwen_optimized_settings.json` | Qwen 优化配置 | 手动参考或合并 |

## 🚀 快速开始

### 1. 运行诊断（可选）
```bash
./diagnose.sh
```

### 2. 应用优化配置
```bash
# 方法 1: 使用 Python 脚本
python3 apply_optimized_config.py

# 方法 2: 手动编辑 ~/.omlx/model_settings.json
# 参考 qwen_optimized_settings.json
```

### 3. 启动优化服务
```bash
# 停止现有服务
pkill -f "omlx serve"

# 启动优化服务
./start_optimized.sh
```

## 📊 关键优化参数

### 内存限制
```bash
--max-model-memory 28GB      # 模型权重 + KV 缓存上限
--max-process-memory 40GB    # 总进程内存限制
```

### 并发控制
```bash
--max-concurrent-requests 4  # 降低并发减少内存峰值
```

### KV 缓存优化
```json
{
  "turboquant_kv_enabled": true,
  "turboquant_kv_bits": 3
}
```

### 模型 TTL
```json
{
  "ttl_seconds": 300  # 5分钟无活动后卸载
}
```

## 📈 预期效果

- **内存占用**: 45GB → 28-32GB (减少 30-40%)
- **响应速度**: 20 分钟 → 2-3 分钟 (提升 6-10x)
- **系统稳定性**: 避免交换，保持流畅

## 🔧 高级优化

### DFlash 推测解码
```bash
pip install dflash-mlx
```
然后在模型设置中配置：
```json
{
  "dflash_enabled": true,
  "dflash_draft_model": "/path/to/draft-model",
  "dflash_draft_quant_bits": 4
}
```

### SSD 缓存
```bash
export ENABLE_SSD_CACHE=true
export SSD_CACHE_MAX_SIZE=50GB
export HOT_CACHE_MAX_SIZE=8GB
./start_optimized.sh
```

## 📝 环境变量

启动脚本支持以下环境变量：

```bash
# 基础配置
MODEL_DIR=~/models                    # 模型目录
MAX_MODEL_MEMORY=28GB                 # 最大模型内存
MAX_PROCESS_MEMORY=40GB               # 最大进程内存
MAX_CONCURRENT_REQUESTS=4             # 最大并发请求
LOG_LEVEL=info                        # 日志级别
PORT=8000                             # 服务端口

# 缓存配置
ENABLE_SSD_CACHE=true                 # 启用 SSD 缓存
SSD_CACHE_DIR=~/.omlx/cache           # SSD 缓存目录
SSD_CACHE_MAX_SIZE=50GB               # SSD 缓存大小
HOT_CACHE_MAX_SIZE=8GB                # 热缓存大小
```

## 🐛 故障排查

### 内存仍然过高
```bash
# 进一步减少内存限制
export MAX_MODEL_MEMORY=24GB
export HOT_CACHE_MAX_SIZE=4GB

# 启用更激进的 KV 压缩
# turboquant_kv_bits: 2
```

### 速度仍然慢
```bash
# 检查交换
top -l 1 | grep Swap

# 启用 DFlash
pip install dflash-mlx

# 考虑更小的模型
```

### 内存不足错误
```bash
# 减少并发请求
export MAX_CONCURRENT_REQUESTS=2

# 减少上下文长度
# max_context_window: 4096
```

## 📚 相关资源

- [omlx GitHub](https://github.com/jundot/omlx)
- [MLX 文档](https://ml-explore.github.io/mlx/)
- [Qwen 模型](https://huggingface.co/Qwen)

## 🤝 贡献

如果你发现更好的优化方案或有改进建议，欢迎：
1. 提交 Issue
2. 创建 Pull Request
3. 分享你的配置

---

**注意**: 这些优化针对 Apple M4 Pro 48GB RAM 的配置。其他配置可能需要调整参数。
