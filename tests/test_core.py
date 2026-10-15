"""test_core.py：core 模块的单元测试。

小技巧：为了让 pytest 无论从哪个目录运行都能找到 core.py，
先把"项目根目录"（本文件所在的上一级）加进模块搜索路径 sys.path。
"""
import sys
from pathlib import Path

# 把项目根目录加入模块搜索路径
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core import get_greeting, demo_cases, validate_cases, parse_json, generate_cases


def test_get_greeting_with_name():
    """传入名字时，返回对应的问候语。"""
    assert get_greeting("小明") == "你好，小明！"


def test_get_greeting_default():
    """不传参数时，使用默认值"世界"。"""
    assert get_greeting() == "你好，世界！"


def test_demo_cases_normal():
    """正常需求：返回 3 条完整用例，6 个字段齐全。"""
    result = demo_cases("登录功能")
    assert result["ok"] is True
    assert len(result["cases"]) == 3
    for case in result["cases"]:
        for field in ["title", "preconditions", "steps", "expected", "priority", "test_type"]:
            assert field in case


def test_demo_cases_empty():
    """空需求：明确报错，不生成假用例。"""
    result = demo_cases("")
    assert result["ok"] is False
    assert result["cases"] == []
    assert "不能为空" in result["error"]


def test_demo_cases_blank():
    """纯空格需求：按空需求处理。"""
    result = demo_cases("   ")
    assert result["ok"] is False


def test_validate_cases_good():
    """完整用例：体检通过。"""
    result = validate_cases(demo_cases("登录功能")["cases"])
    assert result["ok"] is True


def test_validate_cases_missing_field():
    """缺字段：明确报告缺少的字段。"""
    result = validate_cases([{"title": "只有标题"}])
    assert result["ok"] is False
    assert "缺少字段" in result["errors"][0]


def test_validate_cases_wrong_type():
    """steps 不是列表：报告类型错误。"""
    cases = [{"title": "x", "preconditions": "无", "steps": "点按钮",
              "expected": "成功", "priority": "高", "test_type": "功能测试"}]
    result = validate_cases(cases)
    assert result["ok"] is False
    assert any("steps 必须是列表" in e for e in result["errors"])


def test_validate_cases_empty_list():
    """空列表：被拒绝。"""
    result = validate_cases([])
    assert result["ok"] is False


def test_parse_json_valid():
    """合法 JSON 列表可以解析成 Python 数据。"""
    result = parse_json('[{"title": "登录", "priority": "高"}]')
    assert result["ok"] is True
    assert result["data"][0]["title"] == "登录"


def test_parse_json_rejects_string():
    """解析出字符串：不是用例列表，拒绝。"""
    result = parse_json('"hello"')
    assert result["ok"] is False
    assert "列表" in result["error"]


def test_parse_json_rejects_number():
    """解析出数字：不是用例列表，拒绝。"""
    result = parse_json('123')
    assert result["ok"] is False
    assert "列表" in result["error"]


def test_parse_json_rejects_dict():
    """解析出字典：不是用例列表，拒绝。"""
    result = parse_json('{"a": 1}')
    assert result["ok"] is False
    assert "列表" in result["error"]


def test_parse_json_invalid():
    """非法 JSON 被捕获，返回可理解的错误，不崩溃。"""
    result = parse_json("这不是 JSON")
    assert result["ok"] is False
    assert "JSON" in result["error"]


def test_parse_json_empty():
    """空文本直接报错。"""
    result = parse_json("")
    assert result["ok"] is False
    assert "为空" in result["error"]


def test_generate_cases_normal():
    """正常需求：流水线全过，返回 3 条用例。"""
    result = generate_cases("注册功能")
    assert result["ok"] is True
    assert len(result["cases"]) == 3


def test_generate_cases_empty():
    """空需求：第一道关卡拦截。"""
    result = generate_cases("")
    assert result["ok"] is False
    assert "不能为空" in result["error"]


def test_generate_cases_with_model_text():
    """模型路线：合法用例列表 JSON 走完全链路。"""
    model_text = ('[{"title": "登录", "preconditions": "系统可用", '
                  '"steps": ["输入账号"], "expected": "登录成功", '
                  '"priority": "高", "test_type": "功能测试"}]')
    result = generate_cases("登录功能", model_text=model_text)
    assert result["ok"] is True
    assert len(result["cases"]) == 1


def test_generate_cases_with_bad_model_text():
    """模型路线：非法 JSON 被拦截，提示可理解。"""
    result = generate_cases("登录功能", model_text="这不是JSON")
    assert result["ok"] is False
    assert "解析失败" in result["error"]


def test_generate_cases_with_nonlist_model_text():
    """模型路线：解析成功但不是列表，被拦截。"""
    result = generate_cases("登录功能", model_text='{"title": "登录"}')
    assert result["ok"] is False
    assert "解析失败" in result["error"]

def test_validate_cases_non_dict():
    """非字典用例：返回错误，不崩溃。"""
    result = validate_cases(["title"])
    assert result["ok"] is False
    assert "不是字典" in result["errors"][0]
