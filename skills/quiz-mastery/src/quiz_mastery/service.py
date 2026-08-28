from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
import uuid
import json

from .models import KnowledgePoint, KnowledgeSource, Question, QuizSession, MasteryRecord
from .repository import JsonRepository
from .quiz_generator import QuizGenerator
from .evaluator import Evaluator
from .mastery_engine import MasteryEngine
from .planner import Planner


class QuizMasteryService:
    def __init__(self, base_dir: str | Path):
        self.repo = JsonRepository(base_dir)
        self.generator = QuizGenerator()
        self.evaluator = Evaluator()
        self.mastery_engine = MasteryEngine()
        self.planner = Planner()

    # ── Knowledge Points ──────────────────────────────────────────

    def load_knowledge_points(self, document_id: str) -> list[KnowledgePoint]:
        """Load knowledge points from JSON file."""
        raw = self.repo.load_json(
            self.repo.knowledge_points_path(document_id), default={}
        )
        items = raw.get("knowledge_points", [])
        result: list[KnowledgePoint] = []

        for item in items:
            source_data = item.get("source")
            kp = KnowledgePoint(
                id=item["id"],
                title=item["title"],
                description=item.get("description", ""),
                definition=item.get("definition", ""),
                tags=item.get("tags", []),
                source=KnowledgeSource(**source_data) if source_data else None,
            )
            result.append(kp)

        return result

    def save_knowledge_points(
        self, document_id: str, knowledge_points_data: list[dict]
    ) -> None:
        """Save extracted knowledge points to JSON.

        Args:
            document_id: Document identifier.
            knowledge_points_data: List of dicts, each with id, title,
                definition, description, tags.
        """
        payload = {"knowledge_points": knowledge_points_data}
        self.repo.save_json(
            self.repo.knowledge_points_path(document_id), payload
        )

    # ── Progress ──────────────────────────────────────────────────

    def load_progress(
        self, user_id: str, document_id: str
    ) -> dict[str, MasteryRecord]:
        """Load user mastery progress from JSON."""
        raw = self.repo.load_json(
            self.repo.progress_path(user_id, document_id), default={}
        )
        mastery_records = raw.get("mastery_records", {})
        parsed: dict[str, MasteryRecord] = {}

        for kp_id, record in mastery_records.items():
            mr = MasteryRecord(knowledge_point_id=kp_id)
            mr.current_level = record.get("current_level", 1)
            mr.attempts = record.get("attempts", 0)
            mr.last_accuracy = record.get("last_accuracy", 0.0)
            mr.best_accuracy = record.get("best_accuracy", 0.0)
            mr.last_reviewed_at = record.get("last_reviewed_at")
            mr.is_weak = record.get("is_weak", False)
            mr.accuracy_history = record.get("accuracy_history", [])
            mr.next_review_at = record.get("next_review_at")
            mr.review_stage = record.get("review_stage", 0)
            parsed[kp_id] = mr

        return parsed

    def save_progress(
        self,
        user_id: str,
        document_id: str,
        records: dict[str, MasteryRecord],
    ) -> None:
        """Save user mastery progress to JSON."""
        payload = {
            "user_id": user_id,
            "document_id": document_id,
            "mastery_records": {
                kp_id: asdict(record) for kp_id, record in records.items()
            },
        }
        self.repo.save_json(
            self.repo.progress_path(user_id, document_id), payload
        )

    # ── Quiz Generation ───────────────────────────────────────────

    def generate_quiz_for_user(
        self,
        user_id: str,
        document_id: str,
        knowledge_point_ids: list[str] | None = None,
        level: int | None = None,
        num_questions: int | None = None,
    ) -> dict:
        """Generate quiz prompts for given knowledge points.

        If knowledge_point_ids is None, uses all knowledge points.
        If level is None, reads current_level from mastery records
        (first-time defaults to 1).

        Returns dict with 'prompts' (system_prompt + user_prompt),
        'knowledge_points' used, and 'level'.
        """
        knowledge_points = self.load_knowledge_points(document_id)
        progress = self.load_progress(user_id, document_id)

        if knowledge_point_ids:
            selected = [kp for kp in knowledge_points if kp.id in knowledge_point_ids]
        else:
            selected = knowledge_points

        if not selected:
            return {"error": "No knowledge points found"}

        # Determine level per knowledge point group
        # Use the most common level or explicit level
        if level is not None:
            quiz_level = max(1, min(3, level))
        else:
            # Determine from mastery records; first-time = 1
            levels = []
            for kp in selected:
                record = progress.get(kp.id)
                if record is None:
                    levels.append(1)  # First time → L1
                else:
                    levels.append(record.current_level)
            # Use the minimum level among selected (conservative)
            quiz_level = min(levels) if levels else 1

        prompts = self.generator.generate_quiz(
            selected, level=quiz_level, num_questions=num_questions
        )

        return {
            "document_id": document_id,
            "user_id": user_id,
            "level": quiz_level,
            "knowledge_point_ids": [kp.id for kp in selected],
            "prompts": prompts,
        }

    # ── Quiz Submission ───────────────────────────────────────────

    def submit_quiz_answers(
        self,
        user_id: str,
        document_id: str,
        session_id: str,
        answers: dict[str, str],
    ) -> dict:
        """Submit answers for a quiz session, evaluate, and update mastery."""
        session_data = self.repo.load_json(
            self.repo.session_path(session_id), default=None
        )
        if not session_data:
            raise FileNotFoundError(f"Quiz session not found: {session_id}")

        questions = []
        for item in session_data["questions"]:
            questions.append(Question(**item))

        results = self.evaluator.evaluate_answers(questions, answers)
        progress = self.load_progress(user_id, document_id)
        updated = self.mastery_engine.update_mastery(progress, questions, results)
        self.save_progress(user_id, document_id, updated)

        # Calculate score (excluding short_answer with score=None)
        scored_results = [r for r in results if r.score is not None]
        score = sum(r.score for r in scored_results)
        total = len(scored_results)
        needs_review_count = sum(1 for r in results if r.needs_review)

        summary = {
            "session_id": session_id,
            "score": score,
            "total": total,
            "accuracy": score / total if total else 0.0,
            "needs_review_count": needs_review_count,
            "results": [asdict(r) for r in results],
        }

        # Update session data
        session_data["answers"] = answers
        session_data["results"] = summary["results"]
        session_data["status"] = "completed"
        self.repo.save_json(self.repo.session_path(session_id), session_data)

        return summary

    # ── Import Questions ──────────────────────────────────────────

    def import_questions(
        self,
        document_id: str,
        user_id: str,
        questions_data: list[dict],
    ) -> dict:
        """Import parsed questions and create a quiz session.

        Args:
            document_id: Document identifier.
            user_id: User identifier.
            questions_data: List of question dicts (from LLM parsing).

        Returns:
            dict with session_id and questions.
        """
        questions: list[Question] = []
        for item in questions_data:
            q = Question(
                id=item.get("id", f"q_{uuid.uuid4().hex[:8]}"),
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

        session_id = f"quiz_{uuid.uuid4().hex[:12]}"
        kp_ids = list(
            set(kp_id for q in questions for kp_id in q.knowledge_point_ids)
        )
        level = questions[0].level if questions else 1

        session = QuizSession(
            session_id=session_id,
            user_id=user_id,
            document_id=document_id,
            level=level,
            knowledge_point_ids=kp_ids,
            questions=questions,
        )

        self.repo.save_json(
            self.repo.session_path(session_id),
            asdict(session),
        )

        return {
            "session_id": session_id,
            "document_id": document_id,
            "level": level,
            "num_questions": len(questions),
            "questions": [asdict(q) for q in questions],
        }

    # ── Review Candidates ─────────────────────────────────────────

    def get_review_candidates(
        self, user_id: str, document_id: str, today_str: str | None = None
    ) -> list[dict]:
        """Get review recommendations for a user.

        Returns list of knowledge points that need review.
        """
        from datetime import datetime

        if today_str is None:
            today_str = datetime.now().strftime("%Y-%m-%d")

        knowledge_points = self.load_knowledge_points(document_id)
        progress = self.load_progress(user_id, document_id)
        return self.planner.recommend_review(knowledge_points, progress, today_str)

    # ── User Progress ─────────────────────────────────────────────

    def get_user_progress(self, user_id: str, document_id: str) -> dict:
        """Get user's mastery progress summary."""
        progress = self.load_progress(user_id, document_id)
        return {
            "user_id": user_id,
            "document_id": document_id,
            "mastery_records": {
                kp_id: asdict(record) for kp_id, record in progress.items()
            },
        }
