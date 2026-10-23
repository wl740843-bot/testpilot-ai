"""eval_rerun.py：改进提示词后重跑样本需求，输出存文件供对比（Day 12 用）。

用法（项目根目录、虚拟环境激活时）：
    python eval_rerun.py

样本：R01（对照组，原判优）+ R03/R05（原判差）+ R04（原判中）
产物：
    reports/eval_outputs_v2.md —— 改进后提示词的样本输出
"""
import json

from core import generate_cases_with_llm

# 样本：编号 + 需求描述（与 evaluation-plan.md 一致）
SAMPLES = [
    ("R01", "用户登录功能"),
    ("R03", "商品搜索功能"),
    ("R04", "向购物车添加商品"),
    ("R05", "普通用户不能访问管理后台"),
]


def main() -> None:
    lines = []
    ok_count = 0

    for i, (rid, req) in enumerate(SAMPLES, start=1):
        print(f"[{i}/{len(SAMPLES)}] 正在跑：{rid} {req} ...", flush=True)
        r = generate_cases_with_llm(req)

        lines.append(f"## {rid}：{req}\n")
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

    report = (
        "# Day 12 提示词改进后重跑（样本对比）\n\n"
        f"样本格式通过：{ok_count}/{len(SAMPLES)}\n\n"
        + "\n".join(lines)
    )
    with open("reports/eval_outputs_v2.md", "w", encoding="utf-8") as f:
        f.write(report)

    print(f"\n完成：格式通过 {ok_count}/{len(SAMPLES)}，输出已存 reports/eval_outputs_v2.md")


if __name__ == "__main__":
    main()
