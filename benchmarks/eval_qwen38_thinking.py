#!/usr/bin/env python3
"""Qwen3.8-27B-4bit 思考模式验证：AIME 2025 + GSM8K，reasoning effort 分档。

验证 3.8 的卖点：thinking 模式 + reasoning_effort (xhigh/medium/low) 相对
Qwen3.6-27B-4bit（thinking 无分档）的精度与 token 效率。

用法: python benchmarks/eval_qwen38_thinking.py
"""
import asyncio
import json
import random
import re
import time
from pathlib import Path

import httpx

API_BASE = "http://localhost:8001/v1"
API_KEY = "test-key"
DATASET_DIR = Path(__file__).parent.parent / "omlx" / "eval" / "data"
SEED = 42

AIME_N = 15     # AIME 2025 共 30 题，采样一半
GSM8K_N = 15
CONCURRENCY = 2  # 内存有限：最多两路并发（KV cache 每路 ~3GB @12K token）

# 评测矩阵：模型 × 数据集 × effort 档
# 3.8 用 reasoning_effort 分档；3.6 模板无 effort，仅默认 thinking
# 顺序按重要性：头条对比（xhigh vs 3.6）优先
CELLS = [
    {"label": "Qwen3.8@xhigh",  "model": "Qwen3.8-27B-4bit", "kwargs": {"reasoning_effort": "xhigh"}},
    {"label": "Qwen3.6@think",  "model": "Qwen3.6-27B-4bit", "kwargs": {}},
    {"label": "Qwen3.8@medium", "model": "Qwen3.8-27B-4bit", "kwargs": {"reasoning_effort": "medium"}},
]
GSM8K_CELLS = []  # 首轮 AIME 数据已足够回答卖点问题；GSM8K thinking 暂缓

import os
if os.environ.get("WITH_GSM8K"):
    GSM8K_CELLS = [
        {"label": "Qwen3.8@xhigh(gsm8k)", "model": "Qwen3.8-27B-4bit", "kwargs": {"reasoning_effort": "xhigh"}},
        {"label": "Qwen3.6@think(gsm8k)", "model": "Qwen3.6-27B-4bit", "kwargs": {}},
    ]

MAX_TOKENS = {"aime": 12288, "gsm8k": 6144}


def load_jsonl(path: Path, n: int | None = None):
    items = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                items.append(json.loads(line))
    if n and n < len(items):
        rng = random.Random(SEED)
        return rng.sample(items, n)
    return items


def extract_aime(content: str) -> str:
    """AIME 答案为 0-999 整数：优先最后一个 \\boxed{...}，否则最后一个独立整数。"""
    boxed = re.findall(r"\\boxed\{([^{}]*)\}", content)
    for b in reversed(boxed):
        m = re.search(r"-?\d+", b.replace(",", ""))
        if m:
            return m.group(0)
    nums = re.findall(r"(?<![\d.])(\d{1,3})(?![\d.])", content)
    return nums[-1] if nums else ""


def extract_gsm8k(content: str) -> str:
    m = re.search(r"####\s*([\d,.\-]+)", content)
    if m:
        return m.group(1).replace(",", "").strip().rstrip(".")
    nums = re.findall(r"-?[\d,]+\.?\d*", content)
    return nums[-1].replace(",", "").strip().rstrip(".") if nums else ""


