#!/usr/bin/env python3
"""AIMorningReport 每日晨报生成器。

功能：
  1. 为指定日期在 reports/ 下生成一份带标准板块骨架的 Markdown 报告；
  2. 在 README.md 顶部刷新「今日速览」表与「历史日报」索引（若已存在）；
  3. 打印本次生成的文件清单与使用提示。

用法：
  python3 scripts/generate_report.py                 # 用今天日期
  python3 scripts/generate_report.py --date 2026-10-10
  python3 scripts/generate_report.py --no-readme     # 仅生成 reports 文件

说明：
  本脚本只负责「搭骨架 + 汇总」，真实内容仍需人工或自动化管线填充。
  它不联网、不依赖第三方库，纯标准库实现，便于在 CI 中稳定运行。
"""

from __future__ import annotations

import argparse
import datetime as _dt
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPORTS_DIR = ROOT / "reports"
README_PATH = ROOT / "README.md"

SECTIONS = [
    ("今日头条", "### 1. 今日最重要的单条新闻\n\n（在此填写，附来源链接）\n"),
    ("大模型与产品动态", "- **条目**：一句话 + 来源\n"),
    ("智能体与自动化", "- **条目**：一句话 + 来源\n"),
    ("安全与治理", "- **条目**：一句话 + 来源\n"),
    ("产业与投融资", "- **条目**：一句话 + 来源\n"),
    ("研究与开源", "- **条目**：一句话 + 来源\n"),
    ("机器人 / 硬件", "- **条目**：一句话 + 来源\n"),
    ("一句话快讯", "- 快讯 1\n- 快讯 2\n"),
    ("编辑点评", "> 一句话总结：更便宜、更顺滑如期而至；更可问责，没有。\n"),
]

OVERVIEW_ROWS = [
    ("安全与治理", "待补充"),
    ("大模型", "待补充"),
    ("智能体", "待补充"),
    ("产业投融资", "待补充"),
    ("研究与开源", "待补充"),
    ("机器人 / 硬件", "待补充"),
]


def parse_date(value: str) -> _dt.date:
    return _dt.datetime.strptime(value, "%Y-%m-%d").date()


def build_report_body(date: _dt.date) -> str:
    weekday_cn = "周" + "一二三四五六日"[date.weekday()]
    lines = [
        f"# AI 晨报 · {date.isoformat()}（{weekday_cn}）",
        "",
        "> 归档副本。最新一期见仓库根目录 [README.md](../README.md)。",
        "",
        "## 今日速览",
        "",
        "| 板块 | 今日头条 |",
        "| --- | --- |",
    ]
    for board, headline in OVERVIEW_ROWS:
        lines.append(f"| {board} | {headline} |")
    lines.append("")
    for title, placeholder in SECTIONS:
        lines.append(f"## {title}")
        lines.append("")
        lines.append(placeholder.rstrip())
        lines.append("")
    return "\n".join(lines) + "\n"


def write_report(date: _dt.date) -> Path:
    REPORTS_DIR.mkdir(exist_ok=True)
    path = REPORTS_DIR / f"{date.isoformat()}.md"
    if path.exists():
        print(f"[跳过] 已存在：{path}")
    else:
        path.write_text(build_report_body(date), encoding="utf-8")
        print(f"[生成] 报告文件：{path}")
    return path


def refresh_readme(date: _dt.date) -> None:
    if not README_PATH.exists():
        print("[提示] 未找到 README.md，跳过刷新。")
        return

    text = README_PATH.read_text(encoding="utf-8")

    # 刷新「今日速览」日期徽章
    text = re.sub(
        r"!\[更新日期\]\(https://img\.shields\.io/badge/更新-[^)]*\)",
        f"![更新日期](https://img.shields.io/badge/更新-{date.isoformat().replace('-', '--')}-2ea44f)",
        text,
    )

    # 在「历史日报」表格中插入新行（按日期倒序，去重）
    pattern = re.compile(
        r"(## 历史日报\s*\n\| 日期 \| 链接 \|\n\| --- \| --- \|)(.*?)(\n## |\Z)",
        re.S,
    )

    def repl(m: re.Match) -> str:
        header, rows, tail = m.group(1), m.group(2), m.group(3)
        entries = [f"| {date.isoformat()} | [查看](reports/{date.isoformat()}.md) |"]
        for row in rows.strip().splitlines():
            if date.isoformat() in row:
                continue
            if row.strip():
                entries.append(row.strip())
        entries.sort(reverse=True, key=lambda s: re.search(r"\| (\d{4}-\d{2}-\d{2}) \|", s).group(1))
        return header + "\n" + "\n".join(entries) + tail

    new_text, n = pattern.subn(repl, text)
    if n:
        README_PATH.write_text(new_text, encoding="utf-8")
        print("[刷新] README.md 历史日报索引与新日期徽章已更新。")
    else:
        print("[提示] 未在 README.md 中找到「历史日报」区块，跳过刷新。")


def main() -> None:
    parser = argparse.ArgumentParser(description="生成 AIMorningReport 每日晨报骨架")
    parser.add_argument(
        "--date",
        default=_dt.date.today().isoformat(),
        help="报告日期，格式 YYYY-MM-DD（默认今天）",
    )
    parser.add_argument("--no-readme", action="store_true", help="仅生成 reports 文件，不改动 README.md")
    args = parser.parse_args()

    date = parse_date(args.date)
    print(f"== AIMorningReport 生成器 ==  目标日期：{date.isoformat()}")
    write_report(date)
    if not args.no_readme:
        refresh_readme(date)
    print("完成。请补充各板块真实内容后再提交。")


if __name__ == "__main__":
    main()
