"""app.py：Streamlit 应用入口。

运行方式（在项目根目录、虚拟环境已激活时）：
    streamlit run app.py
浏览器会自动打开 http://localhost:8501
"""
import streamlit as st
import pandas as pd
import openpyxl
import os
from io import BytesIO

from dotenv import load_dotenv
load_dotenv()  # 读取 .env（幂等，core.py 也已加载）

from core import generate_cases, analyze_failure, call_llm

# 模式判定依据：.env 有没有真实 Key（被手动强制时听用户的）
_API_KEY = os.getenv("DASHSCOPE_API_KEY", "").strip()
_HAS_KEY = _API_KEY and _API_KEY != "your_key_here"

# 生成用例的最小可用提示词：把项目的数据结构约定告诉模型，让它别自己瞎编格式。
# Day 10 将系统优化：加入示例输出、场景覆盖要求、多轮修正等。
_LLM_PROMPT_TEMPLATE = """你是软件测试专家。请根据下面的需求生成测试用例，只输出 JSON 数组，不要输出任何其他文字。

每个用例必须是 JSON 对象，包含且仅包含以下 6 个字段：
- title: 用例标题（字符串）
- preconditions: 前置条件（字符串）
- steps: 测试步骤（字符串数组）
- expected: 预期结果（字符串）
- priority: 优先级，只能是 "高"、"中"、"低"
- test_type: 测试类型，只能是 "功能测试"、"异常测试"、"边界测试"

要求覆盖正常、异常、边界三类场景。

需求：
{requirement}
"""

st.set_page_config(page_title="TestPilot AI 测试助手")

# 模式选择：自动（推荐）= 有 Key 走真实模型，没 Key 走演示模式；也可手动强制
_mode_choice = st.sidebar.radio(
    "模型模式",
    ["自动（推荐）", "强制演示模式", "强制真实模型"],
    help="自动：.env 配置了真实 API Key 就用真实模型，否则用演示模式。",
)

if _mode_choice == "自动（推荐）":
    APP_MODE = "真实模型" if _HAS_KEY else "演示模式"
elif _mode_choice == "强制演示模式":
    APP_MODE = "演示模式"
else:
    APP_MODE = "真实模型"

st.title("TestPilot AI 测试助手")
st.caption(
    f"当前模式：{APP_MODE} —— "
    + ("真实调用大模型生成用例" if APP_MODE == "真实模型" else "固定生成示例用例；在 .env 填入 API Key 后自动切换为真实模型")
)

# 模式选择：默认"自动"（按 .env 是否有 Key 判定）；也可以手动指定，比如有 Key 但想用演示模式
_mode_choice = st.radio(
    "模型模式",
    ["自动", "真实模型", "演示模式"],
    index=0,
    horizontal=True,
    help="自动：.env 有真实 API Key 就用真实模型，否则用演示模式。手动：强制使用指定模式。",
)
if _mode_choice != "自动":
    APP_MODE = _mode_choice

# ================= 功能一：生成测试用例 =================
st.subheader("1. 生成测试用例")

requirement = st.text_input("请输入需求描述", placeholder="例如：登录功能")

if st.button("生成测试用例"):
    # 统一先拦空需求：别让空需求白白浪费一次模型调用
    if not requirement or requirement.strip() == "":
        st.session_state["error"] = "需求不能为空，请输入要测试的功能描述。"
        st.session_state.pop("cases", None)
    elif APP_MODE == "真实模型":
        # 真实路线：先问模型 → 拿到 JSON 文本 → 交给解析 + 验卡员
        prompt = _LLM_PROMPT_TEMPLATE.format(requirement=requirement)
        llm = call_llm(prompt)
        if not llm["ok"]:
            # 模型调用失败：显示人话提示，绝不把堆栈抛给用户
            st.session_state["error"] = "模型调用失败：" + llm["error"]
            st.session_state.pop("cases", None)
        else:
            result = generate_cases(requirement, model_text=llm["content"])
            if result["ok"]:
                st.session_state["cases"] = result["cases"]
                st.session_state.pop("error", None)
            else:
                st.session_state["error"] = result["error"]
                st.session_state.pop("cases", None)
    else:
        # 演示路线：填表机直接生成
        result = generate_cases(requirement)
        if result["ok"]:
            st.session_state["cases"] = result["cases"]
            st.session_state.pop("error", None)
        else:
            st.session_state["error"] = result["error"]
            st.session_state.pop("cases", None)

if "cases" in st.session_state:
    st.success(f"已生成 {len(st.session_state['cases'])} 条测试用例（{APP_MODE}）")
    df = pd.DataFrame(st.session_state["cases"])
    edited_df = st.data_editor(df, num_rows="dynamic")

    buffer = BytesIO()
    edited_df.to_excel(buffer, index=False, engine="openpyxl")
    st.download_button(
        label="下载 Excel 用例表",
        data=buffer.getvalue(),
        file_name="test_cases.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
elif "error" in st.session_state:
    st.error(st.session_state["error"])

# ================= 功能二：pytest 日志分析 =================
st.divider()
st.subheader("2. pytest 日志分析")

log_text = st.text_area("粘贴报错日志", placeholder="把 pytest 输出的报错日志贴在这里", height=180)

if st.button("分析日志"):
    # 结果存保险箱：分析后去改别的地方，结果不会消失（昨天的坑，今天直接用对）
    analysis = analyze_failure(log_text)
    st.session_state["analysis"] = analysis

if "analysis" in st.session_state:
    a = st.session_state["analysis"]
    if a["ok"]:
        st.write("**发现线索：**")
        for c in a["clues"]:
            st.write(f"- {c}")
        st.write("**排查建议：**")
        for s in a["suggestions"]:
            st.write(f"- {s}")
        # 文案红线：只说初步建议，不下结论
        st.caption("以上为初步排查建议，仅供参考，不构成已确认的故障原因。")
    else:
        st.error(a["error"])
