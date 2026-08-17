#!/usr/bin/env python3
"""Qwen3.8-27B-4bit vs Qwen3.6-27B-4bit 同级对比评测。

通过 oMLX 的 OpenAI 兼容 API 运行多维度基准测试：
- MMLU：通用知识（多选）
- HellaSwag：常识推理（多选）
- GSM8K：小学数学（生成）
- HumanEval：Python 编程（生成）
- TruthfulQA：真实性（多选）

用法: python benchmarks/eval_qwen38_vs_qwen36.py [--api-base http://localhost:8001/v1]
"""
import argparse
import asyncio
import json
import random
import re
import time
from pathlib import Path

import httpx

API_BASE = "http://localhost:8001/v1"
API_KEY = "test-key"  # 与 ~/.omlx/settings.json auth.api_key 一致
DATASET_DIR = Path(__file__).parent.parent / "omlx" / "eval" / "data"
SEED = 42
SAMPLE_SIZE = 50  # 每个数据集采样数

MODELS = [
    "Qwen3.8-27B-4bit",
    "Qwen3.6-27B-4bit",
]

BENCHMARKS = ["mmlu", "hellaswag", "gsm8k", "humaneval", "truthfulqa"]


def load_dataset(name: str, n: int = SAMPLE_SIZE) -> list[dict]:
    """加载数据集并采样。"""
    mapping = {
        "mmlu": "mmlu_test.jsonl",
        "hellaswag": "hellaswag_val.jsonl",
        "gsm8k": "gsm8k_test.jsonl",
        "humaneval": "humaneval.jsonl",
        "truthfulqa": "truthfulqa_mc.jsonl",
    }
    path = DATASET_DIR / mapping[name]
    if not path.exists():
        print(f"  [警告] 数据集文件不存在: {path}")
        return []
    items = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                items.append(json.loads(line))
    rng = random.Random(SEED)
    if n < len(items):
        return rng.sample(items, n)
    return items


def format_messages(name: str, item: dict) -> list[dict]:
    """将数据集条目格式化为聊天消息。"""
    if name == "mmlu":
        q = item.get("question", "")
        choices = item.get("choices", [])
        text = f"{q}\n\n"
        for i, c in enumerate(choices):
            text += f"{chr(65+i)}. {c}\n"
        text += "\n请直接给出答案字母（A/B/C/D），不要解释。"
        return [{"role": "user", "content": text}]

    elif name == "hellaswag":
        ctx = item.get("context", item.get("ctx", ""))
        endings = item.get("endings", item.get("labels", []))
        text = f"{ctx}\n\n"
        for i, e in enumerate(endings):
            text += f"{chr(65+i)}. {e}\n"
        text += "\n请直接给出答案字母，不要解释。"
        return [{"role": "user", "content": text}]

    elif name == "gsm8k":
        q = item.get("question", "")
        return [{"role": "user", "content": f"{q}\n\n请逐步计算，最后在单独一行给出 #### 答案"}]

    elif name == "humaneval":
        prompt = item.get("prompt", "")
        return [{"role": "user", "content": f"请完成以下Python函数，只输出代码：\n\n```python\n{prompt}\n```"}]

    elif name == "truthfulqa":
        q = item.get("question", "")
        choices = item.get("mc1_targets", {}).get("choices", [])
        text = f"{q}\n\n"
        for i, c in enumerate(choices):
            text += f"{chr(65+i)}. {c}\n"
        text += "\n请直接给出答案字母，不要解释。"
        return [{"role": "user", "content": text}]

    return [{"role": "user", "content": str(item)}]


def extract_answer(name: str, response: str, item: dict) -> str:
    """从模型回复中提取答案。"""
    response = response.strip()

    if name in ("mmlu", "hellaswag", "truthfulqa"):
        # 先去掉 <think> 标签
        response = re.sub(r"<think>.*?</think>", "", response, flags=re.DOTALL).strip()
        patterns = re.findall(
            r"(?:answer\s*(?:is|:)\s*)([ABCD])\b", response, re.IGNORECASE
        )
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

    elif name == "gsm8k":
        match = re.search(r"####\s*([\d,.\-]+)", response)
        if match:
            return match.group(1).replace(",", "").strip()
        numbers = re.findall(r"-?[\d,]+\.?\d*", response)
        if numbers:
            return numbers[-1].replace(",", "").strip()
        return ""

    elif name == "humaneval":
        blocks = re.findall(r"```python\s*\n(.*?)```", response, re.DOTALL)
        if blocks:
            return blocks[-1].strip()
        blocks = re.findall(r"```\s*\n(.*?)```", response, re.DOTALL)
        if blocks:
            return blocks[-1].strip()
        return response

    return response


def check_answer(name: str, predicted: str, item: dict) -> bool:
    """检查答案是否正确。"""
    if name == "mmlu":
        try:
            return ord(predicted) - 65 == int(item.get("answer", -1))
        except (ValueError, TypeError):
            return False
    elif name == "hellaswag":
        label = item.get("label", "")
        try:
            idx = int(label)
            return predicted == chr(65 + idx)
        except (ValueError, TypeError):
            return predicted == str(label).upper()
    elif name == "truthfulqa":
        labels = item.get("mc1_targets", {}).get("labels", [])
        try:
            idx = ord(predicted) - 65
            if 0 <= idx < len(labels):
                return labels[idx] == 1
        except Exception:
            pass
        return False
    elif name == "gsm8k":
        answer = item.get("answer", "")
        match = re.search(r"####\s*([\d,.\-]+)", answer)
        if match:
            answer_num = match.group(1).replace(",", "").strip()
            return predicted == answer_num
        return False
    elif name == "humaneval":
        return len(predicted) > 20 and ("def " in predicted or "return" in predicted)
    return False


