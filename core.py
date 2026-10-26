"""core.py：项目的核心逻辑模块。

负责三件事：
1. 测试用例的生成与校验（demo_cases / validate_cases / parse_json / generate_cases）
2. 真实大模型调用（call_llm）
3. pytest 日志分析（analyze_failure）
"""


import json
import os
import requests
from dotenv import load_dotenv

# 读取 .env（找不到文件时静默跳过，不影响纯演示模式运行）
load_dotenv()

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
        # 0. 非字典元素：真实模型可能返回乱数据，直接记错误，不往下走
        if not isinstance(case, dict):
            errors.append(f"第{i}条用例不是字典，无法校验")
            continue
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

    # 新：必须是最外层是列表，字符串/数字/字典都不算用例数据
    if not isinstance(data, list):
        return {"ok": False, "data": [], "error": "JSON 格式正确，但最外层必须是列表（用例数组）。"}

    return {"ok": True, "data": data, "error": None}


def generate_cases(requirement: str, model_text: str = None) -> dict:
    """完整流程：校验输入 → 生成或解析数据 → 校验输出。

    model_text 为 None 时走演示模式（demo_cases 生成）；
    传入模型输出的 JSON 文本时，先用 parse_json 解析，再走验卡员。
    """
    # 1. 校验输入：空需求直接失败，不往下走
    if requirement is None or requirement.strip() == "":
        return {"ok": False, "cases": [], "error": "需求不能为空，请输入要测试的功能描述。"}

    # 2a. 真实模型路线：解析模型文本 → 得到用例
    if model_text is not None:
        parsed = parse_json(model_text)
        if not parsed["ok"]:
            return {"ok": False, "cases": [], "error": "模型输出解析失败：" + parsed["error"]}
        raw_cases = parsed["data"]

    # 2b. 演示模式路线：填表机直接生成
    else:
        demo = demo_cases(requirement)
        if not demo["ok"]:
            return demo
        raw_cases = demo["cases"]

    # 3. 校验输出：生成结果必须过"验卡员"，不合格就打回
    check = validate_cases(raw_cases)
    if not check["ok"]:
        return {
            "ok": False,
            "cases": [],
            "error": "生成的用例未通过校验：" + "; ".join(check["errors"]),
        }

    # 4. 全部通过，交结果
    return {"ok": True, "cases": raw_cases, "error": None}

def has_valid_key() -> bool:
    """判断 .env 是否配置了有效的 API Key（非空且不是占位符）。"""
    key = os.getenv("DASHSCOPE_API_KEY", "").strip()
    return bool(key) and key != "your_key_here"

def resolve_mode(choice: str) -> str:
    """根据用户模式选择 + 是否有 Key，解析最终运行模式。

    返回 "真实模型" 或 "演示模式"：
    - 强制演示模式 → 演示模式
    - 强制真实模型 → 真实模型
    - 自动（默认）→ 有 Key 走真实模型，否则演示模式
    """
    if choice == "强制演示模式":
        return "演示模式"
    if choice == "强制真实模型":
        return "真实模型"
    return "真实模型" if has_valid_key() else "演示模式"

