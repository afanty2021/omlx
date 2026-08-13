#!/usr/bin/env python3
"""Agent 工具调用能力评测 — 模拟 BFCL (Berkeley Function Calling Leaderboard) 风格。

评测维度：
1. 单工具调用：模型能否正确选择并调用工具
2. 多工具选择：给多个工具，选择正确的那个
3. 参数提取：从自然语言中提取正确的参数值
4. 多工具并行调用：一次调用多个工具
5. 无需工具：用户意图不需要工具时，不应调用
6. 多轮对话：基于工具返回结果继续对话
"""
import asyncio
import json
import time
from pathlib import Path

import httpx

API_BASE = "http://localhost:8001/v1"
MODELS = ["Ling-3.0-tiny", "Qwen3.6-35B-A3B-4bit"]

# ── 工具定义 ──────────────────────────────────────────────

TOOL_WEATHER = {
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "获取指定城市的当前天气信息",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "城市名称，如'北京'"},
                "unit": {"type": "string", "enum": ["celsius", "fahrenheit"], "description": "温度单位"}
            },
            "required": ["city"]
        }
    }
}

TOOL_CALC = {
    "type": "function",
    "function": {
        "name": "calculator",
        "description": "数学计算器，支持加减乘除",
        "parameters": {
            "type": "object",
            "properties": {
                "expression": {"type": "string", "description": "数学表达式，如 '2 + 3 * 4'"}
            },
            "required": ["expression"]
        }
    }
}

TOOL_SEARCH = {
    "type": "function",
    "function": {
        "name": "web_search",
        "description": "搜索互联网获取信息",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "搜索关键词"},
                "num_results": {"type": "integer", "description": "返回结果数量，默认5"}
            },
            "required": ["query"]
        }
    }
}

TOOL_TIME = {
    "type": "function",
    "function": {
        "name": "get_current_time",
        "description": "获取当前时间和日期",
        "parameters": {
            "type": "object",
            "properties": {
                "timezone": {"type": "string", "description": "时区，如 'Asia/Shanghai'"}
            }
        }
    }
}

TOOL_SEND_EMAIL = {
    "type": "function",
    "function": {
        "name": "send_email",
        "description": "发送邮件",
        "parameters": {
            "type": "object",
            "properties": {
                "to": {"type": "string", "description": "收件人邮箱"},
                "subject": {"type": "string", "description": "邮件主题"},
                "body": {"type": "string", "description": "邮件正文"}
            },
            "required": ["to", "subject", "body"]
        }
    }
}

ALL_TOOLS = [TOOL_WEATHER, TOOL_CALC, TOOL_SEARCH, TOOL_TIME, TOOL_SEND_EMAIL]


# ── 测试用例 ──────────────────────────────────────────────

