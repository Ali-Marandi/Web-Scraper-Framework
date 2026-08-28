#!/usr/bin/env python3
"""
profile_match.py — 把用户技能列表 vs 关键词库做匹配，输出匹配度报告

用法：
    python profile_match.py --skills "SQL,Python,产品规划,A/B测试" \
                            --library internet \
                            [--out report.md]

library 取值：internet / tech / finance / general
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

LIB_MAP = {
    "internet": "keywords_internet.md",
    "tech": "keywords_tech.md",
    "finance": "keywords_finance.md",
    "general": "keywords_general.md",
}


def extract_keywords(md_path: Path) -> list[str]:
    """简单解析 markdown，把所有 bullet 后面的中英文词汇收集起来。"""
    text = md_path.read_text(encoding="utf-8")
    # 匹配 - 开头的行
    bullets = re.findall(r"^\s*[-*]\s+(.+)$", text, flags=re.MULTILINE)
    keywords: set[str] = set()
    for line in bullets:
        # 去掉括号内的解释、占位符、markdown 控制字符
        clean = re.sub(r"[（(][^)）]*[)）]", "", line)
        clean = re.sub(r"_{2,}", "", clean)
        clean = clean.replace("**", "").replace("__", "")
        for token in re.split(r"[、,，/／\s]+", clean):
            token = token.strip().strip("：:。.\"\"''`*").lower()
            # 过滤掉只含标点 / 短横 / 数字 的词
            if not re.search(r"[一-龥A-Za-z]", token):
                continue
            if 1 < len(token) < 30:
                keywords.add(token)
    return sorted(keywords)


def match_score(user_skills: list[str], lib_keywords: list[str]) -> dict:
    """返回匹配命中、缺失、命中率。模糊匹配：包含即算命中。"""
    user_lower = [s.strip().lower() for s in user_skills if s.strip()]
    hits, missing = [], []
    for kw in lib_keywords:
        if any(kw in u or u in kw for u in user_lower):
            hits.append(kw)
        else:
            missing.append(kw)
    rate = len(hits) / len(lib_keywords) if lib_keywords else 0
    return {
        "hits": hits,
        "missing": missing,
        "rate": rate,
        "user_skills": user_lower,
    }


def render_report(result: dict, library: str) -> str:
    rate_pct = f"{result['rate'] * 100:.1f}%"
    # 缺口前 20 个，避免太长
    top_missing = result["missing"][:20]
    lines = [
        f"# 岗位画像匹配报告 — {library}",
        "",
        f"- **命中率**：{rate_pct}（{len(result['hits'])} / {len(result['hits']) + len(result['missing'])}）",
        f"- **用户提供技能**：{', '.join(result['user_skills'])}",
        "",
        "## ✅ 命中的关键词",
        "",
        ", ".join(result["hits"]) if result["hits"] else "（无）",
        "",
        "## ⚠️ 缺口（前 20 个，按字典序）",
        "",
        ", ".join(top_missing) if top_missing else "（无）",
        "",
        "## 解读",
        "",
        "- 命中率 < 20%：方向不匹配，建议重新评估目标岗",
        "- 命中率 20-50%：可投但需要补关键缺口",
        "- 命中率 > 50%：核心匹配，可以重点投",
        "",
        "注意：本工具是关键词级别的粗筛，不能替代真实 JD 对照（用 jd-resume-tailor 做精准对比）。",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skills", required=True, help="用户技能列表，逗号分隔")
    parser.add_argument(
        "--library", choices=list(LIB_MAP), required=True, help="关键词库"
    )
    parser.add_argument("--out", help="输出 markdown 报告路径，缺省直接打印")
    parser.add_argument(
        "--references-dir",
        default=str(Path(__file__).resolve().parent.parent / "references"),
        help="references 目录路径",
    )
    args = parser.parse_args()

    lib_path = Path(args.references_dir) / LIB_MAP[args.library]
    if not lib_path.exists():
        print(f"✗ 找不到关键词库：{lib_path}", file=sys.stderr)
        sys.exit(1)

    lib_keywords = extract_keywords(lib_path)
    user_skills = [s for s in args.skills.split(",") if s.strip()]
    result = match_score(user_skills, lib_keywords)
    report = render_report(result, args.library)

    if args.out:
        Path(args.out).write_text(report, encoding="utf-8")
        print(f"✓ 报告已生成：{args.out}")
    else:
        print(report)


if __name__ == "__main__":
    main()
