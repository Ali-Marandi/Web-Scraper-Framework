#!/usr/bin/env python3
"""各省高考模式、classify 校验与 API 参数规范化。"""

from __future__ import annotations

from typing import Any

# 仅京沪津批次接口与志愿接口需要 gradeType
PROVINCES_REQUIRING_GRADE_TYPE = frozenset({"北京", "上海", "天津"})

# 测试环境批次接口暂不支持
UNSUPPORTED_PROVINCES = frozenset({"西藏"})

MODE_33 = frozenset({"上海", "北京", "天津", "山东", "浙江", "海南"})
MODE_312 = frozenset({
    "广东", "江苏", "河北", "湖北", "湖南", "福建", "辽宁", "重庆", "甘肃",
    "黑龙江", "吉林", "安徽", "江西", "贵州", "广西", "云南", "内蒙古",
    "四川", "宁夏", "山西", "河南", "陕西", "青海",
})
MODE_OLD = frozenset({"新疆"})

VALID_CLASSIFY_BY_MODE: dict[str, frozenset[str]] = {
    "33": frozenset({"综合"}),
    "312": frozenset({"物理", "历史"}),
    "老高考": frozenset({"文科", "理科"}),
}

MODE_LABELS: dict[str, str] = {
    "33": "3+3",
    "312": "3+1+2",
    "老高考": "老高考",
}

SUBJECTS_312_ELECTIVES = frozenset({"化学", "生物", "政治", "地理"})
SUBJECTS_33_POOL = frozenset({"物理", "历史", "化学", "生物", "政治", "地理"})
SUBJECTS_33_ZHEJIANG = SUBJECTS_33_POOL | frozenset({"技术"})


def parse_subjects_list(subjects: Any) -> list[str]:
    if subjects in (None, "", "null", "NULL"):
        return []
    return [s.strip() for s in str(subjects).split(",") if s.strip()]


def get_province_mode(province: str | None) -> str:
    if not province:
        return "unknown"
    if province in UNSUPPORTED_PROVINCES:
        return "unsupported"
    if province in MODE_OLD:
        return "老高考"
    if province in MODE_33:
        return "33"
    if province in MODE_312:
        return "312"
    return "unknown"


def validate_classify(province: str, classify: str | None) -> None:
    """校验 classify 是否与省份选科模式匹配。"""
    mode = get_province_mode(province)
    if mode == "unsupported":
        raise ValueError(
            f"省份 {province} 在测试环境暂不支持志愿/批次接口（平台未接入该省数据）"
        )
    if mode == "unknown":
        return
    if not classify:
        valid = VALID_CLASSIFY_BY_MODE[mode]
        raise ValueError(
            f"缺少 classify：{province} 为{MODE_LABELS[mode]}模式，应填 {'/'.join(sorted(valid))}"
        )
    valid = VALID_CLASSIFY_BY_MODE[mode]
    if classify not in valid:
        raise ValueError(
            f"classify 与省份不匹配：{province} 为{MODE_LABELS[mode]}模式，"
            f"classify 应为 {'/'.join(sorted(valid))}，当前为 {classify!r}。"
            f"错误 classify 会导致批次接口返回空列表。"
        )


def infer_grade_type(
    province: str | None,
    score: int | None,
    explicit: str | None = None,
    batch_pref: str | None = None,
) -> str | None:
    """京沪津推断本科/专科；其他省份返回 None。"""
    if province not in PROVINCES_REQUIRING_GRADE_TYPE:
        return None
    if explicit in ("本科", "专科"):
        return explicit
    if batch_pref == "专科批":
        return "专科"
    if batch_pref == "本科批":
        return "本科"
    if score is not None and score <= 450:
        return "专科"
    return "本科"


def batch_list_query_params(payload: dict[str, Any]) -> dict[str, Any]:
    """从请求体构建 batch/list 查询参数。"""
    province = payload.get("province")
    classify = payload.get("classify")
    score = payload.get("score")
    if not province or not classify or score is None:
        raise ValueError("批次接口需要 province、classify、score")

    validate_classify(str(province), str(classify))

    params: dict[str, Any] = {
        "province": province,
        "classify": classify,
        "score": int(score),
    }
    grade_type = payload.get("gradeType")
    if not grade_type and province in PROVINCES_REQUIRING_GRADE_TYPE:
        grade_type = infer_grade_type(
            str(province),
            int(score),
            batch_pref=payload.get("batch"),
        )
        if grade_type:
            payload["gradeType"] = grade_type
    if province in PROVINCES_REQUIRING_GRADE_TYPE and grade_type:
        params["gradeType"] = grade_type
    return params


