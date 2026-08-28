#!/usr/bin/env python3
"""从题目文件导入题目。

用法：python3 import_quiz.py <file_path> <document_id> <user_id>

输出：JSON 格式的 prompt（system_prompt + user_prompt），由 agent 发给 LLM 解析题目。
LLM 返回题目 JSON 后，agent 应调用 service.import_questions() 导入。
"""
from pathlib import Path
import json
import sys

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from quiz_mastery.file_parser import parse_file
from quiz_mastery.quiz_extractor import build_extraction_prompt


def main() -> None:
    if len(sys.argv) < 4:
        print("Usage: import_quiz.py <file_path> <document_id> <user_id>")
        print("  file_path:   Path to question file (.md, .txt, .text)")
        print("  document_id: Identifier for this document")
        print("  user_id:     User identifier")
        sys.exit(1)

    file_path = sys.argv[1]
    document_id = sys.argv[2]
    user_id = sys.argv[3]

    content = parse_file(file_path)
    prompts = build_extraction_prompt(content)

    output = {
        "action": "import_questions",
        "document_id": document_id,
        "user_id": user_id,
        "file_path": file_path,
        "prompts": prompts,
        "instructions": (
            "Send the system_prompt and user_prompt to an LLM. "
            "The LLM should return a JSON array of questions. "
            "Then call service.import_questions(document_id, user_id, questions) to import."
        ),
    }

    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
