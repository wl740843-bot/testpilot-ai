"""api_test.py：Day 8 最小 API 调用测试（阿里百炼 · OpenAI 兼容接口）

用途：先单独验证"能不能调通"，成功后再整合进项目。
运行：在虚拟环境（.venv）中执行  python api_test.py
"""
import os
import requests
from dotenv import load_dotenv

# 1. 读取 .env 里的配置
load_dotenv()
API_KEY = os.getenv("DASHSCOPE_API_KEY", "").strip()
BASE_URL = os.getenv("DASHSCOPE_BASE_URL", "").strip()
MODEL = os.getenv("DASHSCOPE_MODEL", "qwen-plus").strip()

# 2. 安全检查：Key 没填就停，绝不带着假 Key 发请求
if not API_KEY or API_KEY == "your_key_here":
    print("[拦截] .env 里还没有真实的 DASHSCOPE_API_KEY，请先填入再运行。")
    raise SystemExit(1)
if not BASE_URL or "{WorkspaceId}" in BASE_URL:
    print("[拦截] .env 里 BASE_URL 还是占位符，请把 {WorkspaceId} 换成你的业务空间 ID。")
    raise SystemExit(1)

# 3. 组装请求：URL = 根地址 + /chat/completions
url = BASE_URL.rstrip("/") + "/chat/completions"
headers = {
    "Authorization": f"Bearer {API_KEY}",   # 认证：你的 Key
    "Content-Type": "application/json",     # 告诉服务器：我发的是 JSON
}
payload = {
    "model": MODEL,
    "messages": [{"role": "user", "content": "你好，请用一句话介绍你自己。"}],
}

print(f"[发送] URL: {url}")
print(f"[发送] 模型: {MODEL}")
print("[发送] 等待响应（超时 30 秒）...")

try:
    resp = requests.post(url, headers=headers, json=payload, timeout=30)
except requests.exceptions.Timeout:
    print("[失败] 请求超时（30 秒），检查网络或稍后再试。")
    raise SystemExit(1)
except requests.exceptions.ConnectionError:
    print("[失败] 网络连接不上，检查 BASE_URL 拼写和网络。")
    raise SystemExit(1)

# 4. 按状态码分类处理（Day 8 学习重点）
print(f"[响应] HTTP 状态码: {resp.status_code}")

if resp.status_code == 200:
    data = resp.json()
    answer = data["choices"][0]["message"]["content"]
    print("[成功] 模型回复：")
    print(answer)
elif resp.status_code == 401:
    print("[失败] 401 鉴权失败：API Key 无效或写错，检查 .env 里的 Key。")
elif resp.status_code == 429:
    print("[失败] 429 限流：请求太频繁，或模型未开通。")
    print("       先换成 qwen-plus 等高限流模型再试（.env 改 DASHSCOPE_MODEL），仍不行再查是否开通。")
elif resp.status_code >= 500:
    print(f"[失败] {resp.status_code} 服务端错误：百炼服务暂时出问题，稍后再试。")
else:
    print(f"[失败] 未预期状态码 {resp.status_code}，响应内容：{resp.text[:300]}")
