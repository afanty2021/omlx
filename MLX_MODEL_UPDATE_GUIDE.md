# MLX 模型更新完整指南

> 更新时间：2026-04-25

## 🎯 核心问题：更新需要重新下载吗？

**答案：取决于什么文件被更新了**

---

## 📊 更新类型详解

### 🔴 需要重新下载（约 10% 的情况）

**触发条件：**
- `.safetensors` 权重文件变更
- 模型重新训练或微调
- 量化位数改变（如 4bit → 8bit）

**原因：**
- 权重文件占模型大小的 95% 以上
- 你的 gemma-4-26b 模型：3 个 safetensors 文件 = 14.5 GB / 总共 15 GB
- 这些文件改变意味着模型本身发生了变化

**操作：**
```bash
# 删除旧模型
rm -rf /Users/berton/.omlx/models/<模型目录>

# 重新下载（使用你平时的方法）
# 方法 1: huggingface-cli
huggingface-cli download <模型-id> \
  --local-dir /Users/berton/.omlx/models/<模型目录> \
  --local-dir-use-symlinks False

# 方法 2: omlx (如果支持)
omlx download <模型-id> --model-dir /Users/berton/.omlx/models/
```

---

### 🟡 部分更新（约 20% 的情况）

**触发条件：**
- `config.json` 配置文件变更
- `tokenizer.json` 分词器文件变更
- 特殊文件（如 `generation_config.json`）变更

**原因：**
- 这些文件影响模型的行为，但不是权重本身
- 可能修复了 bug 或改进了生成参数

**操作：**
```bash
# 方法 1: 只下载更新的文件
huggingface-cli download <模型-id> \
  --local-dir /Users/berton/.omlx/models/<模型目录> \
  --local-dir-use-symlinks False \
  --resume-download

# 方法 2: 手动替换单个文件
# 下载新的 config.json，替换本地文件
```

---

### 🟢 无需操作（约 70% 的情况）

**触发条件：**
- `README.md` 说明文件变更
- `.metadata.json` 元数据变更
- 其他非关键文件变更

**原因：**
- 这些文件不影响模型运行
- 只是说明文档或元信息的更新

**操作：**
- 无需任何操作
- 模型可以正常使用

---

## 📋 你的模型当前状态

根据检查结果：

| 模型 | 更新时间 | 状态 | 建议 |
|-----|---------|------|------|
| gemma-4-26b-a4b-it-4bit | 11 天前 | 🟢 正常 | 无需操作 |
| gemma-4-31b-it-4bit | 11 天前 | 🟢 正常 | 无需操作 |
| gemma-4-31b-it-ud-4bit | 11 天前 | 🟢 正常 | 无需操作 |
| **Qwen3.6-27B-4bit** | **2 天前** | 🟢 初始上传 | **无需操作** |
| **Qwen3.6-27B-UD-MLX-4bit** | **2 天前** | 🟢 初始上传 | **无需操作** |
| Qwen3.6-35B-A3B-4bit | 8 天前 | 🟢 正常 | 无需操作 |
| supergemma4-26b-uncensored-mlx-4bit-v2 | 12 天前 | 🟢 正常 | 无需操作 |
| nvidia-personaplex-7b-v1 | 53 天前 | ⚪ 较旧 | 关注更新 |

**结论：你的所有模型都是最新的，无需重新下载！**

---

## 🔍 如何判断更新类型

### 方法一：查看提交历史（推荐）

```bash
# 使用 Python 脚本
python3 /Users/berton/Github/omlx/check_commits.py
```

**判断规则：**
- 🔴 看到包含 `.safetensors`、`weight`、`model` 的提交 → 需要重新下载
- 🟡 看到包含 `config`、`tokenizer` 的提交 → 可选更新
- 🟢 只看到 `README`、`metadata` 的提交 → 无需操作

### 方法二：访问 HuggingFace 网页

1. 访问 `https://huggingface.co/<模型-id>/commits/main`
2. 查看最近的提交记录
3. 检查提交信息中的文件列表

### 方法三：使用自动检查脚本

```bash
# 定期运行检查脚本
python3 /Users/berton/Github/omlx/check_model_changes.py
```

---

## 💡 省流建议

### 日常使用
1. **每周运行一次检查脚本**：`python3 check_mlx_model_updates.py`
2. **关注 MLX 转换者**：Follow mlx-community 和 Unsloth
3. **看到更新通知后**：先查看提交历史，再决定是否重新下载

### 重新下载前
1. ✅ 确认 safetensors 文件确实更新了
2. ✅ 检查本地磁盘空间（15GB+）
3. ✅ 备份当前模型（可选）：`mv model model.backup`

### 重新下载后
1. ✅ 验证文件完整性：检查 safetensors 文件数量
2. ✅ 测试模型运行：`omlx serve --model-dir ~/.omlx/models`
3. ✅ 对比性能：确保更新后性能正常

---

## 🛠️ 实用工具

### 检查模型更新
```bash
python3 /Users/berton/Github/omlx/check_mlx_model_updates.py
```

### 检查更新类型
```bash
python3 /Users/berton/Github/omlx/check_model_changes.py
```

### 检查提交历史
```bash
python3 /Users/berton/Github/omlx/check_commits.py
```

---

## 📚 相关资源

- **MLX Community**: https://huggingface.co/mlx-community
- **Unsloth**: https://huggingface.co/unsloth
- **HuggingFace 文档**: https://huggingface.co/docs/huggingface_hub

---

*最后更新：2026-04-25*
*你的模型状态：全部最新 ✅*
