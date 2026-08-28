#!/usr/bin/env python3
"""
jd_gap.py — 把 parse_jd.py 的 JSON 与简历文本做 gap 分析

用法：
    python jd_gap.py --jd jd_parsed.json --resume resume.md --out gap.md

输出 markdown 报告：完美命中 / 隐性命中 / 真缺口 三类，附改写建议。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def load_resume_text(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in {".md", ".txt"}:
        return path.read_text(encoding="utf-8")
    if suffix == ".docx":
        try:
            from docx import Document
        except ImportError:
            print(
                "✗ 缺少 python-docx：pip install python-docx --break-system-packages",
                file=sys.stderr,
            )
            sys.exit(1)
        doc = Document(str(path))
        return "\n".join(p.text for p in doc.paragraphs)
    print(f"✗ 暂不支持的格式：{suffix}", file=sys.stderr)
    sys.exit(1)


def find_evidence(resume_text: str, keyword: str, window: int = 30) -> str | None:
    """在简历里找关键词，返回上下文片段；找不到返回 None。"""
    pattern = re.escape(keyword)
    m = re.search(pattern, resume_text, flags=re.IGNORECASE)
    if not m:
        return None
    start = max(0, m.start() - window)
    end = min(len(resume_text), m.end() + window)
    snippet = resume_text[start:end].replace("\n", " ").strip()
    return snippet


def fuzzy_hit(resume_text: str, keyword: str) -> str | None:
    """模糊命中：取关键词的中文 / 英文核心，做包含匹配。"""
    # 拿前 2 个字 / 前 5 个字符
    candidates = []
    if re.search(r"[一-龥]", keyword):
        if len(keyword) >= 4:
            candidates.append(keyword[:2])
            candidates.append(keyword[-2:])
    else:
        if len(keyword) >= 4:
            candidates.append(keyword[:4].lower())
    text_low = resume_text.lower()
    for c in candidates:
        if c and c in text_low:
            return c
    return None


def analyze(jd: dict, resume_text: str) -> dict:
    perfect, implicit, missing = [], [], []

    # 用 must_have 句子里抽出来的 skills 作为对比项
    candidates = jd.get("skills_extracted", []) + jd.get("must_have", [])

    seen = set()
    for c in candidates:
        # 句子层面太长，截短
        keyword = c.strip()
        if len(keyword) > 30:
            # 从长句子里抽更短的关键词
            short_tokens = re.findall(
                r"[A-Za-z][A-Za-z0-9+/.\-_]{1,20}|[一-龥]{2,6}",
                keyword,
            )
            for t in short_tokens:
                if t.lower() not in seen:
                    seen.add(t.lower())
                    process_one(t, resume_text, perfect, implicit, missing)
        else:
            if keyword.lower() not in seen:
                seen.add(keyword.lower())
                process_one(keyword, resume_text, perfect, implicit, missing)

    return {"perfect": perfect, "implicit": implicit, "missing": missing}


def process_one(keyword, resume_text, perfect, implicit, missing):
    ev = find_evidence(resume_text, keyword)
    if ev:
        perfect.append({"keyword": keyword, "evidence": ev})
        return
    fuzzy = fuzzy_hit(resume_text, keyword)
    if fuzzy:
        implicit.append({"keyword": keyword, "fuzzy_match": fuzzy})
    else:
        missing.append(keyword)


def render(jd: dict, gap: dict) -> str:
    lines = ["# JD ⇄ Resume Gap 分析报告", ""]

    spec = jd.get("special_requirements", {})
    if spec:
        lines += ["## JD 硬条件", ""]
        for k, v in spec.items():
            lines.append(f"- **{k}**：{v}")
        lines.append("")

    lines += ["## ✅ 完美命中（简历里有明确证据）", ""]
    if gap["perfect"]:
        for item in gap["perfect"][:30]:
            lines.append(f"- **{item['keyword']}** —— 证据：`...{item['evidence']}...`")
    else:
        lines.append("（无）")
    lines.append("")

    lines += ["## 🟡 隐性命中（简历里有近似但用词不同，建议改写时对齐）", ""]
    if gap["implicit"]:
        for item in gap["implicit"][:20]:
            lines.append(f"- **JD 关键词：{item['keyword']}**（简历里出现：`{item['fuzzy_match']}`）")
    else:
        lines.append("（无）")
    lines.append("")

    lines += ["## 🔴 真缺口（简历完全没有，需要确认 / 补充 / 转换叙事）", ""]
    if gap["missing"]:
        for kw in gap["missing"][:30]:
            lines.append(f"- **{kw}**")
    else:
        lines.append("（无）")
    lines.append("")

    lines += [
        "---",
        "## 改写建议",
        "",
        "1. **完美命中** 的部分保留，但确保措辞与 JD 一致（比如 JD 用『A/B 测试』就别写『AB 实验』）",
        "2. **隐性命中** 是性价比最高的优化点 —— 把简历里的近义词改成 JD 的措辞",
        "3. **真缺口** 分两类：",
        "   - 你做过但没写？→ 补到对应经历的 bullet 里",
        "   - 你没做过？→ **不要编造**。可以在 cover letter / Summary 里诚实说明 transferable skill",
        "4. 把改后的简历再跑一次 ats_check.py 看命中率是否提升",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--jd", required=True, help="parse_jd.py 输出的 json")
    parser.add_argument("--resume", required=True, help="简历文件 (.md/.txt/.docx)")
    parser.add_argument("--out", help="输出 markdown 路径")
    args = parser.parse_args()

    jd = json.loads(Path(args.jd).read_text(encoding="utf-8"))
    resume_text = load_resume_text(Path(args.resume))
    gap = analyze(jd, resume_text)
    report = render(jd, gap)

    if args.out:
        Path(args.out).write_text(report, encoding="utf-8")
        print(f"✓ Gap 报告已生成：{args.out}")
    else:
        print(report)


if __name__ == "__main__":
    main()
