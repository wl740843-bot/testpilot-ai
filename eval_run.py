"""eval_run.py：批量跑评估需求，输出存文件供人工判卷（Day 12 用）。

用法（项目根目录、虚拟环境激活时）：
    python eval_run.py

产物：
    reports/eval_outputs.md —— 20 条需求的模型原始输出
"""
import json

from core import generate_cases_with_llm

# ============ ① 考卷清单：20 条需求（与 evaluation-plan.md 保持一致） ============
REQUIREMENTS = [
    "用户登录功能",
    "新用户注册表单校验",
    "商品搜索功能",
    "向购物车添加商品",
    "普通用户不能访问管理后台",
    "上传商品图片",
    "提交订单并结算",
    "用户忘记密码后重置密码",
    "商品详情页展示",
    "订单在线支付",
    "修改个人资料",
    "对已购商品发表评价",
    "领取优惠券",
    "收藏商品",
    "消息通知已读",
    "退出登录",
    "管理收货地址",
    "搜索结果分页浏览",
    "商品多条件筛选",
    "导出订单报表",
]


def main() -> None:
    """主体循环：逐条跑模型，把输出拼成 Markdown 存文件。"""
    lines = []
    ok_count = 0

    for i, req in enumerate(REQUIREMENTS, start=1):
        print(f"[{i}/20] 正在跑：{req} ...", flush=True)
        r = generate_cases_with_llm(req)

        lines.append(f"## R{i:02d}：{req}\n")
        if r["ok"]:
            ok_count += 1
            lines.append(f"**格式通过：是**（{len(r['cases'])} 条用例）\n")
            for j, c in enumerate(r["cases"], 1):
                lines.append(f"### 用例{j} | {c['priority']} | {c['test_type']}")
                lines.append(f"- 标题：{c['title']}")
                lines.append(f"- 前置：{c['preconditions']}")
                lines.append(f"- 步骤：{'；'.join(c['steps'])}")
                lines.append(f"- 预期：{c['expected']}")
                lines.append("")
        else:
            lines.append(f"**格式通过：否**\n\n> {r['error']}\n")

    # ============ ③ 保存输出 ============
    report = (
        "# Day 12 评估：20 条需求模型原始输出\n\n"
        f"格式通过：{ok_count}/{len(REQUIREMENTS)}\n\n"
        + "\n".join(lines)
    )
    with open("reports/eval_outputs.md", "w", encoding="utf-8") as f:
        f.write(report)

    print(f"\n完成：格式通过 {ok_count}/{len(REQUIREMENTS)}，输出已存 reports/eval_outputs.md")


if __name__ == "__main__":
    main()
