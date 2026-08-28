from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Literal


QuestionType = Literal["single_choice", "true_false", "fill_blank", "short_answer"]


@dataclass
class KnowledgeSource:
    document_id: str
    section_title: str = ""
    page_start: int | None = None
    page_end: int | None = None
    snippets: list[str] = field(default_factory=list)


@dataclass
class KnowledgePoint:
    id: str
    title: str
    description: str
    definition: str = ""
    tags: list[str] = field(default_factory=list)
    source: KnowledgeSource | None = None


@dataclass
class Question:
    id: str
    knowledge_point_ids: list[str]
    level: int  # 1, 2, 3
    type: QuestionType
    prompt: str
    options: list[str] = field(default_factory=list)
    answer: Any = None
    explanation: str = ""
    source_refs: list[str] = field(default_factory=list)


@dataclass
class QuizSession:
    session_id: str
    user_id: str
    document_id: str
    level: int  # 1, 2, 3
    knowledge_point_ids: list[str]
    questions: list[Question]
    status: str = "generated"


@dataclass
class AnswerResult:
    question_id: str
    user_answer: Any
    is_correct: bool | None  # None for short_answer needing review
    score: float | None  # None for short_answer needing review
    feedback: str = ""
    error_type: str = "unknown"
    needs_review: bool = False


@dataclass
class MasteryRecord:
    knowledge_point_id: str
    current_level: int = 1  # 1, 2, 3
    attempts: int = 0
    last_accuracy: float = 0.0
    best_accuracy: float = 0.0
    last_reviewed_at: str | None = None
    is_weak: bool = False
    accuracy_history: list[float] = field(default_factory=list)
    next_review_at: str | None = None  # ISO date string YYYY-MM-DD
    review_stage: int = 0  # 0-4, maps to [1, 2, 4, 7, 15] days


def to_dict(obj: Any) -> Any:
    """Convert a dataclass instance to dict."""
    if hasattr(obj, "__dataclass_fields__"):
        return asdict(obj)
    return obj
