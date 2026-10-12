"""core.py：项目的核心逻辑模块。

Day 1 先放一个简单的示例函数，
页面入口（app.py）和测试（tests/test_core.py）都会 import 它，
用来演示"模块如何被调用"。
"""


def get_greeting(name: str = "世界") -> str:
    """根据名字返回一句问候语。

    参数：
        name: 要问候的名字，不传时默认"世界"。

    返回：
        形如 "你好，XX！" 的字符串。
    """
    return f"你好，{name}！"