async def eval_item(client, cell, bench, item, sem):
    if bench == "aime":
        prompt = item["problem"] + "\n\nPlease reason step by step, and put your final answer as an integer in \\boxed{}."
        gold = str(item["answer"])
        extract = extract_aime
    else:
        prompt = item["question"] + "\n\n请逐步计算，最后在单独一行给出 #### 答案"
        gold_m = re.search(r"####\s*([\d,.\-]+)", item["answer"])
        gold = gold_m.group(1).replace(",", "").strip() if gold_m else ""
        extract = extract_gsm8k

    body = {
        "model": cell["model"],
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": MAX_TOKENS[bench],
        "temperature": 0.0,
    }
    if cell["kwargs"]:
        body["chat_template_kwargs"] = cell["kwargs"]

    async with sem:
        t0 = time.time()
        try:
            r = await client.post(
                f"{API_BASE}/chat/completions",
                headers={"Authorization": f"Bearer {API_KEY}"},
                json=body,
                timeout=1800,
            )
            dt = time.time() - t0
            d = r.json()
            if "error" in d:
                return {"ok": False, "tokens": 0, "time": dt, "finish": "error"}
            msg = d["choices"][0]["message"]
            content = msg.get("content") or ""
            finish = d["choices"][0].get("finish_reason", "?")
            usage = d.get("usage", {})
            pred = extract(content)
            ok = (pred == gold) and finish == "stop"
            return {
                "ok": ok,
                "pred": pred,
                "gold": gold,
                "tokens": usage.get("completion_tokens", 0),
                "time": dt,
                "finish": finish,
            }
        except Exception as e:
            return {"ok": False, "tokens": 0, "time": time.time() - t0, "finish": f"exc:{type(e).__name__}"}


async def run_cell(client, cell, bench, items):
    sem = asyncio.Semaphore(CONCURRENCY)
    t0 = time.time()
    results = await asyncio.gather(*[eval_item(client, cell, bench, it, sem) for it in items])
    wall = time.time() - t0
    acc = sum(1 for r in results if r["ok"]) / len(results)
    total_tok = sum(r["tokens"] for r in results)
    avg_tok = total_tok / len(results)
    truncated = sum(1 for r in results if r.get("finish") == "length")
    tok_s = total_tok / wall if wall > 0 else 0
    print(
        f"  [{cell['label']}] {bench}: acc {acc:.1%} ({sum(1 for r in results if r['ok'])}/{len(results)}), "
        f"avg {avg_tok:.0f} tok/题 (截断 {truncated}), wall {wall:.0f}s, {tok_s:.1f} tok/s",
        flush=True,
    )
    return {
        "label": cell["label"], "bench": bench, "accuracy": acc,
        "correct": sum(1 for r in results if r["ok"]), "count": len(results),
        "avg_tokens": round(avg_tok), "total_tokens": total_tok,
        "truncated": truncated, "wall_s": round(wall), "tok_s": round(tok_s, 1),
        "items": [{k: r.get(k) for k in ("ok", "pred", "gold", "tokens", "finish")} for r in results],
    }


async def main():
    aime = load_jsonl(DATASET_DIR / "aime25.jsonl", AIME_N)
    gsm8k = load_jsonl(DATASET_DIR / "gsm8k_test.jsonl", GSM8K_N)

    print("=" * 72)
    print(f"思考模式对比: AIME2025({AIME_N}题) + GSM8K({GSM8K_N}题) | greedy | 并发{CONCURRENCY} | MTP开")
    print("=" * 72)

    out_path = Path(__file__).parent / "eval_qwen38_thinking_results.json"
    # 断点续跑：已完成的 label 跳过，结果按 label 合并
    out = []
    done_labels = set()
    if out_path.exists():
        try:
            out = json.load(open(out_path))
            done_labels = {c["label"] for c in out}
        except Exception:
            out = []
    async with httpx.AsyncClient() as client:
        print(f"\n--- AIME 2025 ---", flush=True)
        for cell in CELLS:
            if cell["label"] in done_labels:
                print(f"  [{cell['label']}] already done, skip", flush=True)
                continue
            out.append(await run_cell(client, cell, "aime", aime))
            json.dump(out, open(out_path, "w"), indent=2, ensure_ascii=False)  # 逐格落盘
        print(f"\n--- GSM8K ---", flush=True)
        for cell in GSM8K_CELLS:
            if cell["label"] in done_labels:
                continue
            out.append(await run_cell(client, cell, "gsm8k", gsm8k))
            json.dump(out, open(out_path, "w"), indent=2, ensure_ascii=False)

    print(f"\n结果已保存: {out_path}")


if __name__ == "__main__":
    asyncio.run(main())
