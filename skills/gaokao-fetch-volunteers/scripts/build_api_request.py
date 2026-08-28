#!/usr/bin/env python3
"""从 student.json 构建 API 请求体，将考生倾向映射到选填参数。"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

# 意向城市 → API provinces（省份意向）
CITY_TO_PROVINCE: dict[str, str] = {
    "北京": "北京",
    "上海": "上海",
    "天津": "天津",
    "重庆": "重庆",
    "深圳": "广东",
    "广州": "广东",
    "东莞": "广东",
    "佛山": "广东",
    "武汉": "湖北",
    "成都": "四川",
    "杭州": "浙江",
    "宁波": "浙江",
    "南京": "江苏",
    "苏州": "江苏",
    "无锡": "江苏",
    "西安": "陕西",
    "长沙": "湖南",
    "郑州": "河南",
    "济南": "山东",
    "青岛": "山东",
    "合肥": "安徽",
    "厦门": "福建",
    "福州": "福建",
    "大连": "辽宁",
    "沈阳": "辽宁",
    "哈尔滨": "黑龙江",
    "长春": "吉林",
    "昆明": "云南",
    "南宁": "广西",
    "海口": "海南",
    "石家庄": "河北",
    "太原": "山西",
    "南昌": "江西",
    "兰州": "甘肃",
    "贵阳": "贵州",
    "呼和浩特": "内蒙古",
    "乌鲁木齐": "新疆",
    "银川": "宁夏",
    "西宁": "青海",
    "拉萨": "西藏",
}

DEFAULT_API_OPTIONS: dict[str, Any] = {
    "universityNum": 30,
    "majorNum": 6,
    "isAdjust": True,
    "volunteerType": "ACADEMY_GROUP",
    "returnUniversityNum": 30,
    "intentionNum": 0,
}


def _join_csv(values: list[str] | None) -> str | None:
    if not values:
        return None
    cleaned = [str(v).strip() for v in values if str(v).strip()]
    return ",".join(cleaned) if cleaned else None


def cities_to_provinces(cities: list[str] | None) -> list[str]:
    """意向城市去重映射为省份列表。"""
    if not cities:
        return []
    provinces: list[str] = []
    seen: set[str] = set()
    for city in cities:
        key = str(city).strip().replace("市", "").replace("省", "")
        if not key:
            continue
        province = CITY_TO_PROVINCE.get(key, key)
        if province not in seen:
            seen.add(province)
            provinces.append(province)
    return provinces


def student_to_api_payload(student: dict[str, Any]) -> dict[str, Any]:
    """将 student.json 转为 API 请求体。"""
    preferred_provinces = student.get("preferred_provinces") or []
    if not preferred_provinces:
        preferred_provinces = cities_to_provinces(student.get("preferred_cities"))

    payload: dict[str, Any] = {
        "province": student.get("province"),
        "classify": student.get("classify"),
        "subjects": student.get("subjects"),
        "gradeType": student.get("gradeType"),
        "score": student.get("score"),
        "rank": student.get("rank"),
        "batch": student.get("batch"),
        "universitys": _join_csv(student.get("preferred_universities")),
        "provinces": _join_csv(preferred_provinces),
        "tags": _join_csv(student.get("preferred_tags")),
        "majorClass": _join_csv(student.get("preferred_major_classes")),
        **DEFAULT_API_OPTIONS,
    }

    overrides = student.get("api_overrides") or {}
    for key, value in overrides.items():
        if value is not None:
            payload[key] = value

    return payload


def summarize_preferences(student: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    """返回倾向映射摘要，便于 Agent 向用户说明。"""
    return {
        "universitys": payload.get("universitys"),
        "provinces": payload.get("provinces"),
        "tags": payload.get("tags"),
        "majorClass": payload.get("majorClass"),
        "sources": {
            "preferred_universities": student.get("preferred_universities"),
            "preferred_cities": student.get("preferred_cities"),
            "preferred_provinces": student.get("preferred_provinces"),
            "preferred_tags": student.get("preferred_tags"),
            "preferred_major_classes": student.get("preferred_major_classes"),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="从 student.json 构建 API 请求 JSON")
    parser.add_argument("-i", "--input", type=Path, required=True, help="student.json 路径")
    parser.add_argument("-o", "--output", type=Path, required=True, help="输出 api_request.json")
    parser.add_argument(
        "--summary",
        type=Path,
        help="可选：输出倾向映射摘要 JSON（供 Agent 核对）",
    )
    args = parser.parse_args()

    try:
        student = json.loads(args.input.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        print(f"错误: 无法读取 student.json — {e}", file=sys.stderr)
        return 1

    payload = student_to_api_payload(student)
    try:
        from province_config import validate_classify, validate_subjects_for_volunteer_api

        validate_classify(str(payload.get("province", "")), payload.get("classify"))
        validate_subjects_for_volunteer_api(payload)
    except ValueError as e:
        print(f"错误: {e}", file=sys.stderr)
        return 1

    required = ["province", "classify", "score"]
    missing = [k for k in required if not payload.get(k)]
    if missing:
        print(f"错误: student.json 缺少 API 必填字段 {missing}", file=sys.stderr)
        return 1

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"已生成 API 请求: {args.output}")

    if args.summary:
        summary = summarize_preferences(student, payload)
        args.summary.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"已生成倾向映射摘要: {args.summary}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
