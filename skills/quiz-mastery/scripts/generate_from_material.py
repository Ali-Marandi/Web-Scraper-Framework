#!/usr/bin/env python3
"""从学习资料生成知识点提取 prompt。

用法：python3 generate_from_material.py <file_path> <document_id>

输出：JSON 格式的 prompt（system_prompt + user_prompt），由 agent 发给 LLM 执行。
LLM 返回知识点 JSON 后，agent 应调用 service.save_knowledge_points() 保存。
"""
from pathlib import Path
import json
import sys

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from quiz_mastery.file_parser import parse_file, build_extraction_prompt


def main() -> None:
    if len(sys.argv) < 3:
        print("Usage: generate_from_material.py <file_path> <document_id>")
        print("  file_path:   Path to study material (.md, .txt, .text)")
        print("  document_id: Identifier for this document")
        sys.exit(1)

    file_path = sys.argv[1]
    document_id = sys.argv[2]

    content = parse_file(file_path)
    prompts = build_extraction_prompt(content)

    output = {
        "action": "extract_knowledge_points",
        "document_id": document_id,
        "file_path": file_path,
        "prompts": prompts,
        "instructions": (
            "Send the system_prompt and user_prompt to an LLM. "
            "The LLM should return a JSON array of knowledge points. "
            "Then call save_knowledge_points(document_id, knowledge_points) to save."
        ),
    }

    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
