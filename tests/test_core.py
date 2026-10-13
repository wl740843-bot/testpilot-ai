"""test_core.py：core 模块的单元测试。

小技巧：为了让 pytest 无论从哪个目录运行都能找到 core.py，
先把"项目根目录"（本文件所在的上一级）加进模块搜索路径 sys.path。
"""
import sys
from pathlib import Path

# 把项目根目录加入模块搜索路径
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core import get_greeting, demo_cases, validate_cases


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
