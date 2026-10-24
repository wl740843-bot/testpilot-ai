"""test_llm_robustness.py：Day 13 异常与边界测试。

覆盖计划文档 Day 13 要求的五类场景：
1. 模型超时 / 网络断开 / 401 / 429 / 5xx / 未知状态码
2. 返回空内容、非法 JSON、多余文本（```json 包裹等）
3. 超长需求、特殊字符、空输入
4. 字段缺失 / 响应结构异常
5. 所有失败路径绝不泄露 API Key

原则：不发起真实网络请求——全部用 monkeypatch 模拟，测试默认不依赖真实 API。
"""
import sys
from pathlib import Path

import requests
import pytest

# 把项目根目录加入模块搜索路径（必须最先执行，否则找不到 core 模块）
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import core
from core import call_llm, generate_cases_with_llm, parse_json

# 测试用的假 Key / 假地址：所有"不泄露"断言都以它为准
FAKE_KEY = "sk-fake-secret-123456"
FAKE_BASE = "https://fake.example.com/compatible-mode/v1"


@pytest.fixture(autouse=True)
def fake_env(monkeypatch):
    """每个测试前注入假配置；测试结束自动恢复真实环境。"""
    monkeypatch.setenv("DASHSCOPE_API_KEY", FAKE_KEY)
    monkeypatch.setenv("DASHSCOPE_BASE_URL", FAKE_BASE)
    monkeypatch.setenv("DASHSCOPE_MODEL", "qwen-plus")


class FakeResponse:
    """造一个假的 requests.Response，只提供 call_llm 用到的三个成员。"""

    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self._payload = payload if payload is not None else {}

    def json(self):
        return self._payload

    @property
    def text(self):
        return str(self._payload)


def make_post_raiser(exc):
    """返回一个会抛出指定异常的 fake_post（用于网络层失败模拟）。"""

    def fake_post(*args, **kwargs):
        raise exc

    return fake_post


# ============ 1. 网络层失败：超时 / 连接不上 / 其他请求异常 ============

def test_call_llm_timeout_no_key_leak(monkeypatch):
    """请求超时：返回可理解错误，且绝不泄露 Key。setattr(工具箱, "锤子", 新锤子)
"""
    monkeypatch.setattr(core.requests, "post",
                        make_post_raiser(requests.exceptions.Timeout()))
    result = call_llm("你好")
    assert result["ok"] is False
    assert "超时" in result["error"]
    assert FAKE_KEY not in result["error"]


def test_call_llm_connection_error(monkeypatch):
    """连接不上：提示检查 BASE_URL 和网络。"""
    monkeypatch.setattr(core.requests, "post",
                        make_post_raiser(requests.exceptions.ConnectionError()))
    result = call_llm("你好")
    assert result["ok"] is False
    assert "网络" in result["error"]
    assert FAKE_KEY not in result["error"]


def test_call_llm_generic_request_exception(monkeypatch):
    """其他请求异常（如编码类错误）：按通用 RequestException 兜底。"""
    monkeypatch.setattr(core.requests, "post",
                        make_post_raiser(requests.exceptions.RequestException()))
    result = call_llm("你好")
    assert result["ok"] is False
    assert "请求发生异常" in result["error"]
    assert FAKE_KEY not in result["error"]


# ============ 2. HTTP 状态码失败：401 / 429 / 5xx / 未知 ============

def test_call_llm_401(monkeypatch):
    """鉴权失败：提示检查 Key，且错误信息不含 Key 本身。"""
    monkeypatch.setattr(core.requests, "post",
                        lambda *a, **k: FakeResponse(401, {"error": "invalid key"}))
    # 等价写法：
    # def fake_post(*a, **k):
    #     return FakeResponse(401, {"error": "invalid key"})
    result = call_llm("你好")
    assert result["ok"] is False
    assert "鉴权失败" in result["error"]
    assert FAKE_KEY not in result["error"]
    assert "invalid key" not in result["error"]  # 服务端响应原文也不回显


def test_call_llm_429(monkeypatch):
    """限流：提示改 qwen-plus 或稍等重试。"""
    monkeypatch.setattr(core.requests, "post",
                        lambda *a, **k: FakeResponse(429, {}))
    result = call_llm("你好")
    assert result["ok"] is False
    assert "限流" in result["error"]


def test_call_llm_500(monkeypatch):
    """服务端 5xx：提示稍后重试。"""
    monkeypatch.setattr(core.requests, "post",
                        lambda *a, **k: FakeResponse(503, {}))
    result = call_llm("你好")
    assert result["ok"] is False
    assert "暂时出错" in result["error"]


