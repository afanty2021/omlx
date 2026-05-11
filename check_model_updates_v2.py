#!/usr/bin/env python3
"""
检查 HuggingFace 模型更新 - 完整版
包含组织/作者 Follow 建议
"""
from huggingface_hub import HfApi
from datetime import datetime, timezone
import json

api = HfApi()

# 你的模型列表及其作者
models = [
    {
        "local_name": "gemma-4-26b-a4b-it",
        "hf_id": "google/gemma-4-26b-a4b-it",
        "author": "google",
        "author_url": "https://huggingface.co/google"
    },
    {
        "local_name": "gemma-4-31b-it",
        "hf_id": "google/gemma-4-31b-it",
        "author": "google",
        "author_url": "https://huggingface.co/google"
    },
    {
        "local_name": "gemma-4-31b-it-ud",
        "hf_id": "google/gemma-4-31B-it",
        "author": "google",
        "author_url": "https://huggingface.co/google"
    },
    {
        "local_name": "Qwen3.6-27B",
        "hf_id": "Qwen/Qwen3.6-27B",
        "author": "Qwen",
        "author_url": "https://huggingface.co/Qwen"
    },
    {
        "local_name": "Qwen3.6-35B-A3B",
        "hf_id": "Qwen/Qwen3.6-35B-A3B",
        "author": "Qwen",
        "author_url": "https://huggingface.co/Qwen"
    },
    {
        "local_name": "supergemma4-26b-uncensored-mlx-4bit-v2",
        "hf_id": "Jiunsong/supergemma4-26b-uncensored-gguf-v2",
        "author": "Jiunsong",
        "author_url": "https://huggingface.co/Jiunsong"
    },
    {
        "local_name": "nvidia-personaplex-7b-v1",
        "hf_id": "kyutai/moshiko-pytorch-bf16",
        "author": "kyutai",
        "author_url": "https://huggingface.co/kyutai"
    },
]

print("=" * 70)
print("📦 HuggingFace 模型更新检查 + Follow 建议")
print("=" * 70)

# 收集需要关注的作者
authors_to_follow = set()
updated_models = []

for model in models:
    try:
        model_info = api.model_info(model["hf_id"])

        if model_info.last_modified:
            last_modified = model_info.last_modified.astimezone()
            time_ago = datetime.now(timezone.utc) - model_info.last_modified
            days = time_ago.days

            # 友好的时间显示
            if days == 0:
                time_str = "🔴 今天"
                updated_models.append(model)
            elif days == 1:
                time_str = "🟡 昨天"
                if days <= 7:  # 7天内也算更新
                    updated_models.append(model)
            elif days < 7:
                time_str = f"🟢 {days} 天前"
            elif days < 30:
                weeks = days // 7
                time_str = f"🟢 {weeks} 周前"
            else:
                months = days // 30
                time_str = f"⚪ {months} 个月前"

            print(f"\n📌 {model['local_name']}")
            print(f"   HF ID: {model['hf_id']}")
            print(f"   作者: {model['author']} → {model['author_url']}")
            print(f"   最后更新: {last_modified.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   {time_str}")
            print(f"   📥 {model_info.downloads:,} 次下载 | 👍 {model_info.likes} 点赞")

            # 添加到需要关注的作者列表
            authors_to_follow.add((model['author'], model['author_url']))

    except Exception as e:
        print(f"\n❌ {model['local_name']}: {str(e)[:50]}...")

# Follow 建议
print("\n" + "=" * 70)
print("👥 推荐关注的作者/组织（点击链接访问并点击 Follow）")
print("=" * 70)

unique_authors = list(set(authors_to_follow))
for author, url in sorted(unique_authors):
    print(f"\n🔹 {author}: {url}")

# 最近更新的模型
if updated_models:
    print("\n" + "=" * 70)
    print("🆕 最近有更新的模型（7天内）")
    print("=" * 70)
    for model in updated_models:
        print(f"\n✨ {model['local_name']}")
        print(f"   {model['hf_id']}")
        print(f"   作者: {model['author']}")

print("\n" + "=" * 70)
print("💡 提示:")
print("   1. 访问上面的作者链接并点击 Follow 按钮")
print("   2. Follow 后，新模型会出现在你的 HuggingFace 首页")
print("   3. 定期运行此脚本检查更新")
print("=" * 70)
