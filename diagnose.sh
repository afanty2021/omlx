#!/usr/bin/env python3
"""
omlx 性能诊断脚本
用于检查系统状态、配置和潜在问题
"""

import json
import os
import subprocess
import sys
from pathlib import Path

def run_command(cmd):
    """运行 shell 命令并返回输出"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.stdout.strip()
    except Exception as e:
        return f"Error: {e}"

def get_system_info():
    """获取系统信息"""
    print("=" * 60)
    print("系统信息")
    print("=" * 60)

    # 芯片信息
    chip = run_command("sysctl -n machdep.cpu.brand_string")
    print(f"芯片: {chip}")

    # 内存信息
    mem_cmd = "sysctl -n hw.memsize"
    mem_bytes = int(run_command(mem_cmd))
    mem_gb = mem_bytes / (1024**3)
    print(f"总内存: {mem_gb:.1f} GB")

    # 可用内存
    vm_stats = run_command("vm_stat")
    lines = vm_stats.split('\n')
    page_size = 4096
    free_pages = 0
    inactive_pages = 0

    for line in lines:
        if "Pages free:" in line:
            free_pages = int(line.split(':')[1].strip().rstrip('.'))
        elif "Pages inactive:" in line:
            inactive_pages = int(line.split(':')[1].strip().rstrip('.'))

    free_gb = (free_pages * page_size) / (1024**3)
    inactive_gb = (inactive_pages * page_size) / (1024**3)
    available_gb = free_gb + inactive_gb

    print(f"可用内存: {available_gb:.1f} GB (空闲: {free_gb:.1f} GB + 非活动: {inactive_gb:.1f} GB)")

    # Swap 使用情况
    swap_stats = run_command("sysctl -n vm.swapusage")
    print(f"Swap 使用: {swap_stats}")

    print()

def check_omlx_installation():
    """检查 omlx 安装"""
    print("=" * 60)
    print("omlx 安装检查")
    print("=" * 60)

    # 检查 omlx 命令
    omlx_path = run_command("which omlx")
    if omlx_path and "Error" not in omlx_path:
        print(f"✓ omlx 安装位置: {omlx_path}")

        # 获取版本
        version = run_command("omlx --version 2>&1 | head -1")
        print(f"✓ omlx 版本: {version}")
    else:
        print("✗ omlx 未安装或不在 PATH 中")

    # 检查 Python 包
    try:
        import pip
        result = run_command("pip show omlx")
        if result and "Error" not in result:
            for line in result.split('\n'):
                if 'Version:' in line or 'Location:' in line:
                    print(f"✓ {line}")
        else:
            print("✗ omlx Python 包未安装")
    except:
        print("⚠ 无法检查 Python 包")

    print()

def check_configuration():
    """检查配置文件"""
    print("=" * 60)
    print("配置文件检查")
    print("=" * 60)

    config_dir = Path.home() / ".omlx"
    settings_file = config_dir / "model_settings.json"

    if config_dir.exists():
        print(f"✓ 配置目录存在: {config_dir}")
    else:
        print(f"✗ 配置目录不存在: {config_dir}")
        print("  提示: 运行 omlx 会自动创建此目录")

    if settings_file.exists():
        print(f"✓ 模型设置文件存在: {settings_file}")

        try:
            with open(settings_file, 'r') as f:
                settings = json.load(f)

            models = settings.get('models', {})
            if models:
                print(f"✓ 已配置 {len(models)} 个模型:")
                for model_id, config in models.items():
                    print(f"  - {model_id}")
                    if config.get('is_default'):
                        print(f"    [默认]")
                    if config.get('is_pinned'):
                        print(f"    [固定]")
                    if config.get('turboquant_kv_enabled'):
                        print(f"    TurboQuant KV: {config.get('turboquant_kv_bits')} bits")
                    if config.get('dflash_enabled'):
                        print(f"    DFlash: 启用")
        except Exception as e:
            print(f"✗ 无法解析设置文件: {e}")
    else:
        print(f"✗ 模型设置文件不存在: {settings_file}")

    print()

def check_models():
    """检查模型目录"""
    print("=" * 60)
    print("模型检查")
    print("=" * 60)

    model_dirs = [
        Path.home() / "models",
        Path.home() / ".omlx" / "models",
        Path("/Users/berton/Github/models"),
    ]

    found_models = False
    for model_dir in model_dirs:
        if model_dir.exists():
            print(f"✓ 模型目录存在: {model_dir}")

            # 检查 Qwen 模型
            qwen_models = list(model_dir.glob("*Qwen*"))
            if qwen_models:
                print(f"✓ 找到 {len(qwen_models)} 个 Qwen 模型:")
                for model_path in qwen_models:
                    print(f"  - {model_path.name}")
                    # 检查配置文件
                    config_file = model_path / "config.json"
                    if config_file.exists():
                        try:
                            with open(config_file, 'r') as f:
                                config = json.load(f)
                            model_type = config.get('model_type', 'unknown')
                            num_params = config.get('num_parameters', 'unknown')
                            print(f"    类型: {model_type}, 参数: {num_params}")
                        except:
                            pass

            found_models = True
            break

    if not found_models:
        print("✗ 未找到模型目录")
        print("  提示: 请确保模型已下载到 ~/models 或其他位置")

    print()

def check_running_processes():
    """检查运行中的进程"""
    print("=" * 60)
    print("运行进程检查")
    print("=" * 60)

    # 检查 omlx 进程
    omlx_processes = run_command("ps aux | grep -E 'omlx|python.*server' | grep -v grep | grep -v diagnose")

    if omlx_processes:
        print("✓ 发现运行中的 omlx 进程:")
        print(omlx_processes)
    else:
        print("✗ 没有运行中的 omlx 进程")

    # 检查端口占用
    port_check = run_command("lsof -i :8000 -sTCP:LISTEN 2>/dev/null")
    if port_check:
        print("✓ 端口 8000 已被占用:")
        print(port_check)
    else:
        print("✗ 端口 8000 未被占用")

    print()

def check_memory_usage():
    """检查内存使用情况"""
    print("=" * 60)
    print("内存使用检查")
    print("=" * 60)

    # Metal 内存使用（需要 MLX）
    try:
        import mlx.core as mx
        metal_mem = mx.get_active_memory()
        metal_mem_gb = metal_mem / (1024**3)
        print(f"Metal 内存使用: {metal_mem_gb:.2f} GB")
    except:
        print("⚠ 无法获取 Metal 内存使用情况")

    # 系统内存使用
    top_output = run_command("top -l 1 | grep PhysMem")
    if top_output:
        print(f"物理内存: {top_output}")

    print()

def provide_recommendations():
    """提供优化建议"""
    print("=" * 60)
    print("优化建议")
    print("=" * 60)

    recommendations = [
        "1. 设置合理的内存限制:",
        "   --memory-guard-gb 40",
        "",
        "2. 降低并发请求数:",
        "   --max-concurrent-requests 4",
        "",
        "3. 启用 KV 缓存压缩:",
        "   在模型设置中启用 turboquant_kv_enabled=true",
        "   设置 turboquant_kv_bits=3",
        "",
        "4. 启用 SSD 缓存:",
        "   --paged-ssd-cache-dir ~/.omlx/cache",
        "   --hot-cache-max-size 8GB",
        "",
        "5. 考虑使用 DFlash 推测解码:",
        "   pip install dflash-mlx",
        "   在模型设置中配置 dflash_enabled=true",
        "",
        "6. 设置模型 TTL 自动卸载:",
        "   ttl_seconds: 300 (5分钟无活动后卸载)",
        "",
        "7. 使用提供的优化启动脚本:",
        "   ./start_optimized.sh"
    ]

    for rec in recommendations:
        print(rec)

    print()

def main():
    """主函数"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 15 + "omlx 性能诊断工具" + " " * 25 + "║")
    print("╚" + "=" * 58 + "╝")
    print("\n")

    try:
        get_system_info()
        check_omlx_installation()
        check_configuration()
        check_models()
        check_running_processes()
        check_memory_usage()
        provide_recommendations()

        print("=" * 60)
        print("诊断完成")
        print("=" * 60)
        print("\n提示: 使用 ./start_optimized.sh 启动优化后的 omlx 服务")

    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
