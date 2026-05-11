#!/usr/bin/env python3
"""
检查模型的具体更新内容
判断是否需要重新下载
"""
from huggingface_hub import HfApi

api = HfApi()

# 检查刚更新的模型
models_to_check = [
    ("Qwen3.6-27B-4bit", "mlx-community/Qwen3.6-27B-4bit"),
    ("Qwen3.6-27B-UD-MLX-4bit", "unsloth/Qwen3.6-27B-UD-MLX-4bit"),
]

print("=" * 80)
print("🔍 检查最近更新的模型")
print("=" * 80)

for local_name, model_id in models_to_check:
    print(f"\n📌 {local_name}")
    print(f"   模型: {model_id}")
    print(f"   链接: https://huggingface.co/{model_id}/commits/main")
    print("\n   最近 5 次提交:")

    try:
        commits = list(api.list_repo_commits(model_id, repo_type="model"))

        for i, commit in enumerate(commits[:5]):
            # 提取提交标题的前 80 个字符
            title = commit.title[:80] if len(commit.title) > 80 else commit.title

            # 检查是否涉及权重文件
            has_safetensors = any(ext in commit.title for ext in ['.safetensors', 'weight', 'model'])
            has_config = any(ext in commit.title for ext in ['config', 'json'])

            if has_safetensors:
                indicator = "🔴"
                recommendation = "→ 需要重新下载"
            elif has_config:
                indicator = "🟡"
                recommendation = "→ 可能需要更新配置"
            else:
                indicator = "🟢"
                recommendation = "→ 无需重新下载"

            print(f"\n   {indicator} {commit.created_at.strftime('%Y-%m-%d %H:%M')}")
            print(f"      {title}")
            print(f"      {recommendation}")

    except Exception as e:
        print(f"\n   ❌ 无法获取提交历史: {str(e)[:60]}...")

print("\n" + "=" * 80)
print("📋 更新决策指南:")
print("=" * 80)
print("""
🔴 需要重新下载:
   - 看到包含 .safetensors 的提交
   - 看到包含 "weight", "model" 等关键词的提交
   - 操作: 删除旧目录，重新下载

🟡 可选更新:
   - 看到包含 config.json 的提交
   - 看到包含 "config", "tokenizer" 的提交
   - 操作: 可以手动更新配置文件，或重新下载

🟢 无需操作:
   - 只看到 README.md 更新
   - 只看到 .metadata.json 更新
   - 操作: 无需任何操作
""")

print("=" * 80)
print("🔧 更新命令:")
print("=" * 80)
print("""
# 如果需要重新下载，使用以下命令:

# 方法 1: 使用 huggingface-cli
huggingface-cli download <model-id> \
  --local-dir /Users/berton/.omlx/models/<本地目录名> \
  --local-dir-use-symlinks False

# 方法 2: 使用 git（如果模型仓库支持）
cd /Users/berton/.omlx/models/<本地目录名>
git pull

# 方法 3: 手动删除后重新下载
rm -rf /Users/berton/.omlx/models/<本地目录名>
# 然后使用你平时的下载方法
""")
