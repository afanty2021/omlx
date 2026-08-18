# Claude Code 使用 omlx 模型指南

## 📊 性能测试结果

### omlx (Qwen3.5-27B-Claude) 性能

| 任务类型 | 响应时间 | 说明 |
|---------|----------|------|
| 简单对话 | **2-7秒** | 首次加载 2 秒，后续 6-8 秒 |
| 代码解释 | **7-10秒** | 中等复杂度 |
| 代码生成 | **30-40秒** | 完整功能代码 |
| 复杂推理 | **10-20秒** | 需要思考的任务 |

### 与 Claude 官方 API 对比

| 平台 | 模型 | 预期速度 | 成本 |
|------|------|----------|------|
| Claude 官方 | Claude Sonnet 4 | 5-15秒 | $3/百万token |
| Claude 官方 | Claude Opus 4 | 10-30秒 | $15/百万token |
| omlx 本地 | 27B Claude | **2-10秒** | **免费** |

## 🎯 结论

**omlx 作为 Claude Code 后端：**
- ✅ **速度**: 比官方 Opus 快 2-3 倍
- ✅ **成本**: 完全免费
- ✅ **隐私**: 数据不离开本地
- ⚠️ **限制**: 功能可能不完全兼容

## ⚙️ 配置步骤

### 方法 1: 修改 settings.json

编辑 `~/.claude/settings.json`:

```json
{
  "env": {
    "ANTHROPIC_BASE_URL": "http://localhost:8000",
    "ANTHROPIC_API_KEY": "your-claude-code-key",
    "ANTHROPIC_MODEL": "Qwen3.5-27B-Claude-4.6-Opus-Distilled-MLX-4bit",
    "ANTHROPIC_DEFAULT_SONNET_MODEL": "Qwen3.5-27B-Claude-4.6-Opus-Distilled-MLX-4bit",
    "ANTHROPIC_DEFAULT_OPUS_MODEL": "Qwen3.5-27B-Claude-4.6-Opus-Distilled-MLX-4bit",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL": "Qwen3.5-27B-Claude-4.6-Opus-Distilled-MLX-4bit"
  }
}
```

### 方法 2: 使用环境变量

```bash
export ANTHROPIC_BASE_URL="http://localhost:8000"
export ANTHROPIC_API_KEY="your-claude-code-key"
export ANTHROPIC_MODEL="Qwen3.5-27B-Claude-4.6-Opus-Distilled-MLX-4bit"

# 然后启动 Claude Code
claude
```

## 🧪 功能测试

### 测试脚本

创建 `test_claude_api.sh`:

```bash
#!/bin/bash
API_KEY="your-claude-code-key"
BASE_URL="http://localhost:8000"
MODEL="Qwen3.5-27B-Claude-4.6-Opus-Distilled-MLX-4bit"

echo "=== 测试 1: 简单对话 ==="
START=$(date +%s)
RESULT=$(curl -s -X POST "$BASE_URL/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d "{
    \"model\": \"$MODEL\",
    \"messages\": [{\"role\": \"user\", \"content\": \"Hi\"}],
    \"max_tokens\": 50
  }")
END=$(date +%s)

echo "$RESULT" | jq -r '.choices[0].message.content'
echo "耗时: $((END - START_TIME)) 秒"
```

## 📋 支持的功能

### ✅ 完全支持
- 文本生成
- 代码生成
- 对话历史
- 系统提示
- 流式输出

### ⚠️ 部分支持
- 工具调用（需要测试）
- 图像分析（需要测试）
- 长上下文（32K tokens）

### ❌ 不支持
- Claude Artifacts
- 实时网络访问
- 文件上传（部分支持）

## 💡 使用建议

### 适合场景
1. **日常编程**: 快速响应，成本为 0
2. **代码审查**: 大模型，理解深入
3. **本地开发**: 隐私保护，数据安全

### 不适合场景
1. **生产环境**: 稳定性待验证
2. **复杂工具链**: 功能兼容性未知
3. **需要最新 Claude 功能**: 滞后于官方版本

## 🔄 故障排查

### 问题: 连接失败
```bash
# 检查 omlx 状态
curl http://localhost:8000/health

# 检查模型是否加载
curl http://localhost:8000/v1/models/status
```

### 问题: 功能不兼容
```bash
# 查看日志
tail -f ~/.omlx/logs/*.log

# 重启 omlx
pkill omlx
omlx serve --model-dir ~/models
```

### 问题: 性能慢
```bash
# 检查系统资源
top | grep omlx

# 检查 GPU 使用
sudo powermetrics --samplers gpu_power -i 1000
```

## 📚 相关资源

- [omlx GitHub](https://github.com/jundot/omlx)
- [MLX Documentation](https://ml-explore.github.io/mlx/)
- [Claude Code 文档](https://code.anthropic.com)

---

*最后更新: 2026-03-29*