def test_call_llm_unexpected_status(monkeypatch):
    """未预期的状态码（如 418）：给出状态码和响应片段。"""
    monkeypatch.setattr(core.requests, "post",
                        lambda *a, **k: FakeResponse(418, {"msg": "teapot"}))
    result = call_llm("你好")
    assert result["ok"] is False
    assert "418" in result["error"]
    assert FAKE_KEY not in result["error"]


# ============ 3. HTTP 200 但响应结构异常 / 空内容 ============

def test_call_llm_200_missing_choices(monkeypatch):
    """200 但缺 choices 字段：捕获 KeyError → 响应格式异常。"""
    monkeypatch.setattr(core.requests, "post",
                        lambda *a, **k: FakeResponse(200, {"choices": []}))
    result = call_llm("你好")
    assert result["ok"] is False
    assert "响应格式异常" in result["error"]
    assert FAKE_KEY not in result["error"]


def test_call_llm_200_empty_content(monkeypatch):
    """200 但 content 为空字符串：call_llm 如实返回空文本（交给下游 parse_json 拦截）。"""
    monkeypatch.setattr(core.requests, "post",
                        lambda *a, **k: FakeResponse(
                            200, {"choices": [{"message": {"content": ""}}]}))
    result = call_llm("你好")
    assert result["ok"] is True
    assert result["content"] == ""


def test_call_llm_200_normal(monkeypatch):
    """200 且结构正常：ok=True，content 取到模型回复。"""
    monkeypatch.setattr(core.requests, "post",
                        lambda *a, **k: FakeResponse(
                            200, {"choices": [{"message": {"content": "这是回复"}}]}))
    result = call_llm("你好")
    assert result["ok"] is True
    assert result["content"] == "这是回复"


# ============ 4. 配置缺失 / 占位符 ============

def test_call_llm_missing_key(monkeypatch):
    """没配 API Key：直接报错，不发请求。"""
    monkeypatch.delenv("DASHSCOPE_API_KEY")
    result = call_llm("你好")
    assert result["ok"] is False
    assert "未配置" in result["error"]


def test_call_llm_placeholder_base_url(monkeypatch):
    """BASE_URL 还是 {WorkspaceId} 占位符：明确报错。"""
    monkeypatch.setenv("DASHSCOPE_BASE_URL", "https://x/{WorkspaceId}/v1")
    result = call_llm("你好")
    assert result["ok"] is False
    assert "BASE_URL" in result["error"]


# ============ 5. parse_json 输入边界：多余文本 / 特殊字符 ============

def test_parse_json_markdown_wrapped_rejected():
    """模型返回带 ```json 代码块包裹：目前不容错，明确报"不是合法的 JSON"。"""
    text = '```json\n[{"title": "登录", "priority": "高"}]\n```'
    result = parse_json(text)
    assert result["ok"] is False
    assert "JSON" in result["error"]


def test_parse_json_extra_text_rejected():
    """模型返回"好的，结果如下："+JSON：多余文本导致解析失败（不静默吞掉）。"""
    result = parse_json('好的，结果如下：[{"title": "登录"}]')
    assert result["ok"] is False
    assert "JSON" in result["error"]


# ============ 6. generate_cases_with_llm：重试机制与输入边界 ============

def test_generate_with_llm_empty_requirement_no_call(monkeypatch):
    """空需求：第一道关卡拦截，模型一次都不调用。"""
    calls = []

    def fake_call_llm(prompt):
        calls.append(prompt)
        return {"ok": True, "content": "[]", "error": None}

    monkeypatch.setattr(core, "call_llm", fake_call_llm)
    result = generate_cases_with_llm("   ")
    assert result["ok"] is False
    assert "不能为空" in result["error"]
    assert calls == []


def test_generate_with_llm_markdown_wrapped_retry_success(monkeypatch):
    """模型第 1 次返回 ```json 包裹文本（解析失败）→ 自动重写 → 第 2 次合法 → ok。

    验证"失败反馈重写"机制：错误原因喂回模型，最多修正 max_retries 次。
    """
    good = ('[{"title": "登录", "preconditions": "系统可用", '
            '"steps": ["输入账号"], "expected": "登录成功", '
            '"priority": "高", "test_type": "功能测试"}]')
    replies = [f"```json\n{good}\n```", good]
    prompts = []

    def fake_call_llm(prompt):
        prompts.append(prompt)
        return {"ok": True, "content": replies[len(prompts) - 1], "error": None}

    monkeypatch.setattr(core, "call_llm", fake_call_llm)
    result = generate_cases_with_llm("登录功能")
    assert result["ok"] is True
    assert len(prompts) == 2  # 第 1 次失败 + 1 次修正
    assert "解析失败" in prompts[1]  # 第二次的 prompt 带上了失败原因


