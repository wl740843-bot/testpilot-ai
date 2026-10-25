# TestPilot AI — AI 软件测试助手

输入一段功能需求，自动生成结构化测试用例；支持表格编辑、Excel 导出、pytest 日志分析，并可接入真实大模型（阿里云百炼）生成用例。

面向"全国大学生软件测试大赛"训练 / 求职作品集项目。**演示模式不依赖真实大模型，可离线运行；配置 API Key 后自动切换为真实模型**。

## 功能

| 功能 | 说明 |
|------|------|
| 自动生成测试用例（演示模式） | 输入需求（如"登录功能"），按固定模板生成 3 条用例：正常流程 / 异常输入 / 边界值 |
| 自动生成测试用例（真实模型） | 配置 API Key 后自动调用 qwen 系列模型生成用例；输出经 **JSON 解析 + 字段校验**，不合格自动让模型重写（有限次数） |
| 用例统一结构 | 每条用例含 6 个字段：标题、前置条件、步骤、预期结果、优先级、测试类型 |
| 表格内编辑 | 用例生成后直接在页面表格里修改（Streamlit `data_editor`） |
| 导出 Excel | 一键下载 `.xlsx`，可直接用 Excel / WPS 打开 |
| 日志分析 | 粘贴 pytest 报错日志，规则匹配提取关键词并给出**初步排查建议**（仅供参考，不下结论） |
| 双模式切换 | 页面提供"自动（推荐）/ 强制演示 / 强制真实"三种选择 |

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

不配置 Key 直接启动即可用（演示模式）。

## 配置真实模型（阿里云百炼）

复制 `.env.example` 为 `.env`，填入真实值：

| 字段 | 说明 |
|------|------|
| `DASHSCOPE_API_KEY` | 阿里云百炼 API Key（`sk-` 开头）。获取：登录百炼控制台 → API-KEY 管理 → 创建 |
| `DASHSCOPE_BASE_URL` | API 根地址。通用地址（推荐，无需业务空间 ID）：`https://dashscope.aliyuncs.com/compatible-mode/v1` |
| `DASHSCOPE_MODEL` | 模型名称：`qwen-turbo`（最便宜）/ `qwen-plus`（更聪明） |

**安全约定**：`.env` 已被 `.gitignore` 忽略，绝不会被 git 提交；页面和错误提示均不回显 Key（有专门测试把关）。

## 双模式说明

| | 演示模式 | 真实模型模式 |
|---|---|---|
| 数据来源 | `core.demo_cases()` 固定模板 | `core.generate_cases_with_llm()` 调用真实 API |
| 用例质量 | 模板化，与需求贴合度一般 | 贴合需求，覆盖正常/异常/边界 |
| 成本 | 免费 | 消耗少量 API 费用 |
| 失败处理 | 不会失败（本地生成） | 超时/鉴权/限流/格式错误均有明确提示，不泄露 Key |
| 标识 | 页面顶部明确显示"当前模式：演示模式" | 显示"当前模式：真实模型" |

页面默认"自动"：有 Key 走真实模型，没 Key 走演示模式；也可手动强制指定。

## 运行测试

```bash
python -m pytest -v
```

当前 **53 个单元测试**全部通过：
- `tests/test_core.py`：27 个（演示用例、校验、JSON 解析、生成流水线、日志分析）
- `tests/test_llm_robustness.py`：26 个（异常与边界：超时/网络错误/401/429/5xx/未知状态码、空内容、非法 JSON、超长需求、特殊字符、Key 不泄露、重试机制）

测试默认**不发起真实网络请求**（全部用 monkeypatch 模拟），不消耗 API 费用。

## 项目结构

```
testpilot-ai/
├── app.py                   # Streamlit 页面（只负责展示和调用，不写业务规则）
├── core.py                  # 核心逻辑：demo_cases / validate_cases / parse_json /
│                            #           generate_cases / call_llm /
│                            #           generate_cases_with_llm / analyze_failure
├── eval_run.py              # 批量跑 20 条需求评估集（Day 12）
├── eval_rerun.py            # 改进提示词后重跑样本对比（Day 12）
├── requirements.txt         # 依赖清单
├── .env.example             # 环境变量样例（含字段说明，不放真实密钥）
├── .gitignore               # 忽略 .venv / .env / 缓存等
├── README.md                # 本文件
├── tests/
│   ├── test_core.py         # 核心逻辑测试（27 个）
│   └── test_llm_robustness.py  # 异常与边界测试（26 个）
└── reports/
    ├── evaluation-plan.md   # 20 条需求评估集 + 5 维度评估标准
    ├── evaluation.md        # 评估总结
    ├── eval_outputs.md      # 20 条需求原始输出记录
    └── eval_outputs_v2.md   # 提示词改进后重跑样本对比
```

## 技术栈

- Python / Streamlit / pandas / openpyxl / requests / python-dotenv
- pytest（测试框架）
- Git（版本管理，每天一个提交）

## 开发记录

| 周 | 天 | 内容 | Git 提交 |
|----|----|------|----------|
| 第 1 周 | Day 1 | 环境搭建、项目骨架 | `72b4779` |
| | Day 2 | 演示用例生成 + 6 字段结构 + 校验 | `bc2d7d4` |
| | Day 3 | JSON 解析 + 生成流水线 | `e388ca6` |
| | Day 4 | Streamlit 页面 + Excel 导出 + 状态保持 | `ff75dc2` |
| | Day 5 | 规则型日志分析 | `ed3c084` |
| | Day 6 | 补齐单元测试（27 个全绿） | `d8ee276` |
| | Day 7 | 第一周验收：删无用代码、写 README | `aa7dc6a` |
| 第 2 周 | Day 8 | 阿里百炼 API 调用验证 | `6c9467a` |
| | Day 9 | 封装 call_llm + 接入真实模型 + 三层防线 | `579defc` |
| | Day 10 | 优化提示词 + 自动重试修正 | `c751c57` |
| | Day 11 | 20 条需求评估集 + 5 维度评估标准 | `b35ca28` |
| | Day 12 | 批量评估 20 条需求 + 改进提示词 + 重跑对比 | `5ca9105` |
| | Day 13 | 异常与边界测试（26 个）+ Key 不泄露防线 | `f11e10c` / `7f5c5c9` |
| | Day 14 | 第二周验收：验证双模式 + 更新 README | 今日提交 |

## 当前限制

- **演示数据 ≠ 真实结果**：演示模式是固定模板，页面会明确标识，不会冒充真实 AI 输出。
- **真实模型消耗费用**：评估和日常使用会消耗 API 额度，建议少量调用、记录输入输出避免重复消耗。
- **评估集是人工判断**：Day 11-12 的 5 维度评分是"AI 辅助判卷 + 人工复核"，不是自动化指标。
- **日志分析是规则匹配**：覆盖常见报错关键词；复杂嵌套报错需人工补充 traceback 判断。
- **字段固定 6 个**：真实模型返回超出 6 字段约定会被校验打回，暂不支持用户自定义字段。

---

*第 1 周完成：页面可运行、演示用例可生成、Excel 可导出、常见日志可分析、27 个测试通过。*
*第 2 周完成：接入真实大模型、异常处理与 Key 保护、53 个测试通过、20 条需求评估集与评估记录。*
