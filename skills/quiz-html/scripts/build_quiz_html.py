#!/usr/bin/env python3
"""
build_quiz_html.py - 把题目 JSON 注入到模板 HTML，生成可独立运行的练习网页。

用法：
    python3 build_quiz_html.py <questions_json> [options]

参数：
    questions_json   题目 JSON 文件路径（必填）
                     格式：题目数组，每题字段见下方"题目字段"

选项：
    --output <path>  输出 HTML 路径（默认：./quiz_<timestamp>.html）
    --title <str>    页面标题（默认："题库练习"）
    --subtitle <str> 副标题（默认根据题量自动生成）
    --id <str>       题库标识 ID（用于 localStorage 隔离，默认时间戳）
    --open           生成后自动用浏览器打开

题目字段（来自 quiz-mastery 的标准 JSON 格式）：
    type            single_choice | true_false | fill_blank | short_answer
    prompt          题干（必填）
    options         选项数组，仅 single_choice 用，格式 ["A. xxx", "B. yyy", ...]
    answer          标准答案
    explanation     解析（推荐填，K12 学生很需要）
    knowledge_point 知识点名（用于侧边栏分组）
    category        分类路径（推荐用"学科 / 子模块"，如"物理 / 电学"）
    level           难度 1-3（可选）
    memory_tip      记忆口诀（可选，会用橙色卡片高亮显示）

退出码：
    0   成功
    1   参数错误 / 文件不存在
    2   JSON 解析失败 / 数据格式不对
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import webbrowser
from pathlib import Path
from typing import Any


SKILL_DIR = Path(__file__).resolve().parent.parent
TEMPLATE_PATH = SKILL_DIR / "templates" / "quiz_template.html"

REQUIRED_FIELDS = {"type", "prompt", "answer"}
VALID_TYPES = {"single_choice", "true_false", "fill_blank", "short_answer"}


def load_questions(path: Path) -> list[dict[str, Any]]:
    """加载题目 JSON，做基本格式校验。"""
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as e:
        print(f"❌ 无法读取文件：{path} - {e}", file=sys.stderr)
        sys.exit(1)

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"❌ JSON 解析失败：{e}", file=sys.stderr)
        sys.exit(2)

    if not isinstance(data, list):
        print(f"❌ 题目必须是数组（list），得到 {type(data).__name__}", file=sys.stderr)
        sys.exit(2)

    if not data:
        print("❌ 题目数组为空", file=sys.stderr)
        sys.exit(2)

    cleaned: list[dict[str, Any]] = []
    for i, q in enumerate(data, 1):
        if not isinstance(q, dict):
            print(f"⚠️ 第 {i} 题不是对象，已跳过", file=sys.stderr)
            continue
        miss = REQUIRED_FIELDS - set(q.keys())
        if miss:
            # 容忍 quiz-mastery 输出里 prompt 写成 question 的旧字段
            if "prompt" in miss and "question" in q:
                q["prompt"] = q["question"]
                miss.discard("prompt")
        if miss:
            print(f"⚠️ 第 {i} 题缺字段 {miss}，已跳过", file=sys.stderr)
            continue
        if q.get("type") not in VALID_TYPES:
            print(f"⚠️ 第 {i} 题 type 非法：{q.get('type')}（应为 {VALID_TYPES}），已跳过", file=sys.stderr)
            continue
        # 单选题校验：options 必须存在
        if q["type"] == "single_choice" and not q.get("options"):
            print(f"⚠️ 第 {i} 题（选择题）缺 options，已跳过", file=sys.stderr)
            continue
        cleaned.append(q)

    if not cleaned:
        print("❌ 没有任何合法题目", file=sys.stderr)
        sys.exit(2)

    return cleaned


def auto_subtitle(questions: list[dict[str, Any]]) -> str:
    """根据题目自动生成副标题：题量 + 涉及分类。"""
    cats = sorted({(q.get("category") or "").strip() for q in questions if q.get("category")})
    type_count: dict[str, int] = {}
    for q in questions:
        t = q.get("type", "?")
        type_count[t] = type_count.get(t, 0) + 1
    type_names = {
        "single_choice": "选择",
        "true_false": "判断",
        "fill_blank": "填空",
        "short_answer": "简答",
    }
    breakdown = " · ".join(f"{type_names.get(t, t)}×{n}" for t, n in type_count.items())
    parts = [f"共 {len(questions)} 题"]
    if breakdown:
        parts.append(breakdown)
    if cats:
        # 提取顶级学科（按 "/" 拆）
        top_cats = sorted({c.split("/")[0].strip() for c in cats if c})
        if top_cats:
            parts.append("、".join(top_cats))
    return " · ".join(parts)


def render(questions: list[dict[str, Any]], title: str, subtitle: str, qid: str) -> str:
    """把题目数据注入模板。"""
    if not TEMPLATE_PATH.exists():
        print(f"❌ 模板文件不存在：{TEMPLATE_PATH}", file=sys.stderr)
        sys.exit(1)

    html = TEMPLATE_PATH.read_text(encoding="utf-8")

    meta = {"id": qid, "title": title, "subtitle": subtitle}
    quiz_json = json.dumps(questions, ensure_ascii=False)
    meta_json = json.dumps(meta, ensure_ascii=False)

    # 顺序替换，避免 title/subtitle 内含 {{...}} 时被二次解释
    html = html.replace("{{TITLE}}", _safe(title))
    html = html.replace("{{SUBTITLE}}", _safe(subtitle))
    html = html.replace("{{QUIZ_DATA}}", quiz_json)
    html = html.replace("{{META}}", meta_json)
    return html


def _safe(s: str) -> str:
    """HTML 安全转义（仅用于 title/subtitle 这种纯文本占位符）。"""
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _slug(s: str) -> str:
    """生成文件名安全的 slug。"""
    s = re.sub(r"[^\w\u4e00-\u9fa5-]+", "_", s).strip("_")
    return s[:40] or "quiz"


def main() -> int:
    ap = argparse.ArgumentParser(
        description="把题目 JSON 注入模板，生成可独立运行的练习网页",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("questions", type=Path, help="题目 JSON 文件路径")
    ap.add_argument("--output", "-o", type=Path, help="输出 HTML 路径")
    ap.add_argument("--title", default="📚 题库练习", help="页面标题")
    ap.add_argument("--subtitle", default=None, help="副标题（默认自动生成）")
    ap.add_argument("--id", dest="qid", default=None, help="题库 ID（用于 localStorage 隔离）")
    ap.add_argument("--open", action="store_true", help="生成后自动用浏览器打开")
    args = ap.parse_args()

    if not args.questions.exists():
        print(f"❌ 文件不存在：{args.questions}", file=sys.stderr)
        return 1

    questions = load_questions(args.questions)
    title = args.title
    subtitle = args.subtitle or auto_subtitle(questions)
    qid = args.qid or f"q_{int(time.time())}"

    html = render(questions, title, subtitle, qid)

    # 输出路径：默认到题目文件同目录
    if args.output:
        output = args.output
    else:
        ts = time.strftime("%Y%m%d_%H%M%S")
        output = args.questions.parent / f"quiz_{_slug(title)}_{ts}.html"

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(html, encoding="utf-8")

    # 输出统一 JSON，方便 agent 解析
    result = {
        "success": True,
        "output_path": str(output.resolve()),
        "question_count": len(questions),
        "title": title,
        "subtitle": subtitle,
        "id": qid,
        "size_bytes": output.stat().st_size,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))

    if args.open:
        webbrowser.open(f"file://{output.resolve()}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
