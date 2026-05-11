# MLX 模型更新监控指南（正确版）

> 更新时间：2026-04-25

## 📋 你的 MLX 模型列表

| 本地目录 | MLX 版本 | 转换者 | 原始模型 | 最后更新 |
|---------|---------|--------|---------|---------|
| **gemma-4-26b-a4b-it-4bit** | mlx-community/gemma-4-26b-a4b-it-4bit | MLX Community | google/gemma-4-26b-a4b-it | 1 周前 |
| **gemma-4-31b-it-4bit** | mlx-community/gemma-4-31b-it-4bit | MLX Community | google/gemma-4-31b-it | 1 周前 |
| **gemma-4-31b-it-ud-4bit** | unsloth/gemma-4-31b-it-UD-MLX-4bit | Unsloth | google/gemma-4-31B-it | 1 周前 |
| **Qwen3.6-27B-4bit** | mlx-community/Qwen3.6-27B-4bit | MLX Community | Qwen/Qwen3.6-27B | ✨ 2 天前 |
| **Qwen3.6-27B-UD-MLX-4bit** | unsloth/Qwen3.6-27B-UD-MLX-4bit | Unsloth | Qwen/Qwen3.6-27B | ✨ 2 天前 |
| **Qwen3.6-35B-A3B-4bit** | mlx-community/Qwen3.6-35B-A3B-4bit | MLX Community | Qwen/Qwen3.6-35B-A3B | 1 周前 |
| **supergemma4-26b-uncensored-mlx-4bit-v2** | Jiunsong/supergemma4-26b-uncensored-mlx-4bit-v2 | Jiunsong | google/gemma-4-26B-A4B-it | 1 周前 |
| **nvidia-personaplex-7b-v1** | nvidia/PersonaPlex-7b-v1 | NVIDIA | kyutai/moshiko-pytorch-bf16 | 1 个月前 |

## 👥 需要关注的 MLX 转换者

### ✅ 已关注
- ✅ **Jiunsong** - SuperGemma 系列
  - https://huggingface.co/Jiunsong

### 🔔 推荐关注

#### 1. **MLX Community** ⭐ 重要
- **链接**: https://huggingface.co/mlx-community
- **作用**: 维护大部分 MLX 模型转换
- **你的模型**:
  - gemma-4-26b-a4b-it-4bit
  - gemma-4-31b-it-4bit
  - Qwen3.6-27B-4bit
  - Qwen3.6-35B-A3B-4bit

#### 2. **Unsloth** ⭐ 重要
- **链接**: https://huggingface.co/unsloth
- **作用**: 提供优化的 MLX 模型（UD = Unsloth）
- **你的模型**:
  - gemma-4-31b-it-ud-4bit
  - Qwen3.6-27B-UD-MLX-4bit

#### 3. **NVIDIA**
- **链接**: https://huggingface.co/nvidia
- **作用**: 官方 NVIDIA 模型
- **你的模型**:
  - nvidia-personaplex-7b-v1

## 🔴 最近更新的 MLX 模型

### 2 天内更新
- ✨ **Qwen3.6-27B-4bit** (MLX Community 版本)
- ✨ **Qwen3.6-27B-UD-MLX-4bit** (Unsloth 版本)

这些 MLX 版本刚刚更新！建议检查更新内容。

## 🛠️ 检查更新的工具

### 方法一：运行 Python 脚本
```bash
python3 /Users/berton/Github/omlx/check_mlx_model_updates.py
```

### 方法二：设置自动检查
```bash
# 编辑 crontab
crontab -e

# 添加每天早上 9 点检查
0 9 * * * /usr/bin/python3 /Users/berton/Github/omlx/check_mlx_model_updates.py >> ~/.omlx/mlx_updates.log 2>&1
```

## 💡 重要提示

### MLX 模型更新的特点

1. **更新滞后**: MLX 版本通常比原始模型晚几周更新
2. **社区维护**: MLX Community 和 Unsloth 是社区组织，不是官方
3. **转换时间**: 原始模型更新后，需要等待 MLX 转换

### 更新策略

1. **Follow 转换者** - 获取 MLX 版本更新通知
2. **关注原始模型作者** - 了解原始模型何时更新
3. **定期检查** - 使用脚本自动检查

## 📚 相关链接

- **MLX Community**: https://huggingface.co/mlx-community
- **Unsloth**: https://huggingface.co/unsloth
- **检查脚本**: `/Users/berton/Github/omlx/check_mlx_model_updates.py`
- **你的模型目录**: `/Users/berton/.omlx/models/`

## 🔗 快速访问

| 转换者 | 链接 | 状态 |
|--------|------|------|
| MLX Community | https://huggingface.co/mlx-community | ⬜ 未关注 |
| Unsloth | https://huggingface.co/unsloth | ⬜ 未关注 |
| NVIDIA | https://huggingface.co/nvidia | ⬜ 未关注 |
| Jiunsong | https://huggingface.co/Jiunsong | ✅ 已关注 |

---

*最后更新: 2026-04-25*
