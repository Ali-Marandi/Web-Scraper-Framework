#!/usr/bin/env python3
"""调用智能推荐志愿表 API，解析响应并输出结构化 JSON。"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from province_config import (
    PROVINCES_REQUIRING_GRADE_TYPE,
    batch_list_query_params,
    sanitize_payload_for_api,
    validate_classify,
    validate_subjects_for_volunteer_api,
)

# ========== 接口配置（修改此处即可切换环境）==========
BASE_URL = "https://publicapi.chatglm.cn/chatglm_public/skill"
API_PATH = "/zp/volunteer/intelligenceVolunteer"
BATCH_LIST_PATH = "/zp/volunteer/batch/list"
# =====================================================

TYPE_LABELS = {
    "CHONG": "冲",
    "WEN": "稳",
    "BAO": "保",
    "NAN": "难",
    "YI": "易",
}

PROVINCE_BATCH_FALLBACK: dict[str, str] = {
    "天津": "本科批A段",
    "浙江": "普通类一段",
    "山东": "普通类一段",
    "四川": "本科批B段",
    "云南": "本科批B段",
    "甘肃": "本科批",
    "宁夏": "本科批B段",
    "新疆": "本科一批",
}


def resolve_batch_fallback(province: str | None, batch: str | None) -> str | None:
    """批次 API 失败时的省份静态兜底。"""
    if not province:
        return batch
    mapped = PROVINCE_BATCH_FALLBACK.get(province)
    if not mapped:
        return batch
    if batch is None:
        return mapped
    if str(batch).strip() == "本科批":
        return mapped
    return batch


def batch_list_url(
    params: dict[str, Any],
    base_url: str | None = None,
) -> str:
    root = (base_url or BASE_URL).rstrip("/")
    path = BATCH_LIST_PATH if BATCH_LIST_PATH.startswith("/") else f"/{BATCH_LIST_PATH}"
    query = urlencode(params)
    return f"{root}{path}?{query}"


def call_batch_list_api(
    params: dict[str, Any],
    base_url: str | None = None,
    timeout: int = 60,
) -> list[dict[str, Any]]:
    """GET 批次列表，返回 result 数组。"""
    url = batch_list_url(params, base_url)
    req = Request(url, method="GET", headers={"Accept": "*/*"})
    try:
        with urlopen(req, timeout=timeout) as resp:
            charset = resp.headers.get_content_charset() or "utf-8"
            text = resp.read().decode(charset)
    except HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"批次接口 HTTP {e.code}: {detail}") from e
    except URLError as e:
        raise RuntimeError(f"批次接口网络失败: {e.reason}") from e

    raw = json.loads(text)
    if raw.get("status") != 0:
        raise ValueError(f"批次接口异常: status={raw.get('status')}, message={raw.get('message')}")
    result = raw.get("result")
    if not isinstance(result, list):
        raise ValueError("批次接口返回格式异常：result 非数组")
    if not result:
        province = params.get("province")
        classify = params.get("classify")
        grade_type = params.get("gradeType")
        hint = f"classify={classify}"
        if grade_type:
            hint += f", gradeType={grade_type}"
        raise ValueError(
            f"批次列表为空（{province}，{hint}）。"
            f"请确认 classify 与省份选科模式一致（见 reference.md）"
        )
    return result


def select_batch_from_list(
    items: list[dict[str, Any]],
    user_score: int,
    preferred_batch: str | None = None,
    grade_type: str | None = None,
) -> dict[str, Any]:
    """从批次列表中选取与分数、层次最匹配的一项。"""
    if not items:
        raise ValueError("没有可填报的批次")

    candidates = list(items)

    # 1. 精确批次名（非泛称「本科批」）
    if preferred_batch and preferred_batch.strip() not in ("本科批", "专科批"):
        exact = [x for x in candidates if x.get("batch") == preferred_batch]
        if exact:
            return exact[0]

    # 2. 按 gradeType / 泛称本科批·专科批 过滤
    if grade_type:
        filtered = [x for x in candidates if x.get("gradeType") == grade_type]
        if filtered:
            candidates = filtered
    elif preferred_batch == "本科批":
        filtered = [x for x in candidates if x.get("gradeType") == "本科"]
        if filtered:
            candidates = filtered
    elif preferred_batch == "专科批":
        filtered = [x for x in candidates if x.get("gradeType") == "专科"]
        if filtered:
            candidates = filtered

    # 3. 分数达线：取控制线下考生分数仍达标的批次中，控制线最高者（偏本科一段）
    qualified = [x for x in candidates if user_score >= int(x.get("score") or 0)]
    pool = qualified if qualified else candidates
    return max(pool, key=lambda x: int(x.get("score") or 0))


def apply_batch_item_to_payload(payload: dict[str, Any], batch_item: dict[str, Any]) -> None:
    """将选中批次写入志愿请求体。"""
    payload["batch"] = batch_item.get("batch")
    if batch_item.get("type"):
        payload["volunteerType"] = batch_item["type"]
    province = payload.get("province")
    if (
        province in PROVINCES_REQUIRING_GRADE_TYPE
        and batch_item.get("gradeType")
        and not payload.get("gradeType")
    ):
        payload["gradeType"] = batch_item["gradeType"]


def resolve_batch_via_api(
    payload: dict[str, Any],
    base_url: str | None = None,
) -> tuple[str, dict[str, Any], list[dict[str, Any]]]:
    """调用批次接口并选定 batch，返回 (batch名, 选中项, 全部项)。"""
    params = batch_list_query_params(payload)
    items = call_batch_list_api(params, base_url=base_url)
    selected = select_batch_from_list(
        items,
        user_score=int(payload["score"]),
        preferred_batch=payload.get("batch"),
        grade_type=payload.get("gradeType"),
    )
    apply_batch_item_to_payload(payload, selected)
    return selected.get("batch") or "", selected, items


def _parse_json_field(value: Any) -> Any:
    if value is None or value == "":
        return None
    if isinstance(value, (dict, list)):
        return value
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return value
    return value


def parse_score_history(score_str: Any) -> list[dict[str, str]]:
    """将 score / parityScore 字段解析为 [{year, score, rank, plan_num}, ...]。"""
    parsed = _parse_json_field(score_str)
    if not isinstance(parsed, list):
        return []

    rows: list[dict[str, str]] = []
    for item in parsed:
        if not isinstance(item, dict):
            continue
        for year, triple in item.items():
            parts = str(triple).split(",")
            rows.append(
                {
                    "year": str(year),
                    "score": parts[0] if len(parts) > 0 else "-",
                    "rank": parts[1] if len(parts) > 1 else "-",
                    "plan_num": parts[2] if len(parts) > 2 else "-",
                }
            )
    return rows


def parse_parity_scores(parity_str: Any) -> list[dict[str, str]]:
    parsed = _parse_json_field(parity_str)
    if not isinstance(parsed, list):
        return []
    rows: list[dict[str, str]] = []
    for item in parsed:
        if isinstance(item, dict):
            for year, score in item.items():
                rows.append({"year": str(year), "score": str(score)})
    return rows


def normalize_major(major: dict[str, Any]) -> dict[str, Any]:
    type_code = major.get("type") or ""
    return {
        "major_name": major.get("majorName") or "",
        "major_code": major.get("majorCode") or "",
        "major_num": major.get("majorNum"),
        "claim": major.get("claim") or "",
        "study_year": major.get("studyYear") or "",
        "study_cost": major.get("studyCost") or "",
        "major_class": major.get("majorClass") or "",
        "major_remarks": major.get("majorRemarks") or "",
        "plan_num": major.get("planNum"),
        "enroll_probability": major.get("enrollProbability"),
        "type": type_code,
        "type_label": TYPE_LABELS.get(type_code, type_code or "—"),
        "score_history": parse_score_history(major.get("score")),
        "parity_scores": parse_parity_scores(major.get("parityScore")),
    }


def normalize_school(school: dict[str, Any], index: int) -> dict[str, Any]:
    type_code = school.get("type") or ""
    majors = school.get("majorList") or []
    return {
        "index": index,
        "university_name": school.get("universityName") or "",
        "university_code": school.get("universityCode") or "",
        "major_group": school.get("universityMajorGroup") or "",
        "logo": school.get("logo") or "",
        "category_name": school.get("categoryName") or "",
        "property_name": school.get("propertyName") or "",
        "tags": school.get("tags") or "",
        "city_name": school.get("cityName") or "",
        "province_name": school.get("provinceName") or "",
        "enroll_probability": school.get("enrollProbability"),
        "lowest_score": school.get("lowestScore"),
        "type": type_code,
        "type_label": TYPE_LABELS.get(type_code, type_code or "—"),
        "plan_num": school.get("planNum"),
        "level": school.get("level") or "",
        "is_adjust": school.get("isAdjust"),
        "score_history": parse_score_history(school.get("score")),
        "parity_scores": parse_parity_scores(school.get("parityScore")),
        "majors": [normalize_major(m) for m in majors],
    }


def group_schools_by_type(schools: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    order = ["CHONG", "WEN", "BAO", "YI", "NAN"]
    grouped: dict[str, list[dict[str, Any]]] = {k: [] for k in order}
    other: list[dict[str, Any]] = []
    for school in schools:
        t = school.get("type") or ""
        if t in grouped:
            grouped[t].append(school)
        else:
            other.append(school)
    if other:
        grouped["_OTHER"] = other
    return grouped


def normalize_api_response(raw: dict[str, Any]) -> dict[str, Any]:
    """兼容新旧两种响应信封：{code,msg,body} 与 {status,message,result}。"""
    if "result" in raw and "status" in raw:
        status = raw.get("status")
        msg = raw.get("message") or ""
        if status != 0:
            raise ValueError(f"API 返回异常: status={status}, message={msg}")
        return {"code": 200, "msg": msg or "OK", "body": raw.get("result") or {}}
    return raw


def _empty_to_none(value: Any) -> Any:
    if value == "" or value is None:
        return None
    return value


def parse_api_response(raw: dict[str, Any]) -> dict[str, Any]:
    raw = normalize_api_response(raw)
    code = raw.get("code")
    msg = raw.get("msg") or ""
    if code != 200:
        raise ValueError(f"API 返回异常: code={code}, msg={msg}")

    body = raw.get("body") or {}
    schools_raw = body.get("schoolList") or []
    schools = [normalize_school(s, i + 1) for i, s in enumerate(schools_raw)]
    grouped = group_schools_by_type(schools)

    stats = {
        "total": len(schools),
        "chong": len(grouped.get("CHONG", [])),
        "wen": len(grouped.get("WEN", [])),
        "bao": len(grouped.get("BAO", [])),
    }

    return {
        "meta": {
            "generated_from": "intelligenceVolunteer",
            "api_code": code,
            "api_msg": msg,
        },
        "profile": {
            "province": body.get("province"),
            "classify": body.get("classify"),
            "subjects": _empty_to_none(body.get("subjects")),
            "grade_type": _empty_to_none(body.get("gradeType")),
            "score": body.get("score"),
            "rank": body.get("rank"),
            "batch": body.get("batch"),
            "volunteer_type": body.get("volunteerType"),
            "is_adjust": body.get("isAdjust"),
            "university_num": body.get("universityNum"),
            "major_num": body.get("majorNum"),
            "universitys": body.get("universitys"),
            "provinces": body.get("provinces"),
            "tags": body.get("tags"),
            "major_class": body.get("majorClass"),
        },
        "stats": stats,
        "schools": schools,
        "schools_by_type": {
            TYPE_LABELS.get(k, k): grouped[k]
            for k in grouped
            if grouped[k] and not k.startswith("_")
        },
        "raw_body": body,
    }


def load_payload_from_student(student_path: Path) -> dict[str, Any]:
    from build_api_request import student_to_api_payload

    student = json.loads(student_path.read_text(encoding="utf-8"))
    return student_to_api_payload(student)


def build_request_payload(args: argparse.Namespace) -> dict[str, Any]:
    if args.student:
        return load_payload_from_student(args.student)
    if args.config:
        with open(args.config, encoding="utf-8") as f:
            return json.load(f)

    payload: dict[str, Any] = {
        "province": args.province,
        "classify": args.classify,
        "subjects": args.subjects,
        "gradeType": args.grade_type,
        "score": args.score,
        "rank": args.rank,
        "batch": args.batch,
        "universitys": args.universitys,
        "provinces": args.provinces,
        "tags": args.tags,
        "majorClass": args.major_class,
        "universityNum": args.university_num,
        "majorNum": args.major_num,
        "isAdjust": args.is_adjust,
        "volunteerType": args.volunteer_type,
        "returnUniversityNum": args.return_university_num,
        "intentionNum": args.intention_num,
    }
    return payload


def api_url(base_url: str | None = None) -> str:
    root = (base_url or BASE_URL).rstrip("/")
    path = API_PATH if API_PATH.startswith("/") else f"/{API_PATH}"
    return root + path


def call_api(
    payload: dict[str, Any],
    base_url: str | None = None,
    timeout: int = 60,
) -> dict[str, Any]:
    url = api_url(base_url)
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = Request(
        url,
        data=data,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Accept": "*/*",
        },
    )
    try:
        with urlopen(req, timeout=timeout) as resp:
            charset = resp.headers.get_content_charset() or "utf-8"
            text = resp.read().decode(charset)
    except HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {e.code}: {detail}") from e
    except URLError as e:
        raise RuntimeError(f"网络请求失败: {e.reason}") from e

    return json.loads(text)


def main() -> int:
    parser = argparse.ArgumentParser(description="获取并解析智能推荐志愿表")
    parser.add_argument(
        "--student",
        type=Path,
        help="student.json 路径（自动映射倾向到 API 选填参数，优先于 --config）",
    )
    parser.add_argument(
        "--config",
        type=Path,
        help="完整请求 JSON 文件路径",
    )
    parser.add_argument(
        "--base-url",
        default=os.environ.get("ZP_API_BASE_URL", BASE_URL),
        help=f"API 根地址（默认脚本内 BASE_URL: {BASE_URL}）",
    )
    parser.add_argument("-o", "--output", type=Path, required=True, help="解析结果 JSON 输出路径")
    parser.add_argument("--save-raw", type=Path, help="可选：保存 API 原始响应")

    parser.add_argument("--province", help="高考省份")
    parser.add_argument("--classify", help="选科模式：文科/理科/物理/历史/综合")
    parser.add_argument("--subjects", help="选科组合，逗号分隔，如 物理,化学,生物")
    parser.add_argument("--grade-type", dest="grade_type", help="成绩类型：本科/专科（京沪津专科批）")
    parser.add_argument("--score", type=int, help="高考成绩")
    parser.add_argument("--rank", type=int, help="高考位次")
    parser.add_argument("--batch", help="填报批次，如 本科批")
    parser.add_argument(
        "--auto-batch",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="是否通过 batch/list 接口自动解析批次（默认开启）",
    )
    parser.add_argument("--universitys", help="心仪高校，逗号分隔")
    parser.add_argument("--provinces", help="省份意向，逗号分隔")
    parser.add_argument("--tags", help="院校属性意向，逗号分隔")
    parser.add_argument("--major-class", dest="major_class", help="专业类意向，逗号分隔")
    parser.add_argument("--university-num", type=int, default=30)
    parser.add_argument("--major-num", type=int, default=6)
    parser.add_argument(
        "--is-adjust",
        action=argparse.BooleanOptionalAction,
        default=True,
    )
    parser.add_argument("--volunteer-type", default="ACADEMY_GROUP")
    parser.add_argument("--return-university-num", type=int, default=30)
    parser.add_argument("--intention-num", type=int, default=0)

    args = parser.parse_args()

    try:
        payload = build_request_payload(args)
    except (OSError, json.JSONDecodeError) as e:
        print(f"错误: 无法读取请求配置 — {e}", file=sys.stderr)
        return 1

    if not args.student and not args.config:
        required = ["province", "classify", "score"]
        if not args.auto_batch:
            required.append("batch")
        missing = [k for k in required if payload.get(k) is None]
        if missing:
            print(
                f"错误: 缺少必填参数 {missing}，请使用 --student、--config 或补全命令行",
                file=sys.stderr,
            )
            return 1

    # CLI 中 null 用字符串 "null" 传入时转为 None（subjects 在 sanitize 阶段按省处理）
    for key in ("gradeType", "rank", "universitys", "provinces", "tags", "majorClass"):
        if payload.get(key) == "null":
            payload[key] = None

    try:
        validate_classify(str(payload.get("province", "")), payload.get("classify"))
    except ValueError as e:
        print(f"错误: {e}", file=sys.stderr)
        return 1

    batch_resolution: dict[str, Any] | None = None
    if args.auto_batch:
        try:
            batch_name, selected, all_items = resolve_batch_via_api(payload, base_url=args.base_url)
            batch_resolution = {
                "source": "batch/list",
                "selected": selected,
                "available": all_items,
            }
            print(
                f"批次: {batch_name}（{selected.get('gradeType', '')} / {selected.get('type', '')}）",
                file=sys.stderr,
            )
        except (RuntimeError, ValueError, json.JSONDecodeError) as e:
            print(f"警告: 批次接口失败，使用静态兜底 — {e}", file=sys.stderr)
            payload["batch"] = resolve_batch_fallback(payload.get("province"), payload.get("batch"))
            batch_resolution = {"source": "fallback", "batch": payload.get("batch")}
    elif not payload.get("batch"):
        print("错误: 已关闭 --auto-batch 且未提供 batch", file=sys.stderr)
        return 1

    sanitize_payload_for_api(payload)
    try:
        validate_subjects_for_volunteer_api(payload)
    except ValueError as e:
        print(f"错误: {e}", file=sys.stderr)
        return 1

    print(f"请求: {api_url(args.base_url)}", file=sys.stderr)
    try:
        raw = call_api(payload, base_url=args.base_url)
    except (RuntimeError, json.JSONDecodeError) as e:
        print(f"错误: {e}", file=sys.stderr)
        return 1

    if args.save_raw:
        args.save_raw.parent.mkdir(parents=True, exist_ok=True)
        args.save_raw.write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8")

    try:
        parsed = parse_api_response(raw)
    except ValueError as e:
        print(f"错误: {e}", file=sys.stderr)
        return 1

    parsed["request"] = payload
    if batch_resolution:
        parsed["batch_resolution"] = batch_resolution
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(parsed, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"已保存解析结果: {args.output}（共 {parsed['stats']['total']} 所院校）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
