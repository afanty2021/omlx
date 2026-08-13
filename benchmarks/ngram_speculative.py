#!/usr/bin/env python3
"""n-gram 推测解码原型 — 直接使用 mlx-lm 模型，验证加速效果。

原理（Prompt Lookup Decoding）：
1. 从 prompt 中构建 n-gram → next_token 的索引
2. 每生成一个 token 后，检查最后 N 个 token 是否在历史中出现
3. 若匹配，取出后续 K 个 token 作为草稿
4. 一次 forward pass 验证 K+1 个 token（草稿 + 1 个新 token）
5. 接受匹配的前缀，拒绝处用模型输出修正
6. 草稿阶段零 GPU 计算 — 纯 CPU 查表

适用场景：代码生成、JSON 输出、引述、重复模式
"""
import argparse
import collections
import time
from pathlib import Path

import mlx.core as mx
from mlx_lm import load


class NGramIndex:
    """从 token 序列构建 n-gram 索引，支持快速查找后续 token。"""

    def __init__(self, tokens: list[int], ngram_size: int = 3):
        self.ngram_size = ngram_size
        # n-gram tuple → list of next tokens (按出现顺序)
        self.index: dict[tuple[int, ...], list[int]] = collections.defaultdict(list)
        for i in range(len(tokens) - ngram_size):
            key = tuple(tokens[i : i + ngram_size])
            next_tok = tokens[i + ngram_size]
            self.index[key].append(next_tok)

    def lookup(self, recent_tokens: list[int], max_draft: int = 4) -> list[int]:
        """查找最近 N 个 token 的后续 token 作为草稿。"""
        if len(recent_tokens) < self.ngram_size:
            return []
        key = tuple(recent_tokens[-self.ngram_size :])
        candidates = self.index.get(key)
        if not candidates:
            return []
        return candidates[:max_draft]


def generate_baseline(
    model, tokenizer, prompt_ids: list[int], max_tokens: int = 256
) -> tuple[str, float, int]:
    """普通逐 token 生成。"""
    cache = model.make_cache()
    # Prefill
    input_ids = mx.array(prompt_ids)[None, :]
    logits = model(input_ids, cache=cache)
    # logits 可能是 [batch=1, seq=1, vocab] 或 [seq, vocab]
    if logits.ndim == 3:
        logits = logits[:, -1, :]  # [1, vocab]
    elif logits.ndim == 2:
        logits = logits[-1:, :]    # [1, vocab]

    token = mx.argmax(logits, axis=-1)
    mx.eval(token)
    generated = [int(token.item())]

    start = time.time()
    for _ in range(max_tokens - 1):
        logits = model(token[None], cache=cache)
        if logits.ndim == 3:
            logits = logits[:, -1, :]
        elif logits.ndim == 2:
            logits = logits[-1:, :]
        token = mx.argmax(logits, axis=-1)
        mx.eval(token)
        tid = int(token.item())
        generated.append(tid)
        if tid == tokenizer.eos_token_id:
            break

    elapsed = time.time() - start
    text = tokenizer.decode(generated)
    return text, elapsed, len(generated)


def generate_ngram_spec(
    model,
    tokenizer,
    prompt_ids: list[int],
    max_tokens: int = 256,
    ngram_size: int = 3,
    max_draft: int = 4,
) -> tuple[str, float, int, dict]:
    """n-gram 推测解码生成。"""
    index = NGramIndex(prompt_ids, ngram_size)
    cache = model.make_cache()

    # Prefill
    input_ids = mx.array(prompt_ids)[None, :]
    logits = model(input_ids, cache=cache)
    if logits.ndim == 3:
        logits = logits[:, -1, :]
    elif logits.ndim == 2:
        logits = logits[-1:, :]

    token = mx.argmax(logits, axis=-1)
    mx.eval(token)
    generated = [int(token.item())]

    start = time.time()
    total_forward = 0
    total_draft_proposed = 0
    total_draft_accepted = 0
    spec_cycles = 0

    while len(generated) < max_tokens:
        # 1. 查找 n-gram 草稿
        draft = index.lookup(generated, max_draft=max_draft)

        if draft:
            spec_cycles += 1
            total_draft_proposed += len(draft)

            # 2. 用模型验证草稿：把 [token] + draft 一起送入
            verify_ids = mx.array([generated[-1]] + draft)[None, :]
            logits = model(verify_ids, cache=cache)
            # logits: [1, seq_len, vocab] — 第 i 个位置预测第 i+1 个 token
            if logits.ndim == 2:
                logits = logits[None, :, :]

            # 3. 逐个比对
            accepted = 0
            for i, draft_tok in enumerate(draft):
                model_tok = int(mx.argmax(logits[0, i, :]).item())
                if model_tok == draft_tok:
                    accepted += 1
                    generated.append(draft_tok)
                    if len(generated) >= max_tokens:
                        break
                    if draft_tok == tokenizer.eos_token_id:
                        break
                else:
                    # 拒绝：用模型输出修正
                    generated.append(model_tok)
                    break
            else:
                # 全部接受：还需要 logits 最后一个位置的新 token
                model_tok = int(mx.argmax(logits[0, len(draft), :]).item())
                generated.append(model_tok)

            total_draft_accepted += accepted
            total_forward += 1

            if generated[-1] == tokenizer.eos_token_id:
                break
        else:
            # 4. 无草稿：正常生成一个 token
            last_token = mx.array([generated[-1]])
            logits = model(last_token[None], cache=cache)
            if logits.ndim == 3:
                logits = logits[:, -1, :]  # [1, vocab]
            elif logits.ndim == 2:
                logits = logits[-1:, :]    # [1, vocab]
            token = mx.argmax(logits, axis=-1)
            mx.eval(token)
            generated.append(int(token.item()))
            total_forward += 1

            if generated[-1] == tokenizer.eos_token_id:
                break

    elapsed = time.time() - start
    text = tokenizer.decode(generated)
    stats = {
        "spec_cycles": spec_cycles,
        "draft_proposed": total_draft_proposed,
        "draft_accepted": total_draft_accepted,
        "accept_rate": total_draft_accepted / max(total_draft_proposed, 1),
        "forward_passes": total_forward,
        "tokens_generated": len(generated),
        "tokens_per_forward": len(generated) / max(total_forward, 1),
    }
    return text, elapsed, len(generated), stats