def call_llm(prompt: str, timeout: int = 30) -> dict:
    """调用真实大模型（阿里百炼 · OpenAI 兼容接口），返回模型回复文本。

    返回统一结构：
        {"ok": True, "content": "模型回复文本", "error": None}   成功
        {"ok": False, "content": "", "error": "人话提示"}        失败

    错误处理原则：
    1. 配置缺失 → 明确报错，不发请求；
    2. 网络层错误（连不上 / 超时）→ 提示检查网络；
    3. HTTP 错误（401 / 429 / 5xx）→ 按状态码给对应的人话提示；
    4. 任何错误信息都不打印 API Key，不泄露请求细节。
    """
    # 1. 读配置（每次调用现读，改 .env 无需重启解释器）
    api_key = os.getenv("DASHSCOPE_API_KEY", "").strip()
    base_url = os.getenv("DASHSCOPE_BASE_URL", "").strip()
    model = os.getenv("DASHSCOPE_MODEL", "qwen-plus").strip()

    # 2. 配置检查：没配齐就明确报错，绝不带着假配置发请求
    if not has_valid_key():
        return {"ok": False, "content": "", "error": "未配置 DASHSCOPE_API_KEY，请在 .env 中填入真实 API Key，或使用演示模式。"}
    if not base_url or "{WorkspaceId}" in base_url:
        return {"ok": False, "content": "", "error": "BASE_URL 未配置或仍是占位符，请在 .env 中填写正确的 API 根地址。"}

    # 3. 组装请求：根地址 + 聊天窗口
    url = base_url.rstrip("/") + "/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
    }

    # 4. 发送请求：网络层错误在这里接住（请求没到服务器）
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=timeout)
    except requests.exceptions.Timeout:
        return {"ok": False, "content": "", "error": f"请求超时（{timeout} 秒），请检查网络后重试。"}
    except requests.exceptions.ConnectionError:
        return {"ok": False, "content": "", "error": "无法连接到模型服务，请检查 BASE_URL 拼写和网络连接。"}
    except requests.exceptions.RequestException as e:
        return {"ok": False, "content": "", "error": f"请求发生异常：{e.__class__.__name__}。请稍后重试。"}

    # 5. HTTP 状态码分类：请求到了服务器，但结果不理想
    if resp.status_code == 200:
        try:
            data = resp.json()
            answer = data["choices"][0]["message"]["content"]
        except (ValueError, KeyError, IndexError):
            return {"ok": False, "content": "", "error": "响应格式异常：未能从返回内容中解析出模型回复。"}
        return {"ok": True, "content": answer, "error": None}

    if resp.status_code == 401:
        return {"ok": False, "content": "", "error": "鉴权失败（401）：API Key 无效或已过期，请检查 .env 中的 Key。"}
    if resp.status_code == 429:
        return {"ok": False, "content": "", "error": "请求过于频繁（429）：已触发限流，请在 .env 中改用 qwen-plus 等高限流模型，或稍等 1 分钟重试。"}
    if resp.status_code >= 500:
        return {"ok": False, "content": "", "error": f"模型服务暂时出错（{resp.status_code}），请稍后重试。"}
    return {"ok": False, "content": "", "error": f"未预期的状态码 {resp.status_code}，响应内容：{resp.text[:200]}"}


# ============ 真实模型生成用例：提示词 + 完整流程 ============
# Day 10 正式版提示词：明确 6 字段约定 + 给出示例输出，让模型照着抄格式。
LLM_PROMPT_TEMPLATE = """你是软件测试专家。请根据下面的需求生成测试用例，只输出 JSON 数组，不要输出任何其他文字、代码块标记或解释。

每个用例必须是 JSON 对象，包含且仅包含以下 6 个字段：
- title: 用例标题（字符串）
- preconditions: 前置条件（字符串）
- steps: 测试步骤（字符串数组）
- expected: 预期结果（字符串）
- priority: 优先级，只能是 "高"、"中"、"低"
- test_type: 测试类型，只能是 "功能测试"、"异常测试"、"边界测试"

要求覆盖正常、异常、边界三类场景。

预期结果硬性要求（违反即为不合格）：
1. 预期必须"唯一、具体、可观测"——写完读一遍，应能立刻判断符合还是不符合。
2. 禁止用"或""若…否则…""视情况"等字眼连接多个不同结果（如"提示X或提示Y""跳转或提示"均不允许）。
3. 禁止"合理结果""无报错""正确处理""正常提示"等含糊词，必须写出具体的提示文案或页面状态（如"显示'密码不能为空'并停留在注册页"）。

假设硬性要求：
- 需求未提及的具体规则、数值、技术方案（如长度上限、库存值、验证码、JWT、支付方式）不得当作既定事实；确需使用时必须标注"（假设：XXX，待与需求确认）"。

格式请严格参考下面的示例（示例内容仅为格式演示，请按实际需求生成内容）：

[
  {
    "title": "正常流程：输入有效数据",
    "preconditions": "系统可用，用户已进入对应页面",
    "steps": ["打开功能页面", "输入有效数据", "点击提交"],
    "expected": "显示'操作成功'提示并停留在当前页面",
    "priority": "高",
    "test_type": "功能测试"
  }
]

需求：
{requirement}
"""


