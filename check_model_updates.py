#!/usr/bin/env python3
"""
检查 HuggingFace 模型更新
"""
from huggingface_hub import HfApi
from datetime import datetime, timezone

api = HfApi()

# 你的模型列表
models = {
    "gemma-4-26b-a4b-it": "google/gemma-4-26b-a4b-it",
    "gemma-4-31b-it": "google/gemma-4-31b-it",
    "gemma-4-31b-it-ud": "google/gemma-4-31B-it",
    "Qwen3.6-27B": "Qwen/Qwen3.6-27B",
    "Qwen3.6-35B-A3B": "Qwen/Qwen3.6-35B-A3B",
    "moshiko": "kyutai/moshiko-pytorch-bf16",
}

print("=" * 60)
print("📦 HuggingFace 模型更新检查")
print("=" * 60)

for local_name, hf_model_id in models.items():
    try:
        model_info = api.model_info(hf_model_id)

        # 转换时间为本地时区
        if model_info.last_modified:
            last_modified = model_info.last_modified.astimezone()
            time_ago = datetime.now(timezone.utc) - model_info.last_modified

            print(f"\n📌 {local_name}")
            print(f"   HF ID: {hf_model_id}")
            print(f"   最后更新: {last_modified.strftime('%Y-%m-%d %H:%M:%S')}")

            # 友好的时间显示
            days = time_ago.days
            if days == 0:
                print(f"   更新时间: 今天")
            elif days == 1:
                print(f"   更新时间: 昨天")
            elif days < 7:
                print(f"   更新时间: {days} 天前")
            elif days < 30:
                weeks = days // 7
                print(f"   更新时间: {weeks} 周前")
            else:
                months = days // 30
                print(f"   更新时间: {months} 个月前")

            print(f"   下载量: {model_info.downloads:,}")
            print(f"   Likes: {model_info.likes}")

    except Exception as e:
        print(f"\n❌ {local_name}: {e}")

print("\n" + "=" * 60)
print("💡 提示: 访问 https://huggingface.co/<model-id> 点击 Follow 获取更新通知")
print("=" * 60)
