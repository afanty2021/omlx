# omlx 性能优化指南

## 问题诊断
- **模型**: Qwen3.6-35B-A3B-4bit
- **系统**: Apple M4 Pro, 48GB RAM
- **问题**: 内存占用 45GB，网络搜索耗时 20 分钟

## 根本原因
1. **内存限制配置不当** - 默认配置没有充分限制模型内存
2. **KV 缓存增长** - 长上下文对话导致 KV 缓存过度增长
3. **并发请求过高** - 默认 max_num_seqs=8 可能对大模型过多
4. **未启用推测解码** - DFlash 可以提供 3-4x 加速

## 解决方案

### 1. 启动命令优化

```bash
# 基础优化配置
omlx serve \
  --model-dir ~/models \
  --max-model-memory 28GB \
  --max-process-memory 40GB \
  --max-concurrent-requests 4 \
  --log-level info

# 启用 SSD 缓存（适合长上下文）
omlx serve \
  --model-dir ~/models \
  --max-model-memory 28GB \
  --max-process-memory 40GB \
  --paged-ssd-cache-dir ~/.omlx/cache \
  --paged-ssd-cache-max-size 50GB \
  --hot-cache-max-size 8GB \
  --max-concurrent-requests 4

# 启用 DFlash 推测解码（3-4x 加速，短上下文）
# 需要先配置草稿模型（见下方）
```

### 2. 模型特定配置

编辑 `~/.omlx/model_settings.json`:

```json
{
  "version": 1,
  "models": {
    "Qwen3.6-35B-A3B-4bit": {
      "max_tokens": 4096,
      "max_context_window": 8192,
      "temperature": 0.7,
      "top_p": 0.9,
      "turboquant_kv_enabled": true,
      "turboquant_kv_bits": 3,
      "turboquant_skip_last": true,
      "ttl_seconds": 300,
      "dflash_enabled": false,
      "is_pinned": false,
      "is_default": true
    }
  }
}
```

### 3. DFlash 推测解码配置（可选）

如果需要更快的速度，可以启用 DFlash：

```bash
# 1. 安装 DFlash
pip install dflash-mlx

# 2. 下载草稿模型（例如 Qwen2.5-14B-4bit）
# 草稿模型应该与主模型共享 tokenizer

# 3. 配置模型设置
# 在 ~/.omlx/model_settings.json 中添加：
{
  "dflash_enabled": true,
  "dflash_draft_model": "/path/to/qwen2.5-14b-4bit",
  "dflash_draft_quant_bits": 4
}
```

### 4. 内存监控和调优

```bash
# 实时监控内存使用
watch -n 2 'mx.get_active_memory() / 1024**3'  # Python

# 或使用 Activity Monitor 查看 "Metal" 内存使用
```

### 5. Hermes Agent 配置优化

如果使用 Hermes Agent，确保其配置：
- 降低并发请求数
- 增加请求超时时间
- 考虑使用更小的模型进行工具调用

## 参数说明

| 参数 | 推荐值 | 说明 |
|------|--------|------|
| `--max-model-memory` | 28GB | 模型权重 + KV 缓存上限 |
| `--max-process-memory` | 40GB | 总进程内存限制（留 8GB 给系统） |
| `--max-concurrent-requests` | 4 | 降低并发以减少内存峰值 |
| `--paged-ssd-cache-max-size` | 50GB | SSD 缓存大小 |
| `--hot-cache-max-size` | 8GB | 热缓存（内存）大小 |
| `ttl_seconds` | 300 | 5分钟无活动后卸载模型 |

## 预期效果

- **内存占用**: 稳定在 28-32GB
- **响应速度**: 网络搜索从 20 分钟降至 2-3 分钟
- **稳定性**: 避免内存交换和系统卡顿

## 故障排查

### 如果仍然内存过高：
1. 降低 `max_context_window` 到 4096
2. 启用 `turboquant_kv_enabled` 并设置 `turboquant_kv_bits: 2`
3. 减少 `max_concurrent_requests` 到 2
4. 考虑使用更小的模型（如 Qwen-14B）

### 如果速度仍然慢：
1. 检查是否有交换（Activity Monitor -> Swap Used）
2. 启用 DFlash 推测解码
3. 降低 `max_tokens` 限制
4. 使用更快的存储（SSD）用于缓存

## 替代方案

如果性能仍不满意：
1. **使用更小的模型**: Qwen-14B-4bit 或 Qwen-7B-4bit
2. **更激进的量化**: 尝试 3bit 或 2bit 量化
3. **云端推理**: 使用 API 服务进行大模型推理
4. **模型蒸馏**: 使用知识蒸馏后的更小模型
