#!/usr/bin/env python3
"""Integration test for tool call parser fix."""

import json
import sys
sys.path.insert(0, '/Users/berton/Github/omlx')

from omlx.api.tool_calling import (
    _serialize_tool_call_arguments,
    _has_quoted_keys,
    _clean_quoted_keys,
)


def test_has_quoted_keys():
    """Test _has_quoted_keys function."""
    # Test with quoted keys
    assert _has_quoted_keys({'"action"': 'add'}) is True
    assert _has_quoted_keys({'"key"': 'value', 'normal': 'test'}) is True
    assert _has_quoted_keys({'normal': 'test'}) is False
    assert _has_quoted_keys({}) is False
    print("✅ ISC-3: _has_quoted_keys 正常工作")
    return True


def test_clean_quoted_keys():
    """Test _clean_quoted_keys function."""
    # Test basic quoted key (the key literally contains quotes as characters)
    # This happens when the parser returns a dict with keys like r'"key"'
    # Note: In Python dict, the key is the string r'"key"' (5 chars: quote, k, e, y, quote)
    test_dict = {r'"action"': 'add'}
    result = _clean_quoted_keys(test_dict)
    assert result == {'action': 'add'}, f"Expected {{'action': 'add'}}, got {result}"

    # Test mixed keys
    test_dict2 = {r'"key"': 'value', 'normal': 'test'}
    result2 = _clean_quoted_keys(test_dict2)
    assert result2 == {'key': 'value', 'normal': 'test'}, f"Expected {{'key': 'value', 'normal': 'test'}}, got {result2}"

    print("✅ ISC-4: _clean_quoted_keys 正常工作")
    return True


def test_serialize_json_string():
    """Test serializing JSON string arguments."""
    # Test valid JSON string
    json_str = '{"city": "Berlin", "country": "Germany"}'
    result = _serialize_tool_call_arguments(json_str)
    assert result == json_str
    print("✅ ISC-5: omlx 能正确处理 JSON 字符串格式的参数")
    return True


def test_serialize_dict():
    """Test serializing dict arguments."""
    # Test dict input
    dict_input = {"city": "Berlin", "country": "Germany"}
    result = _serialize_tool_call_arguments(dict_input)
    assert result == json.dumps(dict_input, ensure_ascii=False)
    print("✅ ISC-6: omlx 能正确处理 dict 格式的参数")
    return True


def test_serialize_invalid():
    """Test serializing invalid arguments."""
    # Test invalid JSON string
    result = _serialize_tool_call_arguments("not json")
    assert result == "{}"
    # Test non-dict JSON
    result = _serialize_tool_call_arguments('"just a string"')
    assert result == "{}"
    # Test unknown type
    result = _serialize_tool_call_arguments(123)
    assert result == "{}"
    print("✅ ISC-7: omlx 对无效参数返回空对象而不是崩溃")
    return True


def test_quoted_keys_workaround():
    """Test the workaround for quoted keys."""
    # This simulates the bug case where mlx-vlm parser returns a dict
    # with keys that contain embedded quotes
    # The dict has keys like r'"action"' (literally quote-action-quote)

    # Simulate what happens when json.loads parses a string with quoted keys
    # and the result has embedded quotes in the keys
    problematic_dict = {r'"action"': 'add', r'"content"': 'test'}

    result = _serialize_tool_call_arguments(problematic_dict)
    parsed = json.loads(result)

    # The workaround should clean the keys
    assert parsed == {"action": "add", "content": "test"}, \
        f"Expected {{'action': 'add', 'content': 'test'}}, got {parsed}"

    print("✅ ISC-8: omlx 兼容性修复处理带引号的键")
    return True


def test_nested_structures():
    """Test handling nested objects and arrays."""
    # Test nested object
    nested = '{"config": {"enabled": true, "level": 5}}'
    result = _serialize_tool_call_arguments(nested)
    parsed = json.loads(result)
    assert parsed["config"]["enabled"] is True
    assert parsed["config"]["level"] == 5

    # Test array
    array = '{"items": [1, 2, 3]}'
    result = _serialize_tool_call_arguments(array)
    parsed = json.loads(result)
    assert parsed["items"] == [1, 2, 3]
    print("✅ ISC-11: 修复处理嵌套对象和数组")
    return True


def test_unicode_escapes():
    """Test handling Unicode escape sequences."""
    unicode_str = r'{"action": "add", "content": "2026-04-25 > \u672c\u5730\u73af\u5883"}'
    result = _serialize_tool_call_arguments(unicode_str)
    parsed = json.loads(result)
    assert "本地环境" in parsed["content"]
    print("✅ ISC-12: 修复处理 Unicode 转义序列")
    return True


def main():
    """Run all tests."""
    tests = [
        test_has_quoted_keys,
        test_clean_quoted_keys,
        test_serialize_json_string,
        test_serialize_dict,
        test_serialize_invalid,
        test_quoted_keys_workaround,
        test_nested_structures,
        test_unicode_escapes,
    ]

    failed = []
    for test in tests:
        try:
            test()
        except AssertionError as e:
            print(f"❌ {test.__name__} 失败: {e}")
            failed.append(test.__name__)
        except Exception as e:
            print(f"❌ {test.__name__} 错误: {e}")
            failed.append(test.__name__)

    if failed:
        print(f"\n❌ {len(failed)} 个测试失败: {', '.join(failed)}")
        return 1
    else:
        print(f"\n✅ 所有 {len(tests)} 个测试通过!")
        return 0


if __name__ == "__main__":
    sys.exit(main())
