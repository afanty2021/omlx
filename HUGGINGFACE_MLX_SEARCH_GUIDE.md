# HuggingFace 搜索 Unsloth MLX 模型指南

> 最后更新：2026-04-25

## 🔍 方法一：直接搜索链接（最快）

### Unsloth MLX 模型
```
https://huggingface.co/models?search=unsloth+mlx
```

### Qwen MLX 模型
```
https://huggingface.co/models?search=qwen+mlx
```

### Gemma MLX 模型
```
https://huggingface.co/models?search=gemma+mlx
```

### 所有 MLX 模型
```
https://huggingface.co/models?search=mlx
```

---

## 🔍 方法二：访问组织主页

### Unsloth 主页
1. 访问：https://huggingface.co/unsloth
2. 点击 "Models" 标签
3. 在搜索框输入：`mlx`

### MLX Community 主页
1. 访问：https://huggingface.co/mlx-community
2. 浏览所有 MLX 模型

---

## 🔍 方法三：使用搜索脚本

```bash
# 运行搜索脚本
python3 /Users/berton/Github/omlx/search_hf_models.py
```

---

## 📋 热门 Unsloth MLX 模型

### Qwen 系列

| 模型 | 下载量 | 用途 |
|-----|-------|------|
| `unsloth/Qwen3.6-35B-A3B-UD-MLX-4bit` | 50K+ | 多模态推理 |
| `unsloth/Qwen3.6-27B-UD-MLX-4bit` | 21K+ | 通用对话 ✅ 你有这个 |
| `unsloth/Qwen3.6-35B-A3B-MLX-8bit` | 14K+ | 高精度 |

### Gemma 系列

| 模型 | 下载量 | 用途 |
|-----|-------|------|
| `unsloth/gemma-4-31b-it-UD-MLX-4bit` | 13K+ | 多模态 ✅ 你有这个 |
| `unsloth/gemma-4-26B-A4B-it-MLX-4bit` | 8K+ | 工具使用 |

---

## 🎯 识别 MLX 模型的要点

### ✅ 正确的格式（omlx 兼容）

**文件特征：**
- ✅ 包含 `.safetensors` 文件
- ✅ 包含 `config.json`
- ✅ 标签中有 `mlx`

**命名特征：**
- ✅ 包含 `-MLX-` 或 `MLX-`
- ✅ 作者：`mlx-community` 或 `unsloth`
- ✅ README 中提到 MLX 或 Apple Silicon

### ❌ 错误的格式（omlx 不兼容）

**文件特征：**
- ❌ 包含 `.gguf` 文件
- ❌ 包含 `.ggml` 文件

**命名特征：**
- ❌ 包含 `-GGUF` 或 `GGUF-`
- ❌ 集合名称包含 "GGUF"

---

## 📊 搜索结果对比

### Unsloth MLX vs Unsloth GGUF

| 搜索词 | 结果 | 兼容性 |
|--------|------|--------|
| `unsloth mlx` | MLX 格式 | ✅ omlx 兼容 |
| `unsloth gguf` | GGUF 格式 | ❌ 不兼容 |

### 示例模型对比

| MLX 版本 ✅ | GGUF 版本 ❌ |
|------------|-------------|
| `unsloth/Qwen3.6-27B-UD-MLX-4bit` | `unsloth/Qwen3.6-27B-GGUF` |
| `unsloth/gemma-4-31b-it-UD-MLX-4bit` | `unsloth/gemma-4-31B-it-GGUF` |

---

## 💡 搜索技巧

### 1. 组合搜索
```
unsloth qwen mlx     → Unsloth 的 Qwen MLX 模型
mlx-community gemma  → MLX Community 的 Gemma 模型
```

### 2. 排除不相关结果
```
mlx -gguf          → MLX 模型，排除 GGUF
unsloth -gguf mlx  → Unsloth MLX，排除 GGUF
```

### 3. 使用过滤条件
- 按下载量排序（Most downloads）
- 选择任务类型（Text Generation）
- 选择模型大小（如 10B-30B）

---

## 🔧 已创建的工具

1. **search_hf_models.py** - Python 搜索脚本
   ```bash
   python3 /Users/berton/Github/omlx/search_hf_models.py
   ```

2. **search_unsloth_mlx.sh** - 快速链接
   ```bash
   bash /Users/berton/Github/omlx/search_unsloth_mlx.sh
   ```

---

## 📚 快速参考

### 你当前拥有的模型 ✅

- `unsloth/Qwen3.6-27B-UD-MLX-4bit`
- `unsloth/gemma-4-31b-it-UD-MLX-4bit`

### 可以考虑的新模型

- `unsloth/Qwen3.6-35B-A3B-UD-MLX-4bit` (更大，更强)
- `mlx-community/gemma-4-26b-a4b-it-4bit` (MLX Community 版本)

---

## 🌐 相关链接

- **Unsloth**: https://huggingface.co/unsloth
- **MLX Community**: https://huggingface.co/mlx-community
- **MLX 搜索**: https://huggingface.co/models?search=mlx

---

*最后更新：2026-04-25*
