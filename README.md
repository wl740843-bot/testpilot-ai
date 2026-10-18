# TestPilot AI — AI 软件测试助手

输入一段功能需求，自动生成结构化测试用例；支持表格编辑、Excel 导出和 pytest 日志分析。

面向"全国大学生软件测试大赛"训练项目，第一阶段（第 1 周）为**演示模式**，不依赖真实大模型。

## 功能

| 功能 | 说明 |
|------|------|
| 自动生成测试用例 | 输入需求（如"登录功能"），生成 3 条用例：正常流程 / 异常输入 / 边界值 |
| 用例统一结构 | 每条用例含 6 个字段：标题、前置条件、步骤、预期结果、优先级、测试类型 |
| 表格内编辑 | 用例生成后直接在页面表格里修改（Streamlit `data_editor`） |
| 导出 Excel | 一键下载 `.xlsx`，可直接用 Excel / WPS 打开 |
| 日志分析 | 粘贴 pytest 报错日志，自动提取报错关键词并给出**初步排查建议**（仅供参考，不下结论） |
| 双模式 | 演示模式（内置规则生成）/ 真实模型模式（第二周接入，调用失败时安全降级） |

## 快速开始

```bash
# 1. 创建并激活虚拟环境
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate  # macOS / Linux

# 2. 安装依赖（一次性安装 requirements.txt 里的全部包）
pip install -r requirements.txt

# 3. 启动页面
streamlit run app.py

# 4. 浏览器自动打开 http://localhost:8501
```

## 运行测试

```bash
python -m pytest -v
```

当前 27 个单元测试全部通过。

## 项目结构

```
testpilot-ai/
├── app.py               # Streamlit 页面（只负责展示和调用，不写业务规则）
├── core.py              # 核心逻辑：用例生成、校验、JSON 解析、日志分析
├── requirements.txt     # 依赖清单
├── .env.example         # 环境变量样例（模型模式用）
├── .gitignore           # 忽略 .venv / .env / 缓存等
└── tests/
    └── test_core.py     # core 模块的单元测试
```

## 技术栈

- Python 3.14 / Streamlit / pandas / openpyxl
- pytest（测试框架）
- Git（版本管理，每天一个提交）

## 开发记录（第 1 周）

| 天 | 内容 | Git 提交 |
|----|------|----------|
| Day 1 | 环境搭建、项目骨架 | `72b4779` |
| Day 2 | 演示用例生成 + 6 字段结构 + 校验 | `bc2d7d4` |
| Day 3 | JSON 解析 + 生成流水线 | `e388ca6` |
| Day 4 | Streamlit 页面 + Excel 导出 + 状态保持 | `ff75dc2` |
| Day 5 | 规则型日志分析 | `ed3c084` |
| Day 6 | 补齐单元测试（27 个全绿） | `d8ee276` |
| Day 7 | 第一周验收：删无用代码、写 README | 今日提交 |

## 遗留问题

- 日志分析目前是**规则匹配**（关键词 → 建议对照表），覆盖常见报错；复杂嵌套报错需人工补充 traceback 判断。
- 生成用例为演示模式（固定模板），尚未接入真实大模型——第二周计划接入并增加质量评估。
- 真实模型返回的数据若超出 6 字段约定，校验会打回并提示；暂不支持用户自定义字段。

---

*第一阶段（第 1 周）完成：页面可运行、演示用例可生成、Excel 可导出、常见日志可分析、27 个测试通过、Git 记录完整。*