TEST_CASES = [
    # 1. 单工具 — 简单参数
    {
        "id": "single_weather",
        "category": "单工具调用",
        "messages": [{"role": "user", "content": "上海今天天气怎么样？"}],
        "tools": [TOOL_WEATHER],
        "expected_tool": "get_weather",
        "expected_args": {"city": "上海"},
        "should_call": True,
    },
    # 2. 单工具 — 带可选参数
    {
        "id": "single_weather_fahrenheit",
        "category": "单工具调用",
        "messages": [{"role": "user", "content": "查一下纽约的天气，用华氏度"}],
        "tools": [TOOL_WEATHER],
        "expected_tool": "get_weather",
        "expected_args": {"city": "纽约", "unit": "fahrenheit"},
        "should_call": True,
    },
    # 3. 多工具选择 — 计算器
    {
        "id": "multi_calc",
        "category": "多工具选择",
        "messages": [{"role": "user", "content": "帮我算一下 128 * 45 + 37 等于多少"}],
        "tools": ALL_TOOLS,
        "expected_tool": "calculator",
        "expected_args": {"expression": "128 * 45 + 37"},
        "should_call": True,
    },
    # 4. 多工具选择 — 搜索
    {
        "id": "multi_search",
        "category": "多工具选择",
        "messages": [{"role": "user", "content": "帮我搜索一下最新的 AI 大模型排行榜"}],
        "tools": ALL_TOOLS,
        "expected_tool": "web_search",
        "expected_args_contains": {"query": "AI"},
        "should_call": True,
    },
    # 5. 多工具选择 — 天气
    {
        "id": "multi_weather",
        "category": "多工具选择",
        "messages": [{"role": "user", "content": "深圳和广州哪个更热？帮我分别查一下"}],
        "tools": ALL_TOOLS,
        "expected_tool": "get_weather",
        "expected_args_any": [{"city": "深圳"}, {"city": "广州"}],
        "should_call": True,
        "expect_multiple": True,
    },
    # 6. 无需工具 — 闲聊
    {
        "id": "no_tool_chat",
        "category": "无需工具",
        "messages": [{"role": "user", "content": "你好，你能做什么？"}],
        "tools": ALL_TOOLS,
        "expected_tool": None,
        "should_call": False,
    },
    # 7. 无需工具 — 知识问答
    {
        "id": "no_tool_knowledge",
        "category": "无需工具",
        "messages": [{"role": "user", "content": "请用三句话解释什么是量子计算"}],
        "tools": ALL_TOOLS,
        "expected_tool": None,
        "should_call": False,
    },
    # 8. 复杂参数 — 邮件
    {
        "id": "email_complex",
        "category": "复杂参数提取",
        "messages": [{"role": "user", "content": "给 zhangsan@example.com 发一封邮件，主题是'项目进度汇报'，内容写'本周完成了API开发，下周开始前端对接。'"}],
        "tools": [TOOL_SEND_EMAIL],
        "expected_tool": "send_email",
        "expected_args_contains": {
            "to": "zhangsan@example.com",
            "subject": "项目进度汇报",
        },
        "should_call": True,
    },
    # 9. 时间查询
    {
        "id": "time_query",
        "category": "多工具选择",
        "messages": [{"role": "user", "content": "现在东京几点了？"}],
        "tools": ALL_TOOLS,
        "expected_tool": "get_current_time",
        "expected_args_contains": {"timezone": "Tokyo"},
        "should_call": True,
    },
    # 10. 多轮对话 — 基于工具返回结果
    {
        "id": "multi_turn",
        "category": "多轮对话",
        "messages": [
            {"role": "user", "content": "北京天气怎么样？"},
            {"role": "assistant", "content": None, "tool_calls": [{"id": "call_1", "type": "function", "function": {"name": "get_weather", "arguments": '{"city": "北京"}'}}]},
            {"role": "tool", "tool_call_id": "call_1", "content": '{"temperature": 35, "condition": "晴天", "humidity": 60}'},
            {"role": "user", "content": "那适合户外运动吗？"}
        ],
        "tools": [TOOL_WEATHER],
        "expected_tool": None,
        "should_call": False,  # 应该直接回答，不需要再调工具
    },
    # 11. 数学表达式变体
    {
        "id": "calc_variant",
        "category": "参数提取",
        "messages": [{"role": "user", "content": "计算 (15 + 27) / 7 的结果"}],
        "tools": [TOOL_CALC],
        "expected_tool": "calculator",
        "expected_args_contains": {"expression": "(15 + 27) / 7"},
        "should_call": True,
    },
    # 12. 隐含参数
    {
        "id": "weather_implicit",
        "category": "参数提取",
        "messages": [{"role": "user", "content": "我明天要去巴黎出差，那边天气如何？"}],
        "tools": [TOOL_WEATHER],
        "expected_tool": "get_weather",
        "expected_args_contains": {"city": "巴黎"},
        "should_call": True,
    },
]


def extract_tool_calls(data: dict) -> list[dict]:
    """从 API 响应中提取 tool_calls。"""
    if "error" in data:
        return []
    msg = data.get("choices", [{}])[0].get("message", {})
    return msg.get("tool_calls") or []


def check_tool_call(tc: dict, expected: dict) -> dict:
    """检查单个 tool_call 是否符合预期。返回评分详情。"""
    result = {"correct_tool": False, "correct_args": False, "details": ""}

    # 检查工具名
    fn = tc.get("function", {})
    actual_name = fn.get("name", "")
    expected_name = expected.get("expected_tool")
    if expected_name and actual_name == expected_name:
        result["correct_tool"] = True
    elif not expected_name:
        result["correct_tool"] = True

    # 解析参数
    try:
        actual_args = json.loads(fn.get("arguments", "{}"))
    except json.JSONDecodeError:
        actual_args = {}

    # 检查参数
    if expected.get("expected_args"):
        expected_args = expected["expected_args"]
        if all(actual_args.get(k) == v for k, v in expected_args.items()):
            result["correct_args"] = True
        else:
            result["details"] = f"期望 {expected_args}, 实际 {actual_args}"
    elif expected.get("expected_args_contains"):
        check = expected["expected_args_contains"]
        if all(
            str(v).lower() in str(actual_args.get(k, "")).lower()
            for k, v in check.items()
        ):
            result["correct_args"] = True
        else:
            result["details"] = f"期望包含 {check}, 实际 {actual_args}"
    elif expected.get("expected_args_any"):
        any_list = expected["expected_args_any"]
        if any(
            all(str(v).lower() in str(actual_args.get(k, "")).lower() for k, v in opt.items())
            for opt in any_list
        ):
            result["correct_args"] = True
        else:
            result["details"] = f"期望匹配 {any_list} 之一, 实际 {actual_args}"
    else:
        result["correct_args"] = True

    return result


