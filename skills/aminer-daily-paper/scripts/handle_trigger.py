#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

def _clean_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _split_topics(text: str) -> list[str]:
    pieces = re.split(r"[,，;/；、\n]+", text)
    topics: list[str] = []
    for piece in pieces:
        topic = _clean_text(piece)
        if topic and topic not in topics:
            topics.append(topic)
    return topics


def _split_papers(text: str) -> list[str]:
    pieces = re.split(r"[|\n;；]+", text)
    papers: list[str] = []
    for piece in pieces:
        paper = _clean_text(piece)
        if paper and paper not in papers:
            papers.append(paper)
    return papers


def _extract_command_text(raw_text: str) -> str:
    lines = [line.strip() for line in str(raw_text or "").splitlines() if line.strip()]
    for line in reversed(lines):
        match = re.search(r"(/(?:skill\s+)?aminer[-_]dp\b.*)$", line, flags=re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return str(raw_text or "")


FIELD_LABELS = {
    "aminer_author_id": ["aminer_author_id"],
    "topics": ["topics", "topic", "方向", "研究方向"],
    "scholar_name": ["scholar", "name", "author", "学者", "作者"],
    "scholar_org": ["org", "organization", "affiliation", "机构", "单位"],
    "paper_titles": ["paper", "papers", "代表作", "论文"],
    "papers_file": ["papers_file", "source_file", "profile_file", "文件", "路径"],
    "language_sort": ["language_sort"],
    "size": ["size"],
}


GENERIC_REQUEST_PATTERNS = [
    r"帮我推荐(?:一下)?论文",
    r"推荐(?:一下)?论文",
    r"推荐一些论文",
    r"给我推荐(?:一下)?论文",
    r"推荐最近论文",
    r"想看论文",
]

ORG_HINT_PATTERNS = (
    r"大学",
    r"学院",
    r"研究院",
    r"研究所",
    r"实验室",
    r"中心",
    r"University",
    r"College",
    r"Institute",
    r"Laboratory",
    r"Lab\b",
    r"School",
    r"Department",
)


MAX_TOPICS = 8
MAX_TOPIC_LENGTH = 80
MAX_PAPER_TITLES = 8
MAX_PAPER_TITLE_LENGTH = 300
MAX_SCHOLAR_NAME_LENGTH = 80
MAX_SCHOLAR_ORG_LENGTH = 160
MAX_FREE_TEXT_LENGTH = 600
ALLOWED_PAPERS_FILE_SUFFIXES = {".json"}
TOPIC_STOPWORDS = {
    "论文",
    "推荐",
    "一下",
    "推荐一下",
    "相关论文",
    "papers",
    "paper",
    "recommend",
    "recommendation",
    "research papers",
}
TOPIC_STOPWORDS_CASEFOLD = {item.casefold() for item in TOPIC_STOPWORDS}


def _capture_field(command_body: str, field_name: str) -> str:
    labels = FIELD_LABELS[field_name]
    all_labels = [re.escape(label) for values in FIELD_LABELS.values() for label in values]
    pattern = rf"(?:{'|'.join(re.escape(label) for label in labels)})\s*[:：]\s*(.+?)(?=\s*(?:{'|'.join(all_labels)})\s*[:：]|$)"
    match = re.search(pattern, command_body, flags=re.IGNORECASE | re.S)
    return _clean_text(match.group(1)) if match else ""


def _truncate_text(value: Any, max_length: int) -> str:
    cleaned = _clean_text(value)
    if len(cleaned) <= max_length:
        return cleaned
    return cleaned[:max_length].strip()


def _normalize_topics_for_interface(values: list[Any]) -> list[str]:
    topics: list[str] = []
    for value in list(values or []):
        topic = _truncate_text(value, MAX_TOPIC_LENGTH)
        if topic and topic not in topics:
            topics.append(topic)
        if len(topics) >= MAX_TOPICS:
            break
    return topics


def _normalize_paper_titles_for_interface(values: list[Any]) -> list[str]:
    paper_titles: list[str] = []
    for value in list(values or []):
        paper_title = _truncate_text(value, MAX_PAPER_TITLE_LENGTH)
        if paper_title and paper_title not in paper_titles:
            paper_titles.append(paper_title)
        if len(paper_titles) >= MAX_PAPER_TITLES:
            break
    return paper_titles


def _resolve_interface_papers_file(base_dir: Path, path_text: str) -> str:
    cleaned = _clean_text(path_text)
    if not cleaned:
        return ""

    candidate = Path(cleaned).expanduser()
    resolved_base_dir = base_dir.resolve()
    resolved_candidate = (resolved_base_dir / candidate).resolve() if not candidate.is_absolute() else candidate.resolve()
    try:
        resolved_candidate.relative_to(resolved_base_dir)
    except ValueError as exc:
        raise ValueError("papers_file_outside_base_dir") from exc

    if resolved_candidate.suffix.lower() not in ALLOWED_PAPERS_FILE_SUFFIXES:
        raise ValueError("unsupported_papers_file")
    return str(resolved_candidate)


def _normalize_interface_payload(parsed: dict[str, Any], *, base_dir: Path) -> dict[str, Any]:
    normalized = dict(parsed)
    raw_uid = _clean_text(parsed.get("raw_aminer_author_id"))
    if raw_uid and not re.fullmatch(r"[0-9a-fA-F]{24}", raw_uid):
        raise ValueError("invalid_aminer_author_id")

    normalized["aminer_author_id"] = _clean_text(parsed.get("aminer_author_id"))
    normalized["topics"] = _normalize_topics_for_interface(list(parsed.get("topics") or []))
    normalized["scholar_name"] = _truncate_text(parsed.get("scholar_name"), MAX_SCHOLAR_NAME_LENGTH)
    normalized["scholar_org"] = _truncate_text(parsed.get("scholar_org"), MAX_SCHOLAR_ORG_LENGTH)
    normalized["paper_titles"] = _normalize_paper_titles_for_interface(list(parsed.get("paper_titles") or []))
    normalized["papers_file"] = _resolve_interface_papers_file(base_dir, str(parsed.get("papers_file") or ""))
    normalized["free_text"] = _truncate_text(parsed.get("free_text"), MAX_FREE_TEXT_LENGTH)
    lang = _clean_text(parsed.get("language_sort"))
    normalized["language_sort"] = lang if lang in {"zh", "en"} else ""
    raw_size = _clean_text(parsed.get("size"))
    try:
        normalized["size"] = max(1, min(int(raw_size), 20)) if raw_size else 0
    except (ValueError, TypeError):
        normalized["size"] = 0
    if not normalized["topics"] and normalized["free_text"]:
        normalized["topics"] = _infer_topics_from_free_text(normalized["free_text"])
    return normalized


def _strip_explicit_fields(command_body: str) -> str:
    all_labels = [re.escape(label) for values in FIELD_LABELS.values() for label in values]
    pattern = rf"(?:{'|'.join(all_labels)})\s*[:：]\s*.+?(?=\s*(?:{'|'.join(all_labels)})\s*[:：]|$)"
    cleaned = re.sub(pattern, " ", command_body, flags=re.IGNORECASE | re.S)
    return _clean_text(cleaned)


def _remove_generic_request_phrases(text: str) -> str:
    cleaned = str(text or "")
    for pattern in GENERIC_REQUEST_PATTERNS:
        cleaned = re.sub(pattern, " ", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"[。！？!?.，,；;、\s]+", " ", cleaned)
    return _clean_text(cleaned)


def _normalize_topic_candidate(text: str) -> str:
    candidate = _clean_text(text)
    if not candidate:
        return ""
    candidate = re.sub(r'^[\'"`“”‘’]+|[\'"`“”‘’]+$', "", candidate)
    candidate = re.sub(r"^(?:关于|研究(?:方向)?|方向|领域|做|关注|topic(?:s)?|about|on)\s*", "", candidate, flags=re.IGNORECASE)
    candidate = re.sub(r"\s*(?:相关|方向|领域|论文|papers?|research)\s*$", "", candidate, flags=re.IGNORECASE)
    candidate = _clean_text(candidate)
    if not candidate:
        return ""
    if candidate.casefold() in TOPIC_STOPWORDS_CASEFOLD:
        return ""
    return _truncate_text(candidate, MAX_TOPIC_LENGTH)


def _infer_topics_from_free_text(text: str) -> list[str]:
    cleaned = _clean_text(text)
    if not cleaned:
        return []

    for pattern in GENERIC_REQUEST_PATTERNS:
        cleaned = re.sub(pattern, " ", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\b(?:recommend|papers?|please|find|show)\b", " ", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"(?:给我|帮我|请|想看|想要|推荐|看看)\s*", " ", cleaned)
    cleaned = _clean_text(cleaned)
    if not cleaned:
        return []

    parts = re.split(r"[,，;/；、\n]+|\s+(?:and|or|以及|和|与|及)\s+", cleaned, flags=re.IGNORECASE)
    topics: list[str] = []
    seen: set[str] = set()
    for part in parts:
        candidate = _normalize_topic_candidate(part)
        if not candidate:
            continue
        key = candidate.casefold()
        if key in seen:
            continue
        seen.add(key)
        topics.append(candidate)
        if len(topics) >= MAX_TOPICS:
            break
    if topics:
        return topics

    fallback = _normalize_topic_candidate(cleaned)
    return [fallback] if fallback else []


def _infer_scholar_from_free_text(text: str) -> tuple[str, str, str]:
    normalized = _clean_text(text)
    if not normalized:
        return "", "", ""

    patterns = [
        r"^我(?:是|叫)\s*(?P<name>[^，,。；;、\s]{2,20})\s*[，,、]\s*(?P<org>[^。；;，,]{2,60})",
        r"^本人(?:是)?\s*(?P<name>[^，,。；;、\s]{2,20})\s*[，,、]\s*(?P<org>[^。；;，,]{2,60})",
        r"^我是\s*(?P<org>[^，,。；;]{2,60})\s*的\s*(?P<name>[^，,。；;、\s]{2,20})",
    ]
    for pattern in patterns:
        match = re.search(pattern, normalized, flags=re.IGNORECASE)
        if not match:
            continue
        scholar_name = _clean_text(match.groupdict().get("name"))
        scholar_org = _clean_text(match.groupdict().get("org"))
        if not scholar_name:
            continue
        residual = _clean_text(normalized[match.end() :])
        residual = _remove_generic_request_phrases(residual)
        scholar_org = re.split(r"[。！？!?.；;]", scholar_org, maxsplit=1)[0].strip()
        scholar_org = _remove_generic_request_phrases(scholar_org)
        return scholar_name, scholar_org, residual

    bare_match = re.search(
        r"^(?P<name>[A-Za-z][A-Za-z .'-]{1,60}|[\u4e00-\u9fff·]{2,20})\s*[，,、]\s*(?P<org>[^。；;，,\n]{2,80})",
        normalized,
        flags=re.IGNORECASE,
    )
    if bare_match:
        scholar_name = _clean_text(bare_match.group("name"))
        scholar_org = _clean_text(bare_match.group("org"))
        org_hint_pattern = "|".join(ORG_HINT_PATTERNS)
        if scholar_name and scholar_org and re.search(org_hint_pattern, scholar_org, flags=re.IGNORECASE):
            residual = _clean_text(normalized[bare_match.end() :])
            residual = _remove_generic_request_phrases(residual)
            scholar_org = re.split(r"[。！？!?.；;]", scholar_org, maxsplit=1)[0].strip()
            scholar_org = _remove_generic_request_phrases(scholar_org)
            return scholar_name, scholar_org, residual
    return "", "", normalized


def parse_trigger_text(text: str) -> dict[str, Any]:
    raw_text = str(text or "")
    command_text = _extract_command_text(raw_text)
    normalized = _clean_text(command_text)
    is_trigger = bool(re.search(r"^/(skill\s+)?aminer[-_]dp\b", normalized, flags=re.IGNORECASE))
    body = re.sub(r"^/(skill\s+)?aminer[-_]dp\b", "", command_text, flags=re.IGNORECASE).strip()

    uid_match = re.search(r"aminer_author_id\s*[:：]\s*([0-9a-fA-F]{24})", body, flags=re.IGNORECASE)
    uid = uid_match.group(1) if uid_match else ""
    scholar_name = _capture_field(body, "scholar_name")
    scholar_org = _capture_field(body, "scholar_org")
    free_text = _strip_explicit_fields(body)
    if not scholar_name:
        inferred_name, inferred_org, residual = _infer_scholar_from_free_text(free_text)
        if inferred_name:
            scholar_name = inferred_name
            if inferred_org and not scholar_org:
                scholar_org = inferred_org
            free_text = residual

    return {
        "raw_text": raw_text,
        "command_text": command_text,
        "raw_aminer_author_id": _capture_field(body, "aminer_author_id"),
        "aminer_author_id": uid,
        "topics": _split_topics(_capture_field(body, "topics")),
        "scholar_name": scholar_name,
        "scholar_org": scholar_org,
        "paper_titles": _split_papers(_capture_field(body, "paper_titles")),
        "papers_file": _capture_field(body, "papers_file"),
        "language_sort": _capture_field(body, "language_sort"),
        "size": _capture_field(body, "size"),
        "free_text": free_text,
        "is_trigger": is_trigger,
    }


def _load_config(base_dir: Path, config_path: Path | None) -> dict[str, Any]:
    if config_path and config_path.exists():
        return yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    default_path = base_dir / "config.yaml"
    if default_path.exists():
        return yaml.safe_load(default_path.read_text(encoding="utf-8")) or {}
    return {}


def _run_pipeline(
    *,
    base_dir: Path,
    output_dir: Path,
    config_path: Path | None,
    aminer_author_id: str,
    topics: list[str],
    scholar_name: str,
    scholar_org: str,
    paper_titles: list[str],
    papers_file: str,
    free_text: str,
    language_sort: str,
    size: int,
) -> dict[str, Any]:
    command = [
        sys.executable,
        str(base_dir / "scripts" / "run_pipeline.py"),
        "--base-dir",
        str(base_dir),
        "--output-dir",
        str(output_dir),
    ]
    if config_path is not None:
        command.extend(["--config", str(config_path)])
    if aminer_author_id.strip():
        command.extend(["--aminer-author-id", aminer_author_id.strip()])
    if language_sort.strip():
        command.extend(["--language-sort", language_sort.strip()])
    if size > 0:
        command.extend(["--size", str(size)])
    if topics:
        command.extend(["--topics", *topics])
    if scholar_name.strip():
        command.extend(["--scholar-name", scholar_name.strip()])
    if scholar_org.strip():
        command.extend(["--scholar-org", scholar_org.strip()])
    for paper_title in paper_titles:
        if paper_title.strip():
            command.extend(["--paper-title", paper_title.strip()])
    if papers_file.strip():
        command.extend(["--papers-file", papers_file.strip()])
    if free_text.strip():
        command.extend(["--free-text", free_text.strip()])
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip() or "run_pipeline failed"
        raise RuntimeError(detail)
    return json.loads(completed.stdout)


def _compact_pipeline_error(detail: str) -> str:
    text = _clean_text(detail)
    if not text:
        return "unknown_error"
    if "Traceback" not in text:
        return text
    lines = [line.strip() for line in str(detail or "").splitlines() if line.strip()]
    for line in reversed(lines):
        if line.startswith("RuntimeError:"):
            return _clean_text(line.split("RuntimeError:", 1)[1])
    return _clean_text(lines[-1]) if lines else text


def handle_trigger(
    *,
    base_dir: Path,
    text: str,
    config_path: Path | None = None,
) -> dict[str, Any]:
    parsed = parse_trigger_text(text)
    try:
        parsed = _normalize_interface_payload(parsed, base_dir=base_dir)
    except ValueError as exc:
        detail = _clean_text(str(exc))
        if detail == "invalid_aminer_author_id":
            reply_text = "输入里的 `aminer_author_id` 不合法。请提供 24 位十六进制字符串，例如：`/aminer-dp aminer_author_id: 696259801cb939bc391d3a37 topics: 多模态, 智能体`。"
        elif detail == "papers_file_outside_base_dir":
            reply_text = "出于安全限制，`papers_file` 只能指向当前 skill 目录内的 JSON 文件，不能引用目录外路径。"
        elif detail == "unsupported_papers_file":
            reply_text = "`papers_file` 目前只支持 `.json` 文件。"
        else:
            reply_text = f"输入不符合接口约束：{detail}"
        return {
            "status": "success",
            "mode": "invalid_input",
            "final_response": "TEXT",
            "reply_text": reply_text,
        }
    has_profile_input = bool(
        parsed["aminer_author_id"]
        or parsed["topics"]
        or parsed["scholar_name"]
        or parsed["scholar_org"]
        or parsed["paper_titles"]
        or parsed["papers_file"]
        or parsed["free_text"]
    )
    if not parsed["is_trigger"] and not has_profile_input:
        return {
            "status": "success",
            "mode": "help",
            "final_response": "TEXT",
            "reply_text": "请发送 `/aminer-dp`（直接推荐），或加上 `topics: 多模态, 智能体`、`scholar: Jie Tang` 等参数精确推荐，也可以直接描述研究方向。",
        }

    output_dir = base_dir / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)
    loaded_config = _load_config(base_dir, config_path)
    runtime_config_path = output_dir / "runtime_config.yaml"
    runtime_config_path.write_text(yaml.safe_dump(loaded_config, allow_unicode=True, sort_keys=False), encoding="utf-8")

    try:
        pipeline_result = _run_pipeline(
            base_dir=base_dir,
            output_dir=output_dir,
            config_path=runtime_config_path,
            aminer_author_id=parsed["aminer_author_id"],
            topics=parsed["topics"],
            scholar_name=parsed["scholar_name"],
            scholar_org=parsed["scholar_org"],
            paper_titles=parsed["paper_titles"],
            papers_file=parsed["papers_file"],
            free_text=parsed["free_text"],
            language_sort=parsed["language_sort"],
            size=parsed["size"],
        )
    except Exception as exc:
        detail = _compact_pipeline_error(str(exc).strip())
        if parsed["aminer_author_id"] and not parsed["topics"] and ("profile_unavailable" in detail or "missing_topics" in detail or "no_bind_papers_or_experts_topic" in detail):
            return {
                "status": "success",
                "mode": "onboarding_prompt",
                "final_response": "TEXT",
                "reply_text": f"我还没能从这个 `aminer_author_id` 归纳出稳定研究方向，请补充研究方向或代表论文，例如：`/aminer-dp aminer_author_id: {parsed['aminer_author_id']} topics: 多模态, 智能体`。",
            }
        if parsed["scholar_name"] and ("profile_unavailable" in detail or "missing_topics" in detail):
            return {
                "status": "success",
                "mode": "onboarding_prompt",
                "final_response": "TEXT",
                "reply_text": "我查到了学者线索，但还没成功归纳出稳定研究方向。请补充 `topics`、代表论文标题，或直接描述方向，例如：`/aminer-dp 我是张帆进，清华大学，做多模态智能体和 tool-use`。",
            }
        return {
            "status": "success",
            "mode": "error",
            "final_response": "TEXT",
            "reply_text": f"推荐流程执行失败，出错阶段：{detail}",
        }

    result: dict[str, Any] = {
        "status": "success",
        "mode": pipeline_result.get("mode", "success"),
        "parsed_input": parsed,
        "artifacts": {
            "runtime_config": str(runtime_config_path),
            "output_dir": str(output_dir),
        },
        "pipeline": pipeline_result,
        "final_response": pipeline_result.get("final_response", "TEXT"),
    }
    reply_text = pipeline_result.get("reply_text", "")
    if reply_text:
        result["reply_text"] = reply_text
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Parse and run aminer-daily-paper recommendation from trigger text.")
    parser.add_argument("--base-dir", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--text", required=True)
    parser.add_argument("--config", type=Path, default=None)
    args = parser.parse_args()

    result = handle_trigger(
        base_dir=args.base_dir.resolve(),
        text=args.text,
        config_path=args.config.resolve() if args.config else None,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
