#!/usr/bin/env python3
"""Ling-3.0-tiny BF16 vs 8bit 质量与速度对比。"""
import asyncio
import json
import random
import re
import time
from pathlib import Path

import httpx

API_BASE = "http://localhost:8001/v1"
DATASET_DIR = Path(__file__).parent.parent / "omlx" / "eval" / "data"
SEED = 42
SAMPLE_SIZE = 50
MODELS = ["Ling-3.0-tiny", "Ling-3.0-tiny-MLX-8bit", "Ling-3.0-tiny-MLX-4bit"]
BENCHMARKS = ["mmlu", "hellaswag", "gsm8k", "humaneval", "truthfulqa"]


def load_dataset(name, n=SAMPLE_SIZE):
    mapping = {
        "mmlu": "mmlu_test.jsonl", "hellaswag": "hellaswag_val.jsonl",
        "gsm8k": "gsm8k_test.jsonl", "humaneval": "humaneval.jsonl",
        "truthfulqa": "truthfulqa_mc.jsonl",
    }
    path = DATASET_DIR / mapping[name]
    items = []
    with open(path) as f:
        for line in f:
            if line.strip():
                items.append(json.loads(line))
    rng = random.Random(SEED)
    return rng.sample(items, min(n, len(items)))


def format_messages(name, item):
    if name == "mmlu":
        q, choices = item["question"], item["choices"]
        text = f"{q}\n\n" + "".join(f"{chr(65+i)}. {c}\n" for i, c in enumerate(choices))
        return [{"role": "user", "content": text + "\n请直接给出答案字母（A/B/C/D），不要解释。"}]
    if name == "hellaswag":
        ctx, endings = item.get("ctx",""), item.get("endings",[])
        text = f"{ctx}\n\n" + "".join(f"{chr(65+i)}. {e}\n" for i, e in enumerate(endings))
        return [{"role": "user", "content": text + "\n请直接给出答案字母，不要解释。"}]
    if name == "gsm8k":
        return [{"role": "user", "content": item["question"] + "\n\n请逐步计算，最后在单独一行给出 #### 答案"}]
    if name == "humaneval":
        return [{"role": "user", "content": f"请完成以下Python函数，只输出代码：\n\n```python\n{item['prompt']}\n```"}]
    if name == "truthfulqa":
        mc = item.get("mc1_targets", {})
        choices = mc.get("choices", [])
        text = item["question"] + "\n\n" + "".join(f"{chr(65+i)}. {c}\n" for i, c in enumerate(choices))
        return [{"role": "user", "content": text + "\n请直接给出答案字母，不要解释。"}]
    return [{"role": "user", "content": str(item)}]


def extract_answer(name, response):
    response = re.sub(r"<think>.*?</think>", "", response, flags=re.DOTALL).strip()
    if name in ("mmlu", "hellaswag", "truthfulqa"):
        for pat in [r"(?:answer\s*(?:is|:)\s*)([ABCD])\b", r"答案[是为：]\s*([ABCD])"]:
            m = re.findall(pat, response, re.IGNORECASE)
            if m: return m[-1].upper()
        m = re.findall(r"\b([ABCD])\b", response)
        if m: return m[-1].upper()
        if response and response[0].upper() in "ABCD": return response[0].upper()
        return ""
    if name == "gsm8k":
        m = re.search(r"####\s*([\d,.\-]+)", response)
        if m: return m.group(1).replace(",", "").strip()
        nums = re.findall(r"-?[\d,]+\.?\d*", response)
        return nums[-1].replace(",", "").strip() if nums else ""
    if name == "humaneval":
        blocks = re.findall(r"```python\s*\n(.*?)```", response, re.DOTALL)
        if blocks: return blocks[-1].strip()
        blocks = re.findall(r"```\s*\n(.*?)```", response, re.DOTALL)
        return blocks[-1].strip() if blocks else response
    return response


def check_answer(name, predicted, item):
    if name == "mmlu":
        try: return ord(predicted) - 65 == int(item.get("answer", -1))
        except: return False
    if name == "hellaswag":
        try: return predicted == chr(65 + int(item["label"]))
        except: return False
    if name == "truthfulqa":
        labels = item.get("mc1_targets", {}).get("labels", [])
        try: return labels[ord(predicted) - 65] == 1
        except: return False
    if name == "gsm8k":
        m = re.search(r"####\s*([\d,.\-]+)", item.get("answer", ""))
        return predicted == m.group(1).replace(",", "").strip() if m else False
    if name == "humaneval":
        return len(predicted) > 20 and ("def " in predicted or "return" in predicted)
    return False