async def eval_single(
    client: httpx.AsyncClient,
    model: str,
    bench_name: str,
    item: dict,
    idx: int,
    semaphore: asyncio.Semaphore,
) -> tuple:
    """评测单条。"""
    messages = format_messages(bench_name, item)
    max_tokens = 512 if bench_name in ("gsm8k", "humaneval") else 128

    async with semaphore:
        start = time.time()
        try:
            resp = await client.post(
                f"{API_BASE}/chat/completions",
                json={
                    "model": model,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": 0.0,
                    # Qwen3.x 系列默认开思考模式，128 token 内答不完；评测统一关闭
                    "chat_template_kwargs": {"enable_thinking": False},
                },
                timeout=180,
            )
            data = resp.json()
            elapsed = time.time() - start

            if "error" in data:
                return False, elapsed, 0, 0

            message = data["choices"][0]["message"]
            content = message.get("content") or ""
            reasoning = message.get("reasoning_content") or ""
            predicted = extract_answer(bench_name, content, item)
            if not predicted and reasoning:
                predicted = extract_answer(bench_name, reasoning, item)
            correct = check_answer(bench_name, predicted, item)

            usage = data.get("usage", {})
            completion_tokens = usage.get("completion_tokens", 0)
            tok_s = completion_tokens / elapsed if elapsed > 0 else 0

            return correct, elapsed, tok_s, completion_tokens
        except Exception:
            elapsed = time.time() - start
            return False, elapsed, 0, 0


async def run_benchmark(model: str, bench_name: str) -> dict:
    """运行单个基准测试。"""
    items = load_dataset(bench_name)
    if not items:
        return {"benchmark": bench_name, "accuracy": 0, "count": 0, "time": 0}

    print(f"  [{model}] {bench_name}: {len(items)} 题 ...", end="", flush=True)
    semaphore = asyncio.Semaphore(4)
    headers = {"Authorization": f"Bearer {API_KEY}"}
    async with httpx.AsyncClient(headers=headers) as client:
        tasks = [
            eval_single(client, model, bench_name, item, i, semaphore)
            for i, item in enumerate(items)
        ]
        results = await asyncio.gather(*tasks)

    correct = sum(1 for r in results if r[0])
    total_time = sum(r[1] for r in results)
    tok_s_vals = [r[2] for r in results if r[2] > 0]
    avg_tok_s = sum(tok_s_vals) / len(tok_s_vals) if tok_s_vals else 0
    total_tokens = sum(r[3] for r in results if len(r) > 3)

    acc = correct / len(items)
    print(
        f" 准确率 {acc:.1%} ({correct}/{len(items)}), "
        f"耗时 {total_time:.1f}s, {avg_tok_s:.1f} tok/s"
    )
    return {
        "benchmark": bench_name,
        "accuracy": acc,
        "correct": correct,
        "count": len(items),
        "time": total_time,
        "avg_tok_s": avg_tok_s,
        "total_tokens": total_tokens,
    }


async def main():
    global API_BASE

    parser = argparse.ArgumentParser()
    parser.add_argument("--api-base", default=API_BASE)
    parser.add_argument("--models", nargs="+", default=MODELS)
    args = parser.parse_args()

    API_BASE = args.api_base
    models = args.models

    print("=" * 70)
    print("Qwen3.8-27B-4bit vs Qwen3.6-27B-4bit 同级对比评测")
    print(f"API: {API_BASE} | 每数据集采样: {SAMPLE_SIZE} 题 | 温度: 0 (greedy)")
    print("=" * 70)

    all_results = {}
    for model in models:
        print(f"\n{'='*35} {model} {'='*35}")
        results = []
        for bench in BENCHMARKS:
            result = await run_benchmark(model, bench)
            results.append(result)
        all_results[model] = results

    # 汇总表格
    print("\n" + "=" * 70)
    print("汇总结果")
    print("=" * 70)

    header = f"{'Benchmark':<14}"
    for model in models:
        header += f" | {model:<22}"
    print(header)
    print("-" * len(header))

    for bench in BENCHMARKS:
        row = f"{bench:<14}"
        for model in models:
            result = next(
                (r for r in all_results[model] if r["benchmark"] == bench), None
            )
            if result:
                row += f" | {result['accuracy']:.1%} ({result['avg_tok_s']:.0f}t/s)"
            else:
                row += f" | {'N/A':<22}"
        print(row)

    # 速度对比
    print(f"\n{'─'*60}")
    print("速度对比 (tok/s):")
    for bench in BENCHMARKS:
        speeds = []
        for model in models:
            result = next(
                (r for r in all_results[model] if r["benchmark"] == bench), None
            )
            speeds.append(f"{result['avg_tok_s']:.1f}" if result else "N/A")
        print(f"  {bench:<14}: {' vs '.join(speeds)}")

    # 保存 JSON
    output_path = Path(__file__).parent / "eval_qwen38_vs_qwen36_results.json"
    with open(output_path, "w") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    print(f"\n详细结果已保存到: {output_path}")


if __name__ == "__main__":
    asyncio.run(main())
