from __future__ import annotations

import json
from .models import KnowledgePoint


# Maximum questions per quiz round
MAX_QUESTIONS_PER_ROUND = 15

# Question type distribution by level
LEVEL_DISTRIBUTION = {
    1: {"single_choice": 70, "true_false": 30},
    2: {"single_choice": 50, "fill_blank": 30, "true_false": 20},
    3: {"single_choice": 40, "fill_blank": 20, "true_false": 20, "short_answer": 20},
}


class QuizGenerator:
    """Builds prompt templates for LLM-based quiz generation.

    This module does NOT call any LLM API. It constructs system_prompt and
    user_prompt that should be sent to an LLM by the caller (agent).
    """

    def generate_quiz(
        self,
        knowledge_points: list[KnowledgePoint],
        level: int = 1,
        num_questions: int | None = None,
    ) -> dict:
        """Build prompts for quiz generation.

        Args:
            knowledge_points: List of knowledge points to quiz on.
            level: Difficulty level (1, 2, or 3).
            num_questions: Number of questions to generate (max 15).

        Returns:
            dict with 'system_prompt' and 'user_prompt' keys.
        """
        level = max(1, min(3, level))
        if num_questions is None:
            num_questions = 3  # Default: 3 questions per round for efficiency
        num_questions = min(num_questions, MAX_QUESTIONS_PER_ROUND)

        distribution = LEVEL_DISTRIBUTION[level]
        distribution_text = "\n".join(
            f"  - {qtype}: {pct}%" for qtype, pct in distribution.items()
        )

        # Build knowledge point descriptions for the prompt
        kp_descriptions = []
        for kp in knowledge_points:
            desc_parts = [f"- **{kp.title}** (ID: {kp.id})"]
            if kp.definition:
                desc_parts.append(f"  定义: {kp.definition}")
            if kp.description:
                desc_parts.append(f"  描述: {kp.description}")
            if kp.source and kp.source.snippets:
                desc_parts.append(f"  原文片段: {'; '.join(kp.source.snippets)}")
            kp_descriptions.append("\n".join(desc_parts))

        kp_text = "\n\n".join(kp_descriptions)

        level_desc = {
            1: "识记（基础记忆和理解，考察概念辨认和基本事实）",
            2: "理解（深层理解，考察概念区分、原理解释和简单应用）",
            3: "应用（综合运用，考察实际场景应用、分析和问题解决）",
        }

        system_prompt = (
            "你是一个专业的出题助手。根据提供的知识点信息，生成高质量的测验题目。\n"
            "严格按照要求的 JSON 格式输出，不要输出任何其他内容。\n"
            "题目必须紧扣知识点的名称、定义和原文描述，不能出脱离原文的题目。"
        )

        user_prompt = f"""请根据以下知识点生成 {num_questions} 道测验题。

## 难度级别
Level {level}: {level_desc[level]}

## 题型分配
{distribution_text}

## 知识点信息

{kp_text}

## 出题要求
1. 每道题必须关联至少一个知识点 ID
2. 选择题 (single_choice)：4 个选项 A/B/C/D，answer 填正确选项字母
3. 判断题 (true_false)：answer 填 "True" 或 "False"
4. 填空题 (fill_blank)：prompt 中用 ____ 标记空白处，answer 填正确答案文本
5. 简答题 (short_answer)：answer 填参考答案
6. 每道题必须包含 explanation（解析）
7. 题目内容必须基于上述知识点的名称、定义和描述，不要超出范围
8. **每道题必须填写 `category` 和 `knowledge_point` 字段**（用于分类筛选和侧栏分组）：
   - `category`：一级分类，**短词**（建议 2-6 字），用于顶部分类筛选 chip。
     例：物理 / 数学 / 法律 / 历史 / 编程 / 通用 等。
     **不要**写成长串、不要含日期、不要含编号、不要含书名号或斜杠。
   - `knowledge_point`：所属知识点名称（直接用关联知识点的 title 即可），用于侧栏分组。
9. 总题数：{num_questions} 道

## 输出格式
输出纯 JSON 数组，每个元素格式如下：
```json
[
  {{
    "id": "q_001",
    "knowledge_point_ids": ["kp_id"],
    "category": "物理",
    "knowledge_point": "牛顿第二定律",
    "level": {level},
    "type": "single_choice",
    "prompt": "题目内容",
    "options": ["A. 选项一", "B. 选项二", "C. 选项三", "D. 选项四"],
    "answer": "A",
    "explanation": "解析内容"
  }}
]
```

请直接输出 JSON 数组，不要包含 markdown 代码块标记或其他文字。"""

        return {
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
        }
