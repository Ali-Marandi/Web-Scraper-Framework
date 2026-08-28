#!/usr/bin/env python3
"""生成出题 prompt。

用法：python3 run_quiz.py <user_id> <document_id>

根据已保存的知识点和用户掌握度记录，自动决定出题难度。
- 从 mastery_records 读取每个知识点的 current_level
- 首次出题的知识点强制 level=1
- 输出 JSON 格式的 prompt（system_prompt + user_prompt），由 agent 发给 LLM 生成题目

也支持指定知识点和难度：
  python3 run_quiz.py <user_id> <document_id> [level] [kp_id1,kp_id2,...]
"""
from pathlib import Path
import json
import sys

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from quiz_mastery import QuizMasteryService


def main() -> None:
    if len(sys.argv) < 3:
        print("Usage: run_quiz.py <user_id> <document_id> [level] [kp_id1,kp_id2,...]")
        print("  user_id:     User identifier")
        print("  document_id: Document identifier")
        print("  level:       Optional difficulty level (1/2/3)")
        print("  kp_ids:      Optional comma-separated knowledge point IDs")
        sys.exit(1)

    user_id = sys.argv[1]
    document_id = sys.argv[2]

    level = None
    kp_ids = None

    if len(sys.argv) >= 4:
        try:
            level = int(sys.argv[3])
        except ValueError:
            # Maybe it's kp_ids instead
            kp_ids = sys.argv[3].split(",")

    if len(sys.argv) >= 5:
        kp_ids = sys.argv[4].split(",")

    service = QuizMasteryService(
        base_dir=Path(__file__).resolve().parents[1] / "data"
    )

    result = service.generate_quiz_for_user(
        user_id=user_id,
        document_id=document_id,
        knowledge_point_ids=kp_ids,
        level=level,
    )

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
