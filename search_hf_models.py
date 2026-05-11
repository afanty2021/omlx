#!/usr/bin/env python3
"""
HuggingFace 模型搜索工具
专门搜索 MLX 格式的模型
"""
from huggingface_hub import HfApi
import json

api = HfApi()

print("=" * 80)
print("🔍 HuggingFace MLX 模型搜索")
print("=" * 80)

# 搜索配置
searches = [
    ("Unsloth MLX 模型", "unsloth mlx"),
    ("MLX Community 模型", "mlx-community"),
    ("Qwen MLX", "qwen mlx"),
    ("Gemma MLX", "gemma mlx"),
]

for search_name, search_query in searches:
    print(f"\n📌 {search_name}")
    print(f"   搜索: {search_query}")
    print(f"   链接: https://huggingface.co/models?search={search_query.replace(' ', '+')}")
    print()

    try:
        # 使用 HuggingFace API 搜索
        models = list(api.list_models(
            search=search_query,
            limit=10,
            sort="downloads",
            direction=-1
        ))

        if models:
            print(f"   找到 {len(models)} 个热门模型:")
            for i, model in enumerate(models[:5], 1):
                # 获取模型信息
                try:
                    model_info = api.model_info(model.modelId)

                    # 计算模型大小（估算）
                    size_gb = "未知"
                    if model_info.safetensors:
                        total_size = sum(s.size for s in model_info.safetensors.values()) if isinstance(model_info.safetensors, dict) else 0
                        if total_size > 0:
                            size_gb = f"{total_size / 1024 / 1024 / 1024:.1f} GB"

                    print(f"\n   {i}. {model.modelId}")
                    print(f"      下载: {model.downloads:,} | 点赞: {model.likes}")
                    print(f"      大小: {size_gb}")
                    if model_info.last_modified:
                        print(f"      更新: {model_info.last_modified.strftime('%Y-%m-%d')}")
                except:
                    print(f"\n   {i}. {model.modelId}")
                    print(f"      下载: {model.downloads:,} | 点赞: {model.likes}")
        else:
            print("   未找到匹配的模型")

    except Exception as e:
        print(f"   搜索失败: {str(e)[:60]}...")

    print()

print("=" * 80)
print("🔗 直接访问链接")
print("=" * 80)
print("""
Unsloth 所有模型:
https://huggingface.co/unsloth?type=model

MLX Community 所有模型:
https://huggingface.co/mlx-community?type=model

搜索所有 MLX 模型:
https://huggingface.co/models?search=mlx

搜索 Qwen MLX:
https://huggingface.co/models?search=qwen+mlx

搜索 Gemma MLX:
https://huggingface.co/models?search=gemma+mlx
""")

print("=" * 80)
print("💡 搜索技巧")
print("=" * 80)
print("""
1. 在 HuggingFace 搜索框输入:
   "unsloth mlx" - 搜索 Unsloth 的 MLX 模型
   "mlx-community" - 搜索 MLX Community 的模型
   "qwen mlx" - 搜索 Qwen 的 MLX 版本
   "gemma mlx" - 搜索 Gemma 的 MLX 版本

2. 过滤条件:
   - 点击 "Models" 标签
   - 选择 "Text Generation" 或其他任务类型
   - 按下载量排序（Most downloads）

3. 识别 MLX 模型:
   - 文件包含 .safetensors
   - 标签有 "mlx"
   - README 中提到 MLX 或 Apple Silicon

4. 避免混淆:
   - GGUF = 不兼容 omlx
   - MLX = 兼容 omlx ✅
""")