def generate_cases_with_llm(requirement: str, max_retries: int = 2) -> dict:
    """真实模型完整流程：调模型生成 → 解析校验 → 不合格有限次数修正。

    返回统一结构（与 generate_cases 一致）：
        {"ok": True, "cases": [...], "error": None}    成功
        {"ok": False, "cases": [], "error": "原因"}    失败

    max_retries：解析/校验失败后最多重写几次（默认 2，即最多共调用 3 次）。
    限制次数是为了避免"无限重试"白烧 token、无限等待。
    """
    # 1. 拦空需求：不浪费任何一次模型调用
    if requirement is None or requirement.strip() == "":
        return {"ok": False, "cases": [], "error": "需求不能为空，请输入要测试的功能描述。"}

    # 2. 循环调用：第 1 次 + 最多 max_retries 次修正
    # 用 replace 而非 .format()：模板示例 JSON 自带花括号，format 会把 {title} 等误当占位符
    prompt = LLM_PROMPT_TEMPLATE.replace("{requirement}", requirement)
    for attempt in range(1, max_retries + 2):
        llm = call_llm(prompt)
        if not llm["ok"]:
            return {"ok": False, "cases": [], "error": "模型调用失败：" + llm["error"]}

        result = generate_cases(requirement, model_text=llm["content"])
        if result["ok"]:
            return result

        # 解析/校验失败：把错误原因反馈给模型，让它重写（但不超过 max_retries 次）
        if attempt <= max_retries:
            prompt = (
                LLM_PROMPT_TEMPLATE.replace("{requirement}", requirement)
                + "\n\n你上一次的输出未通过程序校验，原因："
                + result["error"]
                + "\n请重新生成，务必只输出合法 JSON 数组，不要任何额外文字。"
            )

    # 3. 修正次数用完仍未通过：如实报错，绝不把非法数据当有效用例
    return {"ok": False, "cases": [], "error": f"模型连续 {max_retries + 1} 次输出未通过校验：{result['error']}"}
# ============ pytest 日志分析：报错关键词 → 排查建议 对照表 ============
# 线索归线索，结论归结论：这里只给"排查方向"，不给"已确认根因"。
FAILURE_RULES = {
    "AssertionError": "断言失败：期望值和实际值不一致，检查被断言的条件、输入数据和预期结果",
    "TypeError": "类型错误：函数收到不匹配的数据类型，检查变量类型和函数传参",
    "KeyError": "键错误：字典里没有这个 key，检查字典内容、拼写和构造来源",
    "ModuleNotFoundError": "模块未安装：依赖没装进当前虚拟环境，检查 requirements.txt 并执行 pip install -r requirements.txt",
    "ImportError": "导入失败：模块存在但导入出错，检查文件路径、命名冲突和循环导入",
    "FileNotFoundError": "文件未找到：路径不对或文件不存在，检查路径写法、当前工作目录和文件是否生成",
    "TimeoutError": "超时：操作超过等待时间，检查网络、服务响应时间和等待时长设置",
    "FAILED": "用例执行失败：pytest 判定该用例未通过，需结合上方具体报错信息定位",
}


def analyze_failure(log_text: str) -> dict:
    """把报错日志翻译成排查方向（线索 + 初步建议，不下结论）。

    返回统一结构：
        {"ok": True, "clues": [...], "suggestions": [...], "error": None}    正常
        {"ok": False, "clues": [], "suggestions": [], "error": "原因"}        输入为空
    """
    # 1. 空日志 / 纯空格：明确提示，不假装分析
    if log_text is None or log_text.strip() == "":
        return {
            "ok": False,
            "clues": [],
            "suggestions": [],
            "error": "日志为空，请粘贴要分析的报错内容。",
        }

    clues = []
    suggestions = []
    lines = log_text.splitlines()

    # 2. 逐行扫描：找关键词，记"第几行 + 命中行原文 + 下一行"
    for i, line in enumerate(lines, start=1):
        for keyword, advice in FAILURE_RULES.items():
            if keyword.lower() in line.lower():
                snippet = line.strip()
                if i < len(lines):
                    snippet += " → " + lines[i].strip()
                clues.append(f"第{i}行出现 {keyword}：{snippet}")
                if advice not in suggestions:
                    suggestions.append(advice)
                break  # 一行只认一个关键词，避免刷屏

    # 3. 一个关键词都没中：普通日志
    if not clues:
        return {
            "ok": True,
            "clues": ["未发现常见报错关键词。"],
            "suggestions": ["日志中没有匹配到常见报错，建议补充完整的 traceback 后重新分析。"],
            "error": None,
        }

    # 4. 有关键词：交线索和建议
    return {"ok": True, "clues": clues, "suggestions": suggestions, "error": None}

