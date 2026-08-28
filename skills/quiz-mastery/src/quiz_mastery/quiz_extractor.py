from __future__ import annotations

import json
from .models import Question


def build_extraction_prompt(content: str) -> dict:
    """Build a prompt for LLM to parse questions from a question file.

    Args:
        content: Raw text content containing questions.

    Returns:
        dict with 'system_prompt' and 'user_prompt' keys.
    """
    system_prompt = (
        "你是一个专业的题目解析助手。从用户提供的题目文件中识别并解析所有题目。\n"
        "严格按照要求的 JSON 格式输出，不要输出任何其他内容。"
    )

    user_prompt = f"""请从以下题目文件内容中解析出所有题目。

## 题目文件内容

{content}

## 解析要求
1. 识别每道题的类型：
   - single_choice: 选择题（有 A/B/C/D 等选项）
   - true_false: 判断题（判断对错）
   - fill_blank: 填空题（有空格需要填写）
   - short_answer: 简答题（需要文字回答）
2. 提取题目的所有信息
3. 如果题目有答案和解析，也一并提取
4. 为每道题分配唯一 ID

## 输出格式
输出纯 JSON 数组，每个元素格式如下：
```json
[
  {{
    "id": "q_001",
    "knowledge_point_ids": [],
    "level": 1,
    "type": "single_choice",
    "prompt": "题目内容",
    "options": ["A. 选项一", "B. 选项二", "C. 选项三", "D. 选项四"],
    "answer": "A",
    "explanation": "解析内容（如果有）"
  }}
]
```

注意：
- type 必须是 single_choice, true_false, fill_blank, short_answer 之一
- 选择题的 answer 填选项字母（A/B/C/D）
- 判断题的 answer 填 "True" 或 "False"
- 填空题的 answer 填正确答案文本
- 简答题的 answer 填参考答案（如果有）
- 如果无法确定 knowledge_point_ids，留空数组
- level 默认为 1，如果能从题目难度判断则相应调整

请直接输出 JSON 数组，不要包含 markdown 代码块标记或其他文字。"""

    return {
        "system_prompt": system_prompt,
        "user_prompt": user_prompt,
    }


def parse_questions_json(json_str: str) -> list[Question]:
    """Parse LLM-returned JSON string into a list of Question objects.

    Args:
        json_str: JSON string containing a list of question dicts.

    Returns:
        List of Question objects.

    Raises:
        json.JSONDecodeError: If json_str is not valid JSON.
        ValueError: If the parsed data is not a list.
    """
    # Try to extract JSON from possible markdown code blocks
    cleaned = json_str.strip()
    if cleaned.startswith("```"):
        # Remove markdown code block markers
        lines = cleaned.split("\n")
        # Remove first line (```json or ```)
        lines = lines[1:]
        # Remove last line (```)
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines)

    data = json.loads(cleaned)
    if not isinstance(data, list):
        raise ValueError(f"Expected a JSON array, got {type(data).__name__}")

    questions: list[Question] = []
    for item in data:
        q = Question(
            id=item.get("id", "q_unknown"),
            knowledge_point_ids=item.get("knowledge_point_ids", []),
            level=item.get("level", 1),
            type=item.get("type", "single_choice"),
            prompt=item.get("prompt", ""),
            options=item.get("options", []),
            answer=item.get("answer"),
            explanation=item.get("explanation", ""),
            source_refs=item.get("source_refs", []),
        )
        questions.append(q)

    return questions