async def eval_single(client, model, bench, item, sem):
    messages = format_messages(bench, item)
    max_tokens = 512
    async with sem:
        start = time.time()
        try:
            resp = await client.post(f"{API_BASE}/chat/completions",
                json={"model": model, "messages": messages, "max_tokens": max_tokens, "temperature": 0.0},
                timeout=120)
            data = resp.json()
            elapsed = time.time() - start
            if "error" in data: return False, elapsed, 0
            content = data["choices"][0]["message"]["content"]
            predicted = extract_answer(bench, content)
            correct = check_answer(bench, predicted, item)
            tok = data.get("usage", {}).get("completion_tokens", 0)
            return correct, elapsed, tok / elapsed if elapsed > 0 else 0
        except: return False, time.time() - start, 0


async def run_bench(model, bench):
    items = load_dataset(bench)
    print(f"  [{model}] {bench}: {len(items)}题 ...", end="", flush=True)
    sem = asyncio.Semaphore(4)
    async with httpx.AsyncClient() as client:
        results = await asyncio.gather(*[eval_single(client, model, bench, item, sem) for item in items])
    correct = sum(1 for r in results if r[0])
    tok_s_vals = [r[2] for r in results if r[2] > 0]
    avg_tok_s = sum(tok_s_vals) / len(tok_s_vals) if tok_s_vals else 0
    acc = correct / len(items)
    print(f" {acc:.1%} ({correct}/{len(items)}), {avg_tok_s:.1f} tok/s")
    return {"benchmark": bench, "accuracy": acc, "avg_tok_s": avg_tok_s, "correct": correct}


async def main():
    print("=" * 65)
    print("Ling-3.0-tiny: BF16 vs 8bit 质量与速度对比")
    print(f"采样: {SAMPLE_SIZE}题/项 | greedy | max_tokens=512")
    print("=" * 65)

    all_results = {}
    for model in MODELS:
        print(f"\n{'='*25} {model} {'='*25}")
        results = []
        for bench in BENCHMARKS:
            results.append(await run_bench(model, bench))
        all_results[model] = results

    print(f"\n{'='*65}")
    print("汇总")
    print("="*65)

    header = f"{'Benchmark':<14}"
    labels = {"Ling-3.0-tiny": "BF16", "Ling-3.0-tiny-MLX-8bit": "8bit", "Ling-3.0-tiny-MLX-4bit": "4bit"}
    for m in MODELS:
        header += f" | {labels.get(m, m):<18}"
    header += " | 8bit vs BF16 | 4bit vs BF16"
    print(header)
    print("-" * len(header))

    for bench in BENCHMARKS:
        row = f"{bench:<14}"
        scores = []
        for m in MODELS:
            r = next((x for x in all_results[m] if x["benchmark"] == bench), None)
            if r:
                row += f" | {r['accuracy']:.1%} ({r['avg_tok_s']:.0f}t/s)"
                scores.append(r["accuracy"])
            else:
                row += f" | {'N/A':<18}"
                scores.append(0)
        bf16 = scores[0] if scores else 0
        d8 = (scores[1] - bf16) * 100 if len(scores) > 1 else 0
        d4 = (scores[2] - bf16) * 100 if len(scores) > 2 else 0
        row += f" | {d8:+.1f}pp       | {d4:+.1f}pp"
        print(row)

    print(f"\n{'─'*65}")
    print("速度对比:")
    for bench in BENCHMARKS:
        speeds = []
        for m in MODELS:
            r = next((x for x in all_results[m] if x["benchmark"] == bench), None)
            speeds.append(r["avg_tok_s"] if r else 0)
        parts = [f"BF16 {speeds[0]:.1f}"]
        if len(speeds) > 1 and speeds[0] > 0:
            parts.append(f"8bit {speeds[1]:.1f} ({speeds[1]/speeds[0]:.2f}x)")
        if len(speeds) > 2 and speeds[0] > 0:
            parts.append(f"4bit {speeds[2]:.1f} ({speeds[2]/speeds[0]:.2f}x)")
        print(f"  {bench:<14}: {' → '.join(parts)} tok/s")

    output = Path(__file__).parent / "eval_8bit_results.json"
    with open(output, "w") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    print(f"\n结果已保存: {output}")


if __name__ == "__main__":
    asyncio.run(main())
