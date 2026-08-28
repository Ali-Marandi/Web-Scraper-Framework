from __future__ import annotations

from .models import Question, AnswerResult


class Evaluator:
    """Evaluates user answers against correct answers.

    - single_choice / true_false: exact match
    - fill_blank: case-insensitive, strip whitespace
    - short_answer: no auto-scoring, returns needs_review=True
    """

    def evaluate_answers(
        self,
        questions: list[Question],
        user_answers: dict[str, str],
    ) -> list[AnswerResult]:
        results: list[AnswerResult] = []

        for q in questions:
            user_answer = user_answers.get(q.id)

            if q.type == "short_answer":
                # Short answer: cannot auto-evaluate, needs human/LLM review
                results.append(
                    AnswerResult(
                        question_id=q.id,
                        user_answer=user_answer,
                        is_correct=None,
                        score=None,
                        feedback="需要人工/LLM评判",
                        error_type="pending_review",
                        needs_review=True,
                    )
                )
                continue

            if user_answer is None:
                results.append(
                    AnswerResult(
                        question_id=q.id,
                        user_answer=None,
                        is_correct=False,
                        score=0.0,
                        feedback=f"未作答。正确答案：{q.answer}。{q.explanation}",
                        error_type="no_answer",
                        needs_review=False,
                    )
                )
                continue

            if q.type == "fill_blank":
                # Fill-in-the-blank: case-insensitive, strip whitespace
                is_correct = (
                    user_answer.strip().lower() == str(q.answer).strip().lower()
                )
            else:
                # single_choice / true_false: exact match
                is_correct = user_answer.strip() == str(q.answer).strip()

            results.append(
                AnswerResult(
                    question_id=q.id,
                    user_answer=user_answer,
                    is_correct=is_correct,
                    score=1.0 if is_correct else 0.0,
                    feedback=(
                        q.explanation
                        if is_correct
                        else f"回答错误。正确答案：{q.answer}。{q.explanation}"
                    ),
                    error_type="none" if is_correct else "concept_confusion",
                    needs_review=False,
                )
            )

        return results
