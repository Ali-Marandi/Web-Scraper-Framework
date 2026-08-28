#!/usr/bin/env python3
"""提交测验答案并评分。

用法：python3 submit_answers.py <user_id> <document_id> <session_id> <answers_json>

参数：
  user_id:      用户标识
  document_id:  文档标识
  session_id:   测验会话 ID
  answers_json: JSON 格式的答案字典，如 '{"q_001":"A","q_002":"True"}'

输出：评分结果 JSON（score, total, accuracy, results）。
"""
from pathlib import Path
import json
import sys

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from quiz_mastery import QuizMasteryService


def main() -> None:
    if len(sys.argv) < 5:
        print("Usage: submit_answers.py <user_id> <document_id> <session_id> <answers_json>")
        sys.exit(1)

    user_id = sys.argv[1]
    document_id = sys.argv[2]
    session_id = sys.argv[3]
    answers = json.loads(sys.argv[4])

    service = QuizMasteryService(
        base_dir=Path(__file__).resolve().parents[1] / "data"
    )

    result = service.submit_quiz_answers(
        user_id=user_id,
        document_id=document_id,
        session_id=session_id,
        answers=answers,
    )

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
