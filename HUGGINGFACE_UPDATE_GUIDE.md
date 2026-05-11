# HuggingFace 模型更新监控指南

## 📋 你的模型列表

| 本地目录 | HuggingFace 模型 | 作者 | 状态 |
|---------|-----------------|------|------|
| gemma-4-26b-a4b-it-4bit | google/gemma-4-26b-a4b-it | Google | 2 周前 |
| gemma-4-31b-it-4bit | google/gemma-4-31b-it | Google | 2 周前 |
| gemma-4-31b-it-ud-4bit | google/gemma-4-31B-it | Google | 2 周前 |
| Qwen3.6-27B-4bit | Qwen/Qwen3.6-27B | Qwen | ✨ 昨天 |
| Qwen3.6-35B-A3B-4bit | Qwen/Qwen3.6-35B-A3B | Qwen | ✨ 昨天 |
| supergemma4-26b-uncensored-mlx-4bit-v2 | Jiunsong/supergemma4-26b-uncensored-gguf-v2 | Jiunsong | 1 周前 |
| nvidia-personaplex-7b-v1 | kyutai/moshiko-pytorch-bf16 | Kyutai | 19 个月前 |

## 🔔 获取更新通知的方法

### 方法一：Follow 模型作者（推荐）

访问以下链接并点击 **Follow** 按钮：

1. **Google** (Gemma 系列)
   - https://huggingface.co/google
   - 关注后获取所有 Gemma 模型更新

2. **Qwen** (通义千问系列)
   - https://huggingface.co/Qwen
   - 关注后获取所有 Qwen 模型更新

3. **Jiunsong** (SuperGemma 作者)
   - https://huggingface.co/Jiunsong
   - 关注后获取 SuperGemma 更新

4. **Kyutai** (Moshiko/Moshi)
   - https://huggingface.co/kyutai
   - 关注后获取语音模型更新

**Follow 后的效果：**
- 在 HuggingFace 首页看到新模型发布
- 活动时间线显示关注对象的动态

### 方法二：定期运行检查脚本

```bash
# 运行完整检查脚本
python3 /Users/berton/Github/omlx/check_model_updates_v2.py

# 或使用简化版
python3 /Users/berton/Github/omlx/check_model_updates.py
```

### 方法三：设置自动检查（可选）

```bash
# 编辑 crontab
crontab -e

# 添加每天早上 9 点检查
0 9 * * * /usr/bin/python3 /Users/berton/Github/omlx/check_model_updates_v2.py >> ~/.omlx/model_updates.log 2>&1
```

## 🚨 重要更新提醒

### 最近更新的模型（7天内）
- ✨ **Qwen3.6-27B** - 昨天更新
- ✨ **Qwen3.6-35B-A3B** - 昨天更新

建议检查更新内容，看是否需要更新本地模型。

## 📚 相关链接

- **HuggingFace 首页**: https://huggingface.co
- **你的模型目录**: `/Users/berton/.omlx/models/`
- **更新检查脚本**: `/Users/berton/Github/omlx/check_model_updates_v2.py`

## 💡 常见问题

**Q: Follow 和 Like 有什么区别？**
- A: Like (❤️) 是给模型点赞，Follow 是关注作者/组织。Follow 后可以看到该作者的所有新模型。

**Q: 如何知道模型有新版本？**
- A: Follow 作者 + 定期运行检查脚本

**Q: 模型更新后需要重新下载吗？**
- A: 不一定。小更新（如 README 修改）不需要重新下载。权重更新才需要。

---

*最后更新: 2026-04-25*
