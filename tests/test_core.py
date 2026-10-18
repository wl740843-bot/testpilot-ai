"""test_core.py：core 模块的单元测试。

小技巧：为了让 pytest 无论从哪个目录运行都能找到 core.py，
先把"项目根目录"（本文件所在的上一级）加进模块搜索路径 sys.path。
"""
import sys
from pathlib import Path

# 把项目根目录加入模块搜索路径（必须最先执行，否则找不到 core 模块）
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core import (
    demo_cases,
    validate_cases,
    parse_json,
    generate_cases,
    analyze_failure,
)


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


# ===================== Day6 新增 analyze_failure 测试用例 =====================
def test_analyze_empty_log():
    """空字符串 / 纯空格 / None → ok=False，error包含日志为空"""
    res1 = analyze_failure("")
    assert res1["ok"] is False
    assert "日志为空" in res1["error"]

    res2 = analyze_failure("   \t\n  ")
    assert res2["ok"] is False
    assert "日志为空" in res2["error"]

    res3 = analyze_failure(None)
    assert res3["ok"] is False
    assert "日志为空" in res3["error"]


def test_analyze_normal_log_no_error():
    """普通成功日志 21 passed：函数分析成功 ok=True；error=None；提示文本放在clues[0]"""
    log_text = """test_case_01 PASSED
test_case_02 PASSED
21 passed in 1.20s
"""
    res = analyze_failure(log_text)
    assert res["ok"] is True
    assert res["error"] is None
    assert "未发现" in res["clues"][0]
    assert len(res["clues"]) == 1
    assert len(res["suggestions"]) == 1


def test_analyze_assertion_error_traceback():
    """AssertionError traceback：ok=True；clues捕获报错行+下一行，不带上一行"""
    log_text = """setup step start
AssertionError: assert 10 > 20
teardown finish
"""
    res = analyze_failure(log_text)
    assert res["ok"] is True
    # 只保留报错行 + 下一行（teardown finish），删掉上一行setup断言
    assert any("AssertionError: assert 10 > 20" in line for line in res["clues"])
    assert any("teardown finish" in line for line in res["clues"])


def test_analyze_module_not_found_error():
    """ModuleNotFoundError：ok=True；suggestions 包含 pip install / requirements.txt"""
    log_text = "ModuleNotFoundError: No module named 'pytest-xdist'"
    res = analyze_failure(log_text)
    assert res["ok"] is True
    assert len(res["clues"]) > 0
    assert any("pip install" in s for s in res["suggestions"])
    assert any("requirements.txt" in s for s in res["suggestions"])


def test_analyze_mixed_two_errors():
    """混合 KeyError + TypeError，两个报错都捕获，ok=True"""
    log_text = """KeyError: 'user_id'
TypeError: unsupported operand type(s) for +: 'int' and 'str'
"""
    res = analyze_failure(log_text)
    assert res["ok"] is True
    assert any("KeyError" in clue for clue in res["clues"])
    assert any("TypeError" in clue for clue in res["clues"])
    assert len(res["suggestions"]) >= 2


def test_analyze_duplicate_keyword_dedup_suggestion():
    """同一个报错关键词多次出现 → suggestion自动去重只保留1条；clues两行都捕获"""
    log_text = """ModuleNotFoundError: No module named 'requests'
ModuleNotFoundError: No module named 'numpy'
"""
    res = analyze_failure(log_text)
    assert res["ok"] is True
    unique_suggest = set(res["suggestions"])
    assert len(unique_suggest) == 1
    # 加强断言：两行日志都抓到clues，只是建议去重
    assert len(res["clues"]) == 2


def test_analyze_error_on_last_line_no_next():
    """报错行在日志最后一行，没有下一行，程序不崩溃，ok=True"""
    log_text = """running test suite
AssertionError: actual != expected
"""
    res = analyze_failure(log_text)
    assert res["ok"] is True
    assert len(res["clues"]) > 0


def test_analyze_lowercase_failed_red_first():
    """小写failed BUG：未修复core时，clues无failed → 测试红；修复core后捕获到，变绿【测试先行】
    core原始只匹配大写 FAILED，小写failed识别不到
    """
    log_text = "1 failed, 2 passed in 0.4s"
    res = analyze_failure(log_text)
    # 红绿判断：检查clues是否抓到failed；修复前clues=["未发现..."]，断言失败变红
    assert any("failed" in c.lower() for c in res["clues"])