def normalize_subjects_for_api(payload: dict[str, Any]) -> None:
    """按省份规则规范化 subjects 字段。"""
    province = payload.get("province")
    grade_type = payload.get("gradeType")
    subjects = payload.get("subjects")

    if province == "新疆":
        if subjects in (None, "", "null", "NULL"):
            payload.pop("subjects", None)
        return

    if province in PROVINCES_REQUIRING_GRADE_TYPE and grade_type == "专科":
        if subjects in (None, "", "null", "NULL"):
            payload["subjects"] = "null"
        return

    if subjects in ("null", "NULL", ""):
        payload["subjects"] = None


def sanitize_payload_for_api(payload: dict[str, Any]) -> None:
    """发志愿接口前按省份规则清理请求体。"""
    province = payload.get("province")
    if province not in PROVINCES_REQUIRING_GRADE_TYPE:
        payload.pop("gradeType", None)
    normalize_subjects_for_api(payload)


def validate_subjects_for_volunteer_api(payload: dict[str, Any]) -> None:
    """志愿接口前校验 subjects 是否满足省份要求。"""
    province = str(payload.get("province") or "")
    mode = get_province_mode(province)
    label = MODE_LABELS.get(mode, mode)

    if province == "新疆":
        return
    if province in PROVINCES_REQUIRING_GRADE_TYPE and payload.get("gradeType") == "专科":
        return

    subjects = payload.get("subjects")
    if subjects in (None, "", "null", "NULL"):
        raise ValueError(
            f"缺少 subjects：{province}（{label}）需传选科组合，如 物理,化学,生物"
        )

    parts = parse_subjects_list(subjects)
    classify = payload.get("classify")

    if mode == "312":
        if len(parts) != 3:
            raise ValueError(
                f"subjects 格式错误：{province}（3+1+2）须传完整三科（首选科目+两门再选），"
                f"逗号分隔，如 classify=物理 时 subjects=物理,化学,生物；"
                f"不能只传两门再选科目。当前为 {subjects!r}（{len(parts)} 科）"
            )
        if classify not in parts:
            raise ValueError(
                f"subjects 与 classify 不一致：{province} classify={classify!r}，"
                f"subjects 须包含首选科目 {classify!r}，当前为 {subjects!r}"
            )
        electives = [p for p in parts if p != classify]
        if len(electives) != 2:
            raise ValueError(
                f"subjects 格式错误：{province}（3+1+2）除首选科目外还须两门再选"
                f"（化学/生物/政治/地理），当前为 {subjects!r}"
            )
        invalid = [p for p in electives if p not in SUBJECTS_312_ELECTIVES]
        if invalid:
            raise ValueError(
                f"subjects 含无效再选科目 {invalid}：3+1+2 再选仅限化学/生物/政治/地理"
            )
        return

    if mode == "33" and province not in PROVINCES_REQUIRING_GRADE_TYPE:
        if len(parts) != 3:
            raise ValueError(
                f"subjects 格式错误：{province}（3+3）须传完整三科选考科目，"
                f"逗号分隔，如 物理,化学,生物；当前为 {subjects!r}（{len(parts)} 科）"
            )
        pool = SUBJECTS_33_ZHEJIANG if province == "浙江" else SUBJECTS_33_POOL
        invalid = [p for p in parts if p not in pool]
        if invalid:
            raise ValueError(f"subjects 含无效科目 {invalid}：{province} 选考范围见 reference.md")
        return

    if mode == "33" and province in PROVINCES_REQUIRING_GRADE_TYPE:
        if payload.get("gradeType") == "本科" and len(parts) != 3:
            raise ValueError(
                f"subjects 格式错误：{province}（3+3 本科）须传完整三科，"
                f"如 物理,化学,生物；当前为 {subjects!r}"
            )
