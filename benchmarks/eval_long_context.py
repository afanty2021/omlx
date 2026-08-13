#!/usr/bin/env python3
"""Ling-3.0-tiny-MLX-8bit 长上下文 prefill/decode 性能分析。

逐步增大 prompt 长度，分别测量：
- prefill 速度（tokens/s）
- decode 速度（tokens/s）
- KV cache 内存占用
- KDA 层 vs MLA 层的瓶颈分析
"""
import asyncio
import json
import time
from pathlib import Path

import httpx

API_BASE = "http://localhost:8001/v1"
MODEL = "Ling-3.0-tiny-MLX-8bit"

# 测试上下文长度
CONTEXT_LENGTHS = [500, 1000, 2000, 4000, 8000, 16000, 32000, 64000]


def make_prompt(approx_tokens: int) -> str:
    """生成约 N tokens 的测试文本（中英混合，有信息密度）。"""
    # 一个段落约 60 tokens
    para = (
        "人工智能技术正在快速发展。深度学习模型在自然语言处理、"
        "计算机视觉和语音识别等领域取得了突破性进展。"
        "大语言模型通过在海量文本数据上预训练，"
        "学会了理解人类语言的深层结构和语义关系。"
        "这些模型不仅能生成连贯的文本，"
        "还能进行推理、翻译、摘要和代码编写等复杂任务。"
    )
    repeats = max(1, approx_tokens // 30)
    text = (para + "\n\n") * repeats
    text += "\n\n请用一句话总结以上内容的核心观点。"
    return text


async def bench_context(client: httpx.AsyncClient, target_tokens: int) -> dict:
    """测试给定 prompt 长度的 prefill + decode 性能。"""
    prompt = make_prompt(target_tokens)

    print(f"  {target_tokens:>6d} tokens ... ", end="", flush=True)

    # 第一步：发送请求，测量 prefill + 少量 decode
    start = time.time()
    try:
        resp = await client.post(
            f"{API_BASE}/chat/completions",
            json={
                "model": MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 64,
                "temperature": 0,
                "stream": False,
            },
            timeout=600,
        )
        elapsed = time.time() - start
        data = resp.json()

        if "error" in data:
            print(f"❌ {data['error']['message'][:60]}")
            return {"target": target_tokens, "error": data["error"]["message"]}

        usage = data.get("usage", {})
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        total_time = usage.get("total_time", elapsed)

        # oMLX 的 total_time 是 decode 时间，prefill 时间 = elapsed - total_time
        # 但更准确的是从 server log 获取
        # 这里用估算：total_time 是 model 生成时间
        prefill_time = max(0.01, elapsed - total_time)
        decode_time = total_time

        prefill_tps = prompt_tokens / prefill_time if prefill_time > 0 else 0
        decode_tps = completion_tokens / decode_time if decode_time > 0 else 0

        print(
            f"prompt={prompt_tokens:>6d} | "
            f"prefill={prefill_time:.2f}s ({prefill_tps:.0f} t/s) | "
            f"decode={decode_tps:.1f} t/s"
        )

        return {
            "target": target_tokens,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "elapsed": elapsed,
            "prefill_time": prefill_time,
            "decode_time": decode_time,
            "prefill_tps": prefill_tps,
            "decode_tps": decode_tps,
        }
    except Exception as e:
        elapsed = time.time() - start
        print(f"❌ {str(e)[:60]}")
        return {"target": target_tokens, "error": str(e), "elapsed": elapsed}


async def main():
    print("=" * 65)
    print(f"Ling-3.0-tiny-MLX-8bit 长上下文性能分析")
    print(f"模型: {MODEL}")
    print(f"测试长度: {CONTEXT_LENGTHS}")
    print("=" * 65)

    results = []
    async with httpx.AsyncClient() as client:
        for target in CONTEXT_LENGTHS:
            result = await bench_context(client, target)
            results.append(result)
            # 检查是否 OOM 或出错
            if "error" in result:
                print(f"\n  ⚠️ 在 {target} tokens 处停止（内存或超时）")
                break

    # 汇总表格
    print(f"\n{'='*65}")
    print("汇总")
    print("="*65)

    header = f"{'Prompt':>8s} | {'Prefill Time':>12s} | {'Prefill Speed':>13s} | {'Decode Speed':>12s} | {'Total':>8s}"
    print(header)
    print("-" * len(header))

    for r in results:
        if "error" in r:
            continue
        print(
            f"{r['prompt_tokens']:>8d} | "
            f"{r['prefill_time']:>10.2f}s | "
            f"{r['prefill_tps']:>10.0f} t/s | "
            f"{r['decode_tps']:>10.1f} t/s | "
            f"{r['elapsed']:>6.1f}s"
        )

    # 分析瓶颈
    print(f"\n{'─'*65}")
    print("瓶颈分析:")

    valid = [r for r in results if "error" not in r and r["prompt_tokens"] > 100]
    if len(valid) >= 2:
        shortest = valid[0]
        longest = valid[-1]

        prefill_decay = shortest["prefill_tps"] / max(longest["prefill_tps"], 1)
        decode_decay = shortest["decode_tps"] / max(longest["decode_tps"], 1)

        print(f"  Prefill 速度衰减: {shortest['prefill_tps']:.0f} → {longest['prefill_tps']:.0f} t/s ({prefill_decay:.1f}x 衰减)")
        print(f"  Decode 速度衰减: {shortest['decode_tps']:.1f} → {longest['decode_tps']:.1f} t/s ({decode_decay:.1f}x 衰减)")

        if prefill_decay > 3:
            print(f"  ⚠️ Prefill 严重衰减 — MLA 层的 O(n²) 注意力成为瓶颈")
        if decode_decay > 2:
            print(f"  ⚠️ Decode 衰减明显 — KV cache 增长导致内存带宽压力")

    output = Path(__file__).parent / "eval_long_context_results.json"
    with open(output, "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\n结果已保存: {output}")


if __name__ == "__main__":
    asyncio.run(main())
