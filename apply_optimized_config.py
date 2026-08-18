#!/usr/bin/env python3
"""
自动应用 omlx 优化配置
"""

import json
import os
import shutil
from pathlib import Path

def backup_existing_config():
    """备份现有配置"""
    config_path = Path.home() / ".omlx" / "model_settings.json"

    if config_path.exists():
        backup_path = config_path.with_suffix('.json.backup')
        shutil.copy(config_path, backup_path)
        print(f"✓ 已备份现有配置到: {backup_path}")
        return True
    else:
        print("✗ 未找到现有配置文件")
        return False

def apply_qwen_optimization():
    """应用 Qwen 模型优化配置"""
    config_path = Path.home() / ".omlx" / "model_settings.json"

    # 创建配置目录
    config_path.parent.mkdir(parents=True, exist_ok=True)

    # 读取现有配置
    existing_config = {}
    if config_path.exists():
        with open(config_path, 'r') as f:
            existing_config = json.load(f)

    # Qwen 优化配置
    qwen_optimization = {
        "max_tokens": 4096,
        "max_context_window": 8192,
        "temperature": 0.7,
        "top_p": 0.9,
        "turboquant_kv_enabled": True,
        "turboquant_kv_bits": 3,
        "turboquant_skip_last": True,
        "ttl_seconds": 300,
        "dflash_enabled": False,
        "is_pinned": False,
        "is_default": True
    }

    # 更新配置
    if "models" not in existing_config:
        existing_config["models"] = {}

    # 尝试找到 Qwen 模型
    qwen_models = [k for k in existing_config["models"].keys() if "qwen" in k.lower()]

    if qwen_models:
        # 更新现有的 Qwen 模型配置
        for model_id in qwen_models:
            print(f"✓ 更新模型配置: {model_id}")
            existing_config["models"][model_id].update(qwen_optimization)
    else:
        # 创建通用 Qwen 配置模板
        print("✓ 创建 Qwen 通用配置模板")
        existing_config["models"]["Qwen3.6-35B-A3B-4bit"] = qwen_optimization

    # 保存配置
    with open(config_path, 'w') as f:
        json.dump(existing_config, f, indent=2, ensure_ascii=False)

    print(f"✓ 配置已保存到: {config_path}")

def create_startup_script():
    """创建启动脚本"""
    script_dir = Path.home() / "omlx-scripts"
    script_dir.mkdir(parents=True, exist_ok=True)

    # 这里可以添加自定义的启动脚本内容
    print(f"✓ 脚本目录: {script_dir}")

def main():
    """主函数"""
    print("=" * 60)
    print("omlx 优化配置应用工具")
    print("=" * 60)
    print()

    # 备份现有配置
    print("1. 备份现有配置...")
    backup_existing_config()
    print()

    # 应用优化配置
    print("2. 应用 Qwen 模型优化...")
    apply_qwen_optimization()
    print()

    # 完成
    print("=" * 60)
    print("配置应用完成!")
    print("=" * 60)
    print()
    print("下一步:")
    print("1. 使用优化启动脚本: ./start_optimized.sh")
    print("2. 或手动启动: omlx serve --memory-guard-gb 40")
    print()

if __name__ == "__main__":
    main()
