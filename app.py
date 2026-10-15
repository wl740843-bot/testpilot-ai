"""app.py：Streamlit 应用入口。

运行方式（在项目根目录、虚拟环境已激活时）：
    streamlit run app.py
浏览器会自动打开 http://localhost:8501
"""
import streamlit as st
import pandas as pd
import openpyxl
from io import BytesIO

from core import generate_cases

APP_MODE = "演示模式"   # 可选："演示模式" / "真实模型"

st.set_page_config(page_title="TestPilot AI 测试助手")

st.title("TestPilot AI 测试助手")
st.caption(f"当前模式：{APP_MODE} —— 固定生成示例用例；接入真实模型后会变为'真实模型'")

# ---------- 输入区 ----------
requirement = st.text_input("请输入需求描述", placeholder="例如：登录功能")

# ---------- 生成按钮：点一下，结果存进"保险箱" ----------
if st.button("生成测试用例"):
    result = generate_cases(requirement)
    if result["ok"]:
        # 成功：用例存进保险箱，并清掉旧错误
        st.session_state["cases"] = result["cases"]
        st.session_state.pop("error", None)
    else:
        # 失败：错误存进保险箱，并清掉旧用例（避免显示上一次的结果）
        st.session_state["error"] = result["error"]
        st.session_state.pop("cases", None)

# ---------- 展示区：保险箱里有就显示，不依赖按钮 ----------
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
