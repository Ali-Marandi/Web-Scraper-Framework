#!/usr/bin/env python3
"""将解析后的志愿 JSON + 推荐分析套用 HTML 模板，生成可视化报告。"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

SKILL_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_TEMPLATE = SKILL_ROOT / "templates" / "volunteer_report.html"

VOLUNTEER_TYPE_LABELS = {
    "ACADEMY_MAJOR": "院校志愿",
    "ACADEMY_GROUP": "专业组",
    "MAJOR_GROUP": "专业平行志愿",
}

TYPE_CSS = {
    "冲": "chong",
    "稳": "wen",
    "保": "bao",
    "难": "nan",
    "易": "yi",
}

SECTION_ORDER = ["冲", "稳", "保", "易", "难"]
SECTION_TITLE_CLASS = {
    "冲": "title-chong",
    "稳": "title-wen",
    "保": "title-bao",
    "易": "title-wen",
    "难": "title-chong",
}


def format_subjects(subjects: str | None) -> str:
    if not subjects:
        return "—"
    parts = [p.strip() for p in re.split(r"[,，]", subjects) if p.strip()]
    return "·".join(parts) if parts else subjects


def split_tags(tags: str | None, limit: int = 8) -> list[str]:
    if not tags:
        return []
    items = [t.strip() for t in re.split(r"[,，]", tags) if t.strip()]
    return items[:limit]


def build_school_tags(school: dict[str, Any]) -> list[str]:
    tags: list[str] = []
    primary_parts = []
    if school.get("property_name"):
        primary_parts.append(school["property_name"])
    if school.get("university_code"):
        primary_parts.append(f"代码{school['university_code']}")
    if primary_parts:
        tags.append(" · ".join(primary_parts))
    loc_parts = []
    if school.get("province_name"):
        loc_parts.append(school["province_name"])
    if school.get("city_name"):
        loc_parts.append(school["city_name"])
    if loc_parts:
        tags.append("".join(loc_parts))
    tags.extend(split_tags(school.get("tags")))
    return tags


def enrich_major(major: dict, rec_id: str | None = None) -> dict:
    major = dict(major)
    cost = major.get("study_cost")
    if cost and not str(cost).endswith("元"):
        major["study_cost_display"] = f"{cost}元"
    else:
        major["study_cost_display"] = cost or "—"
    major["rec_id"] = rec_id
    return major


def enrich_school(school: dict) -> dict:
    label = school.get("type_label") or ""
    school = dict(school)
    school["type_css"] = TYPE_CSS.get(label, "default")
    school["tag_list"] = build_school_tags(school)
    school["majors"] = [enrich_major(m) for m in school.get("majors") or []]
    school["has_details"] = bool(school.get("score_history") or school.get("majors"))
    return school


def university_group_key(school: dict) -> tuple[str, str]:
    return (school.get("university_name") or "", school.get("university_code") or "")


def collect_probabilities(schools: list[dict]) -> list[int]:
    probs: list[int] = []
    for school in schools:
        if school.get("enroll_probability") is not None:
            probs.append(int(school["enroll_probability"]))
        for major in school.get("majors") or []:
            if major.get("enroll_probability") is not None:
                probs.append(int(major["enroll_probability"]))
    return probs


def format_prob_range(probs: list[int]) -> tuple[int | None, int | None, str | None]:
    if not probs:
        return None, None, None
    low, high = min(probs), max(probs)
    if low == high:
        return low, high, f"{low}%"
    return low, high, f"{low}%–{high}%"


def sort_majors_by_rec(majors: list[dict]) -> list[dict]:
    """推荐专业排在前面，其余保持相对顺序。"""
    return sorted(majors, key=lambda m: (0 if m.get("rec_id") else 1))


def university_rec_rank(uni: dict) -> int:
    """同档位院校排序：推荐学校+推荐专业 > 仅推荐学校 > 其他。"""
    has_school_rec = bool(uni.get("rec_id"))
    has_major_rec = False
    for m in uni.get("flat_majors") or []:
        if m.get("rec_id"):
            has_major_rec = True
            break
    if not has_major_rec:
        for g in uni.get("groups") or []:
            if any(m.get("rec_id") for m in g.get("majors") or []):
                has_major_rec = True
                break
    if has_school_rec and has_major_rec:
        return 0
    if has_school_rec:
        return 1
    return 2


def build_major_group_entry(school: dict, major_rec_map: dict[tuple, str]) -> dict:
    majors = []
    for m in school.get("majors") or []:
        key = (school.get("university_name"), school.get("university_code"), m.get("major_name"), m.get("major_code"))
        rec_id = major_rec_map.get(key)
        majors.append(enrich_major(m, rec_id))
    return {
        "major_group": school.get("major_group") or "",
        "enroll_probability": school.get("enroll_probability"),
        "score_history": school.get("score_history") or [],
        "majors": sort_majors_by_rec(majors),
        "has_content": bool(school.get("score_history") or majors),
    }


def flatten_majors(groups: list[dict]) -> list[dict]:
    majors: list[dict] = []
    for g in groups:
        for m in g.get("majors") or []:
            row = dict(m)
            row["entry_probability"] = g.get("enroll_probability")
            row["entry_score_history"] = g.get("score_history") or []
            majors.append(row)
    return sort_majors_by_rec(majors)


def build_rec_maps(analysis: dict | None) -> tuple[dict[tuple, str], dict[tuple, str], dict[str, dict]]:
    """返回 (school_rec_map, major_rec_map, rec_modals)。"""
    if not analysis:
        return {}, {}, {}

    modals: dict[str, dict] = {}
    school_map: dict[tuple, str] = {}
    major_map: dict[tuple, str] = {}

    for i, s in enumerate(analysis.get("recommended_schools") or []):
        rid = f"school-{i}"
        key = (s.get("university_name"), s.get("university_code"))
        school_map[key] = rid
        modal = s.get("modal") or {}
        modals[rid] = {"title": modal.get("title", ""), "body": modal.get("body", "")}

    for i, m in enumerate(analysis.get("recommended_majors") or []):
        rid = f"major-{i}"
        key = (m.get("university_name"), m.get("university_code"), m.get("major_name"), m.get("major_code"))
        major_map[key] = rid
        modal = m.get("modal") or {}
        modals[rid] = {"title": modal.get("title", ""), "body": modal.get("body", "")}

    return school_map, major_map, modals


def aggregate_universities(schools: list[dict], school_rec_map: dict, major_rec_map: dict) -> list[dict]:
    buckets: dict[tuple[str, str], list[dict]] = {}
    order: list[tuple[str, str]] = []

    for school in schools:
        key = university_group_key(school)
        if key not in buckets:
            buckets[key] = []
            order.append(key)
        buckets[key].append(enrich_school(school))

    aggregated: list[dict] = []
    for display_index, key in enumerate(order, start=1):
        group_schools = sorted(buckets[key], key=lambda s: s.get("index") or 0)
        primary = group_schools[0]
        groups = [build_major_group_entry(s, major_rec_map) for s in group_schools]
        probs = collect_probabilities(group_schools)
        prob_min, prob_max, prob_display = format_prob_range(probs)

        major_groups = [g["major_group"] for g in groups if g["major_group"]]
        has_major_group = len(major_groups) > 0
        if len(major_groups) == 1:
            group_subtitle = f"/ 专业组 {major_groups[0]}"
        elif len(major_groups) > 1:
            group_subtitle = f"/ {len(major_groups)}个专业组"
        else:
            group_subtitle = ""

        flat_majors = flatten_majors(groups) if not has_major_group else []
        uni_key = (primary.get("university_name"), primary.get("university_code"))

        aggregated.append(
            {
                "index": display_index,
                "sort_index": min(s.get("index") or display_index for s in group_schools),
                "university_name": primary.get("university_name") or "",
                "university_code": primary.get("university_code") or "",
                "type_css": primary.get("type_css", "default"),
                "tag_list": primary.get("tag_list") or [],
                "group_subtitle": group_subtitle,
                "group_count": len(groups),
                "prob_min": prob_min,
                "prob_max": prob_max,
                "prob_display": prob_display,
                "groups": groups,
                "has_major_group": has_major_group,
                "flat_majors": flat_majors,
                "flat_major_count": len(flat_majors),
                "has_details": any(g["has_content"] for g in groups),
                "rec_id": school_rec_map.get(uni_key),
            }
        )

    aggregated.sort(key=lambda u: (university_rec_rank(u), u["sort_index"]))
    for i, uni in enumerate(aggregated, start=1):
        uni["index"] = i
    return aggregated


def build_sections(schools_by_type: dict[str, list], school_rec_map: dict, major_rec_map: dict) -> list[dict]:
    sections = []
    seen = set()
    for label in SECTION_ORDER:
        schools = schools_by_type.get(label)
        if not schools:
            continue
        seen.add(label)
        universities = aggregate_universities(schools, school_rec_map, major_rec_map)
        sections.append(
            {
                "label": label,
                "title_class": SECTION_TITLE_CLASS.get(label, ""),
                "count": len(universities),
                "universities": universities,
            }
        )
    for label, schools in schools_by_type.items():
        if label in seen or not schools:
            continue
        universities = aggregate_universities(schools, school_rec_map, major_rec_map)
        sections.append(
            {
                "label": label,
                "title_class": "",
                "count": len(universities),
                "universities": universities,
            }
        )
    return sections


def compute_stat_pcts(stats: dict[str, Any]) -> dict[str, int]:
    total = stats.get("total") or 0
    if total <= 0:
        return {"chong": 0, "wen": 0, "bao": 0}
    return {
        "chong": round((stats.get("chong") or 0) / total * 100),
        "wen": round((stats.get("wen") or 0) / total * 100),
        "bao": round((stats.get("bao") or 0) / total * 100),
    }


def enrich_context(data: dict, analysis: dict | None = None) -> dict:
    profile = data.get("profile") or {}
    stats = data.get("stats") or {}
    schools_by_type = data.get("schools_by_type") or {}

    school_rec_map, major_rec_map, rec_modals = build_rec_maps(analysis)

    score = profile.get("score")
    score_display = f"{score} 分" if score is not None else "—"
    if profile.get("rank"):
        score_display += f" / 位次 {profile['rank']}"

    narrative = (analysis or {}).get("analysis") or {}
    student = (analysis or {}).get("student") or {}

    return {
        "title": "高考志愿智能推荐方案",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "profile": profile,
        "student": student,
        "subjects_display": format_subjects(profile.get("subjects")),
        "score_display": score_display,
        "stats": stats,
        "stat_pcts": compute_stat_pcts(stats),
        "sections": build_sections(schools_by_type, school_rec_map, major_rec_map),
        "volunteer_type_label": VOLUNTEER_TYPE_LABELS.get(
            profile.get("volunteer_type") or "", profile.get("volunteer_type") or "—"
        ),
        "is_adjust_label": "服从" if profile.get("is_adjust") else "不服从",
        "has_analysis": bool(narrative),
        "analysis": narrative,
        "rec_modals_json": json.dumps(rec_modals, ensure_ascii=False),
    }


def render_report(
    data: dict,
    template_path: Path,
    output_path: Path,
    analysis: dict | None = None,
) -> None:
    if not template_path.is_file():
        raise FileNotFoundError(f"模板不存在: {template_path}")

    env = Environment(
        loader=FileSystemLoader(str(template_path.parent)),
        autoescape=select_autoescape(["html", "xml"]),
    )
    template = env.get_template(template_path.name)
    html = template.render(**enrich_context(data, analysis))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="生成志愿推荐 HTML 报告")
    parser.add_argument("-i", "--input", type=Path, required=True, help="fetch_volunteers.py 输出的 JSON")
    parser.add_argument("-o", "--output", type=Path, required=True, help="HTML 输出路径")
    parser.add_argument("-a", "--analysis", type=Path, help="Agent 产出的 analysis.json")
    parser.add_argument(
        "-t",
        "--template",
        type=Path,
        default=DEFAULT_TEMPLATE,
        help=f"Jinja2 模板路径（默认 {DEFAULT_TEMPLATE}）",
    )
    args = parser.parse_args()

    if not args.input.is_file():
        print(f"错误: 输入文件不存在 {args.input}", file=sys.stderr)
        return 1

    try:
        data = json.loads(args.input.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"错误: JSON 解析失败 — {e}", file=sys.stderr)
        return 1

    analysis = None
    if args.analysis:
        if not args.analysis.is_file():
            print(f"错误: 分析文件不存在 {args.analysis}", file=sys.stderr)
            return 1
        try:
            analysis = json.loads(args.analysis.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            print(f"错误: analysis JSON 解析失败 — {e}", file=sys.stderr)
            return 1

    try:
        render_report(data, args.template, args.output, analysis)
    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        return 1

    print(f"已生成 HTML 报告: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
