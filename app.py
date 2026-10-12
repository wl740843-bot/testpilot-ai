"""app.py：Streamlit 应用入口。

运行方式（在项目根目录、虚拟环境已激活时）：
    streamlit run app.py
浏览器会自动打开 http://localhost:8501
"""
import streamlit as st

# 从我们自己写的 core 模块导入函数
from core import get_greeting

st.set_page_config(page_title="Day 1 骨架")

st.title("Day 1：环境与项目骨架")

name = st.text_input("你的名字", value="世界")
st.write(get_greeting(name))
