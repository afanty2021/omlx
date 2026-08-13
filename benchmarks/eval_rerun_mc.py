#!/usr/bin/env python3
"""重跑 MMLU + HellaSwag（修复 answer 格式后），并合并之前的评测结果。"""
import asyncio
import json
import random
import re
import sys
import time
from pathlib import Path

import httpx

API_BASE = "http://localhost:8001/v1"
DATASET_DIR = Path(__file__).parent.parent / "omlx" / "eval" / "data"
SEED = 42
SAMPLE_SIZE = 50
MODELS = ["Ling-3.0-tiny", "Qwen3.6-35B-A3B-4bit"]
BENCHMARKS = ["mmlu", "hellaswag"]
PREV_RESULTS = Path(__file__).parent / "eval_ling_vs_qwen_results.json"


def load_dataset(name, n=SAMPLE_SIZE):
    mapping = {
        "mmlu": "mmlu_test.jsonl",
        "hellaswag": "hellaswag_val.jsonl",
    }
    path = DATASET_DIR / mapping[name]
    items = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                items.append(json.loads(line))
    rng = random.Random(SEED)
    return rng.sample(items, min(n, len(items)))


def format_messages(name, item):
    if name == "mmlu":
        q = item.get("question", "")
        choices = item.get("choices", [])
        text = f"{q}\n\n"
        for i, c in enumerate(choices):
            text += f"{chr(65+i)}. {c}\n"
        text += "\n请直接给出答案字母（A/B/C/D），不要解释。"
        return [{"role": "user", "content": text}]
    elif name == "hellaswag":
        ctx = item.get("ctx", "")
        endings = item.get("endings", [])
        text = f"{ctx}\n\n"
        for i, e in enumerate(endings):
            text += f"{chr(65+i)}. {e}\n"
        text += "\n请直接给出答案字母，不要解释。"
        return [{"role": "user", "content": text}]
    return [{"role": "user", "content": str(item)}]


def extract_mc(response):
    response = re.sub(r"<think>.*?</think>", "", response, flags=re.DOTALL).strip()
    patterns = re.findall(r"(?:answer\s*(?:is|:)\s*)([ABCD])\b", response, re.IGNORECASE)
    if patterns:
        return patterns[-1].upper()
    patterns = re.findall(r"答案[是为：]\s*([ABCD])", response)
    if patterns:
        return patterns[-1].upper()
    matches = re.findall(r"\b([ABCD])\b", response)
    if matches:
        return matches[-1].upper()
    if response and response[0].upper() in "ABCD":
        return response[0].upper()
    return ""


def check_mc(name, predicted, item):
    if name == "mmlu":
        try:
            return ord(predicted) - 65 == int(item.get("answer", -1))
        except (ValueError, TypeError):
            return False
    elif name == "hellaswag":
        try:
            return predicted == chr(65 + int(item.get("label", -1)))
        except (ValueError, TypeError):
            return False
    return False


async def eval_single(client, model, bench_name, item, semaphore):
    messages = format_messages(bench_name, item)
    async with semaphore:
        start = time.time()
        try:
            resp = await client.post(
                f"{API_BASE}/chat/completions",
                json={"model": model, "messages": messages, "max_tokens": 512, "temperature": 0.0},
                timeout=120,
            )
            data = resp.json()
            elapsed = time.time() - start
            if "error" in data:
                return False, elapsed, 0, 0
            content = data["choices"][0]["message"]["content"]
            predicted = extract_mc(content)
            correct = check_mc(bench_name, predicted, item)
            usage = data.get("usage", {})
            tok = usage.get("completion_tokens", 0)
            return correct, elapsed, tok / elapsed if elapsed > 0 else 0, tok
        except Exception:
            return False, time.time() - start, 0, 0


async def run_bench(model, bench_name):
    items = load_dataset(bench_name)
    print(f"  [{model}] {bench_name}: {len(items)} 题 ...", end="", flush=True)
    sem = asyncio.Semaphore(4)
    async with httpx.AsyncClient() as client:
        tasks = [eval_single(client, model, bench_name, item, sem) for item in items]
        results = await asyncio.gather(*tasks)
    correct = sum(1 for r in results if r[0])
    total_time = sum(r[1] for r in results)
    tok_s_vals = [r[2] for r in results if r[2] > 0]
    avg_tok_s = sum(tok_s_vals) / len(tok_s_vals) if tok_s_vals else 0
    acc = correct / len(items)
    print(f" 准确率 {acc:.1%} ({correct}/{len(items)}), {avg_tok_s:.1f} tok/s")
    return {"benchmark": bench_name, "accuracy": acc, "correct": correct,
            "count": len(items), "time": total_time, "avg_tok_s": avg_tok_s}


async def main():
    print("=" * 60)
    print("重跑 MMLU + HellaSwag（修复 answer 索引格式）")
    print("=" * 60)

    # 加载之前结果
    prev = {}
    if PREV_RESULTS.exists():
        with open(PREV_RESULTS) as f:
            prev = json.load(f)

    for model in MODELS:
        print(f"\n--- {model} ---")
        for bench in BENCHMARKS:
            result = await run_bench(model, bench)
            # 替换之前结果中的对应条目
            if model in prev:
                prev[model] = [result if r["benchmark"] == bench else r for r in prev[model]]

    # 输出完整汇总
    all_benches = ["mmlu", "hellaswag", "gsm8k", "humaneval", "truthfulqa"]
    print("\n" + "=" * 60)
    print("完整汇总（修复后）")
    print("=" * 60)

    header = f"{'Benchmark':<14}"
    for m in MODELS:
        header += f" | {m:<24}"
    print(header)
    print("-" * len(header))

    for bench in all_benches:
        row = f"{bench:<14}"
        for m in MODELS:
            r = next((x for x in prev.get(m, []) if x["benchmark"] == bench), None)
            if r:
                row += f" | {r['accuracy']:.1%} ({r.get('avg_tok_s',0):.0f}t/s)"
            else:
                row += f" | {'N/A':<24}"
        print(row)

    with open(PREV_RESULTS, "w") as f:
        json.dump(prev, f, indent=2, ensure_ascii=False)
    print(f"\n结果已更新到: {PREV_RESULTS}")


if __name__ == "__main__":
    asyncio.run(main())