async def eval_single(
    client: httpx.AsyncClient, model: str, case: dict
) -> dict:
    """评测单个用例。"""
    start = time.time()
    try:
        resp = await client.post(
            f"{API_BASE}/chat/completions",
            json={
                "model": model,
                "messages": case["messages"],
                "tools": case.get("tools", []),
                "max_tokens": 1024,
                "temperature": 0.0,
            },
            timeout=120,
        )
        data = resp.json()
        elapsed = time.time() - start

        tool_calls = extract_tool_calls(data)
        should_call = case.get("should_call", True)

        if not should_call:
            # 不应该调用工具
            if len(tool_calls) == 0:
                return {"correct": True, "time": elapsed, "detail": "正确：未调用工具"}
            else:
                return {"correct": False, "time": elapsed, "detail": f"错误：不应调用但调用了 {tool_calls[0]['function']['name']}"}

        # 应该调用工具
        if len(tool_calls) == 0:
            return {"correct": False, "time": elapsed, "detail": "错误：应调用但未调用"}

        # 检查第一个 tool_call
        check = check_tool_call(tool_calls[0], case)
        correct = check["correct_tool"] and check["correct_args"]

        # 多工具并行调用检查
        if case.get("expect_multiple"):
            multi_correct = len(tool_calls) >= 2
            return {
                "correct": correct and multi_correct,
                "time": elapsed,
                "detail": f"调用 {len(tool_calls)} 次, 工具={check['correct_tool']}, 参数={check['correct_args']} {check.get('details','')}"
            }

        return {
            "correct": correct,
            "time": elapsed,
            "detail": f"工具={check['correct_tool']}, 参数={check['correct_args']} {check.get('details','')}"
        }

    except Exception as e:
        return {"correct": False, "time": time.time() - start, "detail": f"异常: {e}"}


async def run_eval(model: str) -> list[dict]:
    """运行完整评测。"""
    results = []
    async with httpx.AsyncClient() as client:
        for case in TEST_CASES:
            result = await eval_single(client, model, case)
            result["id"] = case["id"]
            result["category"] = case["category"]
            result["model"] = model
            results.append(result)

            status = "✅" if result["correct"] else "❌"
            print(f"  {status} [{case['category']}] {case['id']}: {result['detail']}")

    return results


async def main():
    print("=" * 70)
    print("Agent 工具调用能力评测")
    print(f"测试用例: {len(TEST_CASES)} 个 | 模型: {len(MODELS)} 个")
    print("=" * 70)

    all_results = {}
    for model in MODELS:
        print(f"\n{'='*30} {model} {'='*30}")
        results = await run_eval(model)
        all_results[model] = results

    # 汇总
    print("\n" + "=" * 70)
    print("汇总结果")
    print("=" * 70)

    # 按维度统计
    categories = sorted(set(c["category"] for c in TEST_CASES))
    header = f"{'维度':<16}"
    for m in MODELS:
        header += f" | {m:<20}"
    print(header)
    print("-" * len(header))

    for cat in categories:
        row = f"{cat:<16}"
        for m in MODELS:
            cat_results = [r for r in all_results[m] if r["category"] == cat]
            correct = sum(1 for r in cat_results if r["correct"])
            total = len(cat_results)
            row += f" | {correct}/{total} ({correct/total*100:.0f}%){'':<6}"
        print(row)

    # 总分
    print("-" * len(header))
    row = f"{'总分':<16}"
    for m in MODELS:
        correct = sum(1 for r in all_results[m] if r["correct"])
        total = len(all_results[m])
        row += f" | {correct}/{total} ({correct/total*100:.0f}%){'':<6}"
    print(row)

    # 逐题对比
    print(f"\n{'─'*60}")
    print("逐题对比:")
    print(f"{'─'*60}")
    for case in TEST_CASES:
        scores = []
        for m in MODELS:
            r = next((x for x in all_results[m] if x["id"] == case["id"]), None)
            scores.append("✅" if r and r["correct"] else "❌")
        print(f"  {case['id']:<30} {' vs '.join(scores)}")

    # 保存
    output_path = Path(__file__).parent / "eval_tool_calling_results.json"
    with open(output_path, "w") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    print(f"\n详细结果已保存到: {output_path}")


if __name__ == "__main__":
    asyncio.run(main())
