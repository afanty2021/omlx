#!/usr/bin/env python3
"""
检查 MLX 模型更新 - 正确版本
"""
from huggingface_hub import HfApi
from datetime import datetime, timezone

api = HfApi()

# 你的 MLX 模型列表（真正的来源）
mlx_models = [
    {
        "local_name": "gemma-4-26b-a4b-it-4bit",
        "mlx_id": "mlx-community/gemma-4-26b-a4b-it-4bit",
        "author": "mlx-community",
        "author_url": "https://huggingface.co/mlx-community",
        "base_model": "google/gemma-4-26b-a4b-it"
    },
    {
        "local_name": "gemma-4-31b-it-4bit",
        "mlx_id": "mlx-community/gemma-4-31b-it-4bit",
        "author": "mlx-community",
        "author_url": "https://huggingface.co/mlx-community",
        "base_model": "google/gemma-4-31b-it"
    },
    {
        "local_name": "gemma-4-31b-it-ud-4bit",
        "mlx_id": "unsloth/gemma-4-31b-it-UD-MLX-4bit",
        "author": "unsloth",
        "author_url": "https://huggingface.co/unsloth",
        "base_model": "google/gemma-4-31B-it"
    },
    {
        "local_name": "Qwen3.6-27B-4bit",
        "mlx_id": "mlx-community/Qwen3.6-27B-4bit",
        "author": "mlx-community",
        "author_url": "https://huggingface.co/mlx-community",
        "base_model": "Qwen/Qwen3.6-27B"
    },
    {
        "local_name": "Qwen3.6-27B-UD-MLX-4bit",
        "mlx_id": "unsloth/Qwen3.6-27B-UD-MLX-4bit",
        "author": "unsloth",
        "author_url": "https://huggingface.co/unsloth",
        "base_model": "Qwen/Qwen3.6-27B"
    },
    {
        "local_name": "Qwen3.6-35B-A3B-4bit",
        "mlx_id": "mlx-community/Qwen3.6-35B-A3B-4bit",
        "author": "mlx-community",
        "author_url": "https://huggingface.co/mlx-community",
        "base_model": "Qwen/Qwen3.6-35B-A3B"
    },
    {
        "local_name": "supergemma4-26b-uncensored-mlx-4bit-v2",
        "mlx_id": "Jiunsong/supergemma4-26b-uncensored-mlx-4bit-v2",
        "author": "Jiunsong",
        "author_url": "https://huggingface.co/Jiunsong",
        "base_model": "google/gemma-4-26B-A4B-it"
    },
    {
        "local_name": "nvidia-personaplex-7b-v1",
        "mlx_id": "nvidia/PersonaPlex-7b-v1",
        "author": "nvidia",
        "author_url": "https://huggingface.co/nvidia",
        "base_model": "kyutai/moshiko-pytorch-bf16"
    },
]

print("=" * 80)
print("📦 MLX 模型更新检查 - 你的模型真正来源")
print("=" * 80)

# 收集需要关注的作者
authors_to_follow = {}
updated_models = []

for model in mlx_models:
    try:
        model_info = api.model_info(model["mlx_id"])

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
                if days <= 7:
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
            print(f"   MLX 版本: {model['mlx_id']}")
            print(f"   作者: {model['author']}")
            print(f"   原始模型: {model['base_model']}")
            print(f"   最后更新: {last_modified.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   {time_str}")
            print(f"   📥 {model_info.downloads:,} 次下载 | 👍 {model_info.likes} 点赞")

            # 收集作者信息
            if model['author'] not in authors_to_follow:
                authors_to_follow[model['author']] = model['author_url']

    except Exception as e:
        print(f"\n❌ {model['local_name']}: {str(e)[:80]}...")

# Follow 建议
print("\n" + "=" * 80)
print("👥 推荐关注的 MLX 模型转换者（点击链接访问并点击 Follow）")
print("=" * 80)

for author, url in sorted(authors_to_follow.items()):
    print(f"\n🔹 {author}: {url}")

# 最近更新的模型
if updated_models:
    print("\n" + "=" * 80)
    print("🆕 最近有更新的 MLX 模型（7天内）")
    print("=" * 80)
    for model in updated_models:
        print(f"\n✨ {model['local_name']}")
        print(f"   MLX ID: {model['mlx_id']}")
        print(f"   作者: {model['author']}")

print("\n" + "=" * 80)
print("💡 提示:")
print("   1. Follow 上述作者/组织，获取 MLX 模型更新")
print("   2. MLX 模型由社区维护，更新可能滞后于原始模型")
print("   3. 原始模型更新后，MLX 版本通常需要几周时间跟进")
print("=" * 80)