def test_generate_with_llm_missing_field_retry_success(monkeypatch):
    """模型第 1 次返回缺字段用例（校验失败）→ 自动重写 → 第 2 次完整 → ok。"""
    bad = '[{"title": "登录", "priority": "高"}]'
    good = ('[{"title": "登录", "preconditions": "系统可用", '
            '"steps": ["输入账号"], "expected": "登录成功", '
            '"priority": "高", "test_type": "功能测试"}]')
    replies = [bad, good]
    prompts = []

    def fake_call_llm(prompt):
        prompts.append(prompt)
        return {"ok": True, "content": replies[len(prompts) - 1], "error": None}

    monkeypatch.setattr(core, "call_llm", fake_call_llm)
    result = generate_cases_with_llm("登录功能")
    assert result["ok"] is True
    assert len(prompts) == 2
    assert "未通过程序校验" in prompts[1]


def test_generate_with_llm_always_empty_content_gives_up(monkeypatch):
    """模型每次都返回空内容：重试次数用完后如实报错，不把空数据当结果。"""
    calls = []

    def fake_call_llm(prompt):
        calls.append(prompt)
        return {"ok": True, "content": "", "error": None}

    monkeypatch.setattr(core, "call_llm", fake_call_llm)
    result = generate_cases_with_llm("登录功能", max_retries=1)
    assert result["ok"] is False
    assert "连续" in result["error"] and "未通过校验" in result["error"]
    assert len(calls) == 2  # 第 1 次 + 1 次修正


def test_generate_with_llm_long_requirement(monkeypatch):
    """超长需求（5000 字符）：不崩溃，正常走链路。"""
    long_req = "用户登录功能" + "（附加说明：系统需支持多端，界面简洁）" * 400  # 约 5000 字符
    good = ('[{"title": "登录", "preconditions": "系统可用", '
            '"steps": ["输入账号"], "expected": "登录成功", '
            '"priority": "高", "test_type": "功能测试"}]')

    def fake_call_llm(prompt):
        assert len(prompt) > len(long_req)  # 需求确实拼进了 prompt
        return {"ok": True, "content": good, "error": None}

    monkeypatch.setattr(core, "call_llm", fake_call_llm)
    result = generate_cases_with_llm(long_req)
    assert result["ok"] is True


def test_generate_with_llm_special_chars(monkeypatch):
    """需求含引号、换行、中文标点、emoji：模板替换后不炸，链路正常。"""
    tricky = '登录"功能"\n密码：\'abc\'；<script>alert(1)</script> 🔐'
    good = ('[{"title": "登录", "preconditions": "系统可用", '
            '"steps": ["输入账号"], "expected": "登录成功", '
            '"priority": "高", "test_type": "功能测试"}]')

    def fake_call_llm(prompt):
        assert tricky in prompt
        return {"ok": True, "content": good, "error": None}

    monkeypatch.setattr(core, "call_llm", fake_call_llm)
    result = generate_cases_with_llm(tricky)
    assert result["ok"] is True


# ============ 7. 统一 Key 不泄露防线 ============

@pytest.mark.parametrize("fake_post_factory,status", [
    (lambda: make_post_raiser(requests.exceptions.Timeout()), "超时"),
    (lambda: make_post_raiser(requests.exceptions.ConnectionError()), "连接"),
    (lambda: lambda *a, **k: FakeResponse(401, {}), "401"),
    (lambda: lambda *a, **k: FakeResponse(429, {}), "429"),
    (lambda: lambda *a, **k: FakeResponse(500, {}), "500"),
    (lambda: lambda *a, **k: FakeResponse(200, {"choices": []}), "缺字段"),
])
def test_no_key_leak_any_failure(monkeypatch, fake_post_factory, status):
    """所有失败路径统一检查：错误信息里绝不出现假 Key（防线不遗漏）。"""
    monkeypatch.setattr(core.requests, "post", fake_post_factory())
    result = call_llm("你好")
    assert result["ok"] is False
    assert FAKE_KEY not in result["error"], f"路径[{status}]泄露了 Key！"
