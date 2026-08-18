# omlx 性能问题快速修复指南

## 🚨 问题症状
- ❌ 运行 Qwen3.6-35B-A3B-4bit 内存占用 45GB/48GB
- ❌ Hermes Agent 网络搜索耗时 20 分钟
- ❌ 系统响应缓慢，可能发生交换

## ✅ 解决方案（3 步修复）

### 第 1 步：运行诊断脚本
```bash
cd /Users/berton/Github/omlx
./diagnose.sh
```

### 第 2 步：应用优化配置
```bash
# 备份现有配置
cp ~/.omlx/model_settings.json ~/.omlx/model_settings.json.backup 2>/dev/null || true

# 应用 Qwen 优化配置
cat qwen_optimized_settings.json | jq '.models' > /tmp/qwen_settings.json
# 手动合并到 ~/.omlx/model_settings.json 或直接替换
```

### 第 3 步：使用优化启动脚本
```bash
# 停止现有的 omlx 服务
pkill -f "omlx serve" 2>/dev/null || true

# 启动优化后的服务
./start_optimized.sh
```

## 📋 关键优化参数

| 参数 | 原值 | 优化值 | 效果 |
|------|------|--------|------|
| memory-guard-gb | 未设置（默认 balanced） | 40 | 总内存上限，留 8GB 给系统 |
| max-concurrent-requests | 8 | 4 | 减少并发压力 |
| turboquant_kv_bits | 4 | 3 | KV 缓存压缩，减少 25% 内存 |
| max_context_window | 未限制 | 8192 | 限制上下文长度 |
| ttl_seconds | 未设置 | 300 | 5 分钟无活动后卸载模型 |

## 🎯 预期效果

- **内存占用**: 45GB → 28-32GB (减少 30-40%)
- **响应速度**: 20 分钟 → 2-3 分钟 (提升 6-10x)
- **系统稳定性**: 避免交换，保持流畅

## 🔧 故障排查

### 如果内存仍然过高:
```bash
# 进一步减少内存限制
export MEMORY_GUARD_GB=24
export HOT_CACHE_MAX_SIZE=4GB

# 或启用更激进的 KV 压缩
# 在 model_settings.json 中设置:
"turboquant_kv_bits": 2
```

### 如果速度仍然慢:
```bash
# 1. 检查是否有交换
top -l 1 | grep Swap

# 2. 启用 DFlash 推测解码（需要额外安装）
pip install dflash-mlx

# 3. 考虑使用更小的模型
# Qwen-14B-4bit 或 Qwen-7B-4bit
```

### 如果出现内存不足错误:
```bash
# 减少并发请求
export MAX_CONCURRENT_REQUESTS=2

# 减少上下文长度
# 在 model_settings.json 中设置:
"max_context_window": 4096
```

## 📚 相关文件

- `OMLX_OPTIMIZATION_GUIDE.md` - 详细优化指南
- `start_optimized.sh` - 优化启动脚本
- `diagnose.sh` - 诊断脚本
- `qwen_optimized_settings.json` - Qwen 模型优化配置

## 🚀 高级优化

### 启用 DFlash 推测解码 (3-4x 加速)

```bash
# 1. 安装 DFlash
pip install dflash-mlx

# 2. 下载草稿模型（与主模型共享 tokenizer）
# 例如: Qwen2.5-14B-4bit

# 3. 在模型设置中配置
{
  "dflash_enabled": true,
  "dflash_draft_model": "/path/to/qwen2.5-14b-4bit",
  "dflash_draft_quant_enabled": true,
  "dflash_draft_quant_weight_bits": 4
}
```

### 启用 SSD 缓存（长上下文优化）

```bash
# 使用启动脚本中的 SSD 缓存选项
export ENABLE_SSD_CACHE=true
export SSD_CACHE_MAX_SIZE=50GB
export HOT_CACHE_MAX_SIZE=8GB

./start_optimized.sh
```

## 💡 使用建议

1. **日常使用**: 使用优化启动脚本
2. **开发测试**: 可以降低内存限制以测试边界情况
3. **生产环境**: 启用 SSD 缓存和 TTL 自动卸载
4. **极限性能**: 启用 DFlash 推测解码

## 📞 获取帮助

- 查看详细指南: `cat OMLX_OPTIMIZATION_GUIDE.md`
- 运行诊断: `./diagnose.sh`
- 检查日志: `tail -f ~/.omlx/logs/server.log`
- GitHub Issues: https://github.com/jundot/omlx/issues

---

**注意**: 这些优化针对 Apple M4 Pro 48GB RAM 的配置。其他配置可能需要调整参数。
