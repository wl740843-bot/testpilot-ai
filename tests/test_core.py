"""test_core.py：core 模块的单元测试。

小技巧：为了让 pytest 无论从哪个目录运行都能找到 core.py，
先把"项目根目录"（本文件所在的上一级）加进模块搜索路径 sys.path。
"""
import sys
from pathlib import Path

# 把项目根目录加入模块搜索路径
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core import get_greeting


def test_get_greeting_with_name():
    """传入名字时，返回对应的问候语。"""
    assert get_greeting("小明") == "你好，小明！"


def test_get_greeting_default():
    """不传参数时，使用默认值"世界"。"""
    assert get_greeting() == "你好，世界！"