def main():
    parser = argparse.ArgumentParser(description="n-gram 推测解码基准测试")
    parser.add_argument("--model", default="inclusionAI/Ling-3.0-tiny",
                        help="模型路径")
    parser.add_argument("--max-tokens", type=int, default=200,
                        help="最大生成 token 数")
    parser.add_argument("--ngram-size", type=int, default=3,
                        help="n-gram 大小")
    parser.add_argument("--max-draft", type=int, default=4,
                        help="最大草稿 token 数")
    args = parser.parse_args()

    model_path = str(Path.home() / "models" / args.model)
    if not Path(model_path).exists():
        model_path = str(Path.home() / ".omlx" / "models" / args.model)

    print(f"加载模型: {model_path}")
    # 先应用 bailing_hybrid patch
    from omlx.patches.bailing_hybrid import apply_bailing_hybrid_patch
    apply_bailing_hybrid_patch()
    model, tokenizer = load(model_path, tokenizer_config={"trust_remote_code": True})
    model.eval()
    print(f"模型加载完成\n")

    # 测试用例 — 覆盖不同场景
    test_cases = [
        {
            "name": "代码生成（重复模式）",
            "prompt": '''请完成以下 Python 函数，实现一个简单的 LRU 缓存：

```python
class LRUCache:
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.cache = {}

    def get(self, key: str) -> int:
        if key in self.cache:
            self.cache.move_to_end(key)
            return self.cache[key]
        return -1

    def put(self, key: str, value: int) -> None:
''',
        },
        {
            "name": "JSON 输出（结构重复）",
            "prompt": '''将以下信息转换为 JSON 格式，每个用户包含 name, age, email 字段：

用户列表：
1. 张三，25岁，zhangsan@example.com
2. 李四，30岁，lisi@example.com
3. 王五，28岁，wangwu@example.com
4. 赵六，35岁，zhaoliu@example.com

输出格式：
{"users": [
''',
        },
        {
            "name": "文本总结（引述原文）",
            "prompt": """请阅读以下文本并用中文总结要点（不超过100字）：

人工智能（AI）是计算机科学的一个分支，它致力于创造能够模拟人类智能行为的系统。AI的研究领域包括机器学习、自然语言处理、计算机视觉、机器人技术等。近年来，随着深度学习技术的突破，AI在图像识别、语音识别、自然语言理解等方面取得了显著进展。大语言模型（LLM）作为AI领域的重要成果，通过在海量文本数据上训练，能够生成高质量的自然语言文本，在对话系统、代码生成、内容创作等领域展现出强大的能力。

请总结：
""",
        },
        {
            "name": "数学推理（格式重复）",
            "prompt": """计算以下算术题，请逐步计算并给出最终答案：

题1: 125 + 338 = ?
题2: 847 - 293 = ?
题3: 56 × 12 = ?
题4: 144 ÷ 12 = ?

格式要求：
题1: 125 + 338 = 463
""",
        },
    ]

    print(f"参数: ngram_size={args.ngram_size}, max_draft={args.max_draft}, max_tokens={args.max_tokens}")
    print("=" * 70)

    for case in test_cases:
        prompt = case["prompt"]
        prompt_ids = tokenizer.encode(prompt)

        print(f"\n{'─'*50}")
        print(f"测试: {case['name']}")
        print(f"Prompt tokens: {len(prompt_ids)}")

        # 基线
        baseline_text, baseline_time, baseline_tokens = generate_baseline(
            model, tokenizer, prompt_ids, max_tokens=args.max_tokens
        )
        baseline_tps = baseline_tokens / baseline_time

        # n-gram 推测
        spec_text, spec_time, spec_tokens, stats = generate_ngram_spec(
            model, tokenizer, prompt_ids,
            max_tokens=args.max_tokens,
            ngram_size=args.ngram_size,
            max_draft=args.max_draft,
        )
        spec_tps = spec_tokens / spec_time

        speedup = spec_tps / baseline_tps if baseline_tps > 0 else 0

        # 正确性检查
        text_match = baseline_text[:50] == spec_text[:50]

        print(f"\n  基线:   {baseline_tokens} tokens in {baseline_time:.2f}s = {baseline_tps:.1f} tok/s")
        print(f"  推测:   {spec_tokens} tokens in {spec_time:.2f}s = {spec_tps:.1f} tok/s")
        print(f"  加速比: {speedup:.2f}x")
        print(f"  正确性: {'✅ 匹配' if text_match else '⚠️ 差异'}")
        print(f"  推测统计:")
        print(f"    推测周期: {stats['spec_cycles']}")
        print(f"    草稿提议: {stats['draft_proposed']}")
        print(f"    草稿接受: {stats['draft_accepted']}")
        print(f"    接受率:   {stats['accept_rate']:.1%}")
        print(f"    forward passes: {stats['forward_passes']}")
        print(f"    tokens/forward: {stats['tokens_per_forward']:.1f}")
        print(f"  基线输出: {repr(baseline_text[:100])}")
        print(f"  推测输出: {repr(spec_text[:100])}")

    print(f"\n{'='*70}")
    print("完成")


if __name__ == "__main__":
    main()
