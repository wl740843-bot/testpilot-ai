"""app.py：Streamlit 应用入口。

运行方式（在项目根目录、虚拟环境已激活时）：
    streamlit run app.py
浏览器会自动打开 http://localhost:8501
"""
import streamlit as st
import pandas as pd
import openpyxl
from io import BytesIO

from core import generate_cases, analyze_failure

APP_MODE = "演示模式"   # 可选："演示模式" / "真实模型"

st.set_page_config(page_title="TestPilot AI 测试助手")

st.title("TestPilot AI 测试助手")
st.caption(f"当前模式：{APP_MODE} —— 固定生成示例用例；接入真实模型后会变为'真实模型'")

# ================= 功能一：生成测试用例 =================
st.subheader("1. 生成测试用例")

requirement = st.text_input("请输入需求描述", placeholder="例如：登录功能")

if st.button("生成测试用例"):
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
