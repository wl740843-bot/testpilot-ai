"""core.py：项目的核心逻辑模块。

Day 1 先放一个简单的示例函数，
页面入口（app.py）和测试（tests/test_core.py）都会 import 它，
用来演示"模块如何被调用"。
"""

import json

# ============ 测试用例的统一数据结构约定 ============
# 一条用例 = 一个字典，必须包含下面 6 个字段，谁都不能少。
# 以后演示模式、真实模型生成的结果，都按这个格式来。
REQUIRED_FIELDS = [
    "title",  # 用例标题：这条用例测什么
    "preconditions",  # 前置条件：测试开始前环境要满足什么
    "steps",  # 测试步骤：字符串列表，一步步怎么操作
    "expected",  # 预期结果：操作完应该看到什么
    "priority",  # 优先级：高 / 中 / 低
    "test_type",  # 测试类型：功能测试 / 异常测试 / 边界测试
]


def get_greeting(name: str = "世界") -> str:
    """根据名字返回一句问候语。

    参数：
        name: 要问候的名字，不传时默认"世界"。

    返回：
        形如 "你好，XX！" 的字符串。
    """
    return f"你好，{name}！"


def demo_cases(requirement: str) -> dict:
    """演示模式：根据需求生成固定格式的示例测试用例。

    返回统一结构：
        {"ok": True, "cases": [...], "error": None}   成功
        {"ok": False, "cases": [], "error": "原因"}   失败（空需求）
    """
    # 空需求 / 纯空格需求：绝不假装生成结果，明确报错
    if requirement is None or requirement.strip() == "":
        return {
            "ok": False,
            "cases": [],
            "error": "需求不能为空，请输入要测试的功能描述。",
        }

    # 正常需求：生成 3 条演示用例（正常 / 异常 / 边界）
    cases = [
        {
            "title": f"{requirement}-正常流程",
            "preconditions": "系统可用，用户已进入对应页面",
            "steps": ["打开功能页面", "输入有效数据", "点击提交"],
            "expected": "操作成功，无报错",
            "priority": "高",
            "test_type": "功能测试",
        },
        {
            "title": f"{requirement}-异常输入",
            "preconditions": "系统可用，用户已进入对应页面",
            "steps": ["打开功能页面", "输入非法数据", "点击提交"],
            "expected": "给出明确的错误提示，不崩溃",
            "priority": "中",
            "test_type": "异常测试",
        },
        {
            "title": f"{requirement}-边界值",
            "preconditions": "系统可用，用户已进入对应页面",
            "steps": ["打开功能页面", "输入边界值数据", "点击提交"],
            "expected": "按边界规则正确处理",
            "priority": "中",
            "test_type": "边界测试",
        },
    ]
    return {"ok": True, "cases": cases, "error": None}


def validate_cases(cases: list) -> dict:
    """校验用例列表：字段是否齐全、类型是否合理。

    返回：
        {"ok": True, "errors": []}                      全部通过
        {"ok": False, "errors": ["第1条缺少字段: title"]}  有问题
    """
    errors = []

    # 一个用例都没有，也算问题
    if not cases:
        return {"ok": False, "errors": ["用例列表为空，没有任何用例。"]}

    for i, case in enumerate(cases, start=1):
        # 1. 检查 6 个必需字段是否都存在
        for field in REQUIRED_FIELDS:
            if field not in case:
                errors.append(f"第{i}条用例缺少字段: {field}")

        # 2. 检查类型是否合理
        if "title" in case and not isinstance(case["title"], str):
            errors.append(f"第{i}条用例 title 必须是字符串")
        if "steps" in case and not isinstance(case["steps"], list):
            errors.append(f"第{i}条用例 steps 必须是列表")
        if "expected" in case and not isinstance(case["expected"], str):
            errors.append(f"第{i}条用例 expected 必须是字符串")

    if errors:
        return {"ok": False, "errors": errors}
    return {"ok": True, "errors": []}


def parse_json(text: str) -> dict:
    """把模型返回的文本解析成 Python 数据。

    返回统一结构：
        {"ok": True, "data": [...], "error": None}    解析成功
        {"ok": False, "data": [], "error": "原因"}    解析失败
    """
    # 空文本：直接报错，别去解析
    if text is None or text.strip() == "":
        return {"ok": False, "data": [], "error": "模型返回内容为空。"}

    # 尝试解析 JSON；失败会被 except 接住，程序不崩溃
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        return {"ok": False, "data": [], "error": f"不是合法的 JSON 格式：{e}"}

    return {"ok": True, "data": data, "error": None}


def generate_cases(requirement: str) -> dict:
    """完整流程：校验输入 → 生成数据 → 校验输出。

    Day 3 先用演示模式（demo_cases）生成，
    以后接入真实模型时，把中间这步换成模型调用即可。
    """
    # 1. 校验输入：空需求直接失败，不往下走
    demo = demo_cases(requirement)
    if not demo["ok"]:
        return demo

    # 2. 校验输出：生成结果必须过"验卡员"，不合格就打回
    check = validate_cases(demo["cases"])
    if not check["ok"]:
        return {
            "ok": False,
            "cases": [],
            "error": "生成的用例未通过校验：" + "; ".join(check["errors"]),
        }

    # 3. 全部通过，交结果
    return demo
