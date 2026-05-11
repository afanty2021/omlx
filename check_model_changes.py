#!/usr/bin/env python3
"""
检查 MLX 模型是否需要重新下载
分析更新类型并提供更新建议
"""
from huggingface_hub import HfApi
from huggingface_hub import scan_cache_dir
from datetime import datetime, timezone
import os

api = HfApi()

# 你的 MLX 模型列表
mlx_models = [
    {"local_name": "gemma-4-26b-a4b-it-4bit", "mlx_id": "mlx-community/gemma-4-26b-a4b-it-4bit"},
    {"local_name": "gemma-4-31b-it-4bit", "mlx_id": "mlx-community/gemma-4-31b-it-4bit"},
    {"local_name": "gemma-4-31b-it-ud-4bit", "mlx_id": "unsloth/gemma-4-31b-it-UD-MLX-4bit"},
    {"local_name": "Qwen3.6-27B-4bit", "mlx_id": "mlx-community/Qwen3.6-27B-4bit"},
    {"local_name": "Qwen3.6-27B-UD-MLX-4bit", "mlx_id": "unsloth/Qwen3.6-27B-UD-MLX-4bit"},
    {"local_name": "Qwen3.6-35B-A3B-4bit", "mlx_id": "mlx-community/Qwen3.6-35B-A3B-4bit"},
    {"local_name": "supergemma4-26b-uncensored-mlx-4bit-v2", "mlx_id": "Jiunsong/supergemma4-26b-uncensored-mlx-4bit-v2"},
    {"local_name": "nvidia-personaplex-7b-v1", "mlx_id": "nvidia/PersonaPlex-7b-v1"},
]

print("=" * 80)
print("📦 MLX 模型更新分析")
print("=" * 80)

print("\n📋 更新类型说明:")
print("   🔴 需要重新下载: safetensors 权重文件变更")
print("   🟡 部分更新: 配置或分词器文件变更")
print("   🟢 无需更新: 仅 README 或说明文件变更")
print("   ⚪ 无法判断: 无法获取本地文件信息")
print("\n" + "=" * 80)

for model in mlx_models:
    local_path = f"/Users/berton/.omlx/models/{model['local_name']}"

    if not os.path.exists(local_path):
        print(f"\n❌ {model['local_name']}")
        print(f"   本地路径不存在: {local_path}")
        continue

    try:
        # 获取远程模型信息
        model_info = api.model_info(model["mlx_id"])

        # 获取远程文件列表
        repo_files = api.list_repo_files(model["mlx_id"], repo_type="model")

        # 分类文件
        weight_files = [f for f in repo_files if f.endswith('.safetensors')]
        config_files = [f for f in repo_files if f.endswith('.json') and not f.endswith('.metadata.json')]
        readme_files = [f for f in repo_files if 'README' in f.upper()]

        # 获取最后修改时间
        if model_info.last_modified:
            last_modified = model_info.last_modified.astimezone()
            time_ago = (datetime.now(timezone.utc) - model_info.last_modified).days

            print(f"\n📌 {model['local_name']}")
            print(f"   MLX ID: {model['mlx_id']}")
            print(f"   最后更新: {last_modified.strftime('%Y-%m-%d %H:%M:%S')} ({time_ago}天前)")

            # 分析更新建议
            print(f"\n   📁 文件构成:")
            print(f"      权重文件: {len(weight_files)} 个")
            print(f"      配置文件: {len(config_files)} 个")
            print(f"      说明文件: {len(readme_files)} 个")

            # 检查本地权重文件
            local_weights = []
            for wf in weight_files:
                local_wf = os.path.join(local_path, wf)
                if os.path.exists(local_wf):
                    local_weights.append(wf)

            # 更新建议
            print(f"\n   💡 更新建议:")

            if time_ago > 30:
                print(f"      ⚪ 模型较旧 ({time_ago} 天前)")
                print(f"      建议检查是否有新版本发布")
                print(f"      如果有新版本，需要重新下载")
            elif time_ago <= 7:
                print(f"      🔴 模型刚更新 ({time_ago} 天前)")
                print(f"      ⚠️  可能需要重新下载")
                print(f"      建议:")
                print(f"         1. 查看模型的 Commit History")
                print(f"         2. 如果只更新了 README，无需重新下载")
                print(f"         3. 如果更新了 .safetensors，需要重新下载")
            else:
                print(f"      🟢 模型状态正常 ({time_ago} 天前)")
                print(f"      无需更新")

            # 检查本地文件完整性
            if len(local_weights) == len(weight_files):
                print(f"\n   ✅ 本地文件完整")
                print(f"      {len(local_weights)}/{len(weight_files)} 个权重文件存在")
            else:
                print(f"\n   ⚠️  本地文件不完整")
                print(f"      {len(local_weights)}/{len(weight_files)} 个权重文件存在")
                print(f"      建议重新下载")

    except Exception as e:
        print(f"\n❌ {model['local_name']}")
        print(f"   检查失败: {str(e)[:60]}...")

print("\n" + "=" * 80)
print("🔧 如何更新模型:")
print("=" * 80)
print("""
1. 查看更新历史:
   huggingface-cli repo list <model-id>

2. 查看具体改动:
   访问 https://huggingface.co/<model-id>/commits/main

3. 如果只更新了 README:
   → 无需操作

4. 如果更新了 .safetensors:
   → 删除旧模型目录，重新下载
   → 或使用 omlx 的模型管理功能

5. 使用 omlx 重新下载:
   omlx download <model-id> --model-dir /Users/berton/.omlx/models/
""")

print("=" * 80)
print("💡 省流建议:")
print("=" * 80)
print("""
- MLX 模型更新频率低，通常几个月才一次
- 大多数更新只是 README 修改，无需重新下载
- 只有看到 safetensors 文件变更才需要重新下载
- 15GB 的模型重新下载需要时间，建议先检查更新内容
""")
