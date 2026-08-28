from __future__ import annotations

from datetime import datetime, timedelta

from .models import MasteryRecord, Question, AnswerResult


# Ebbinghaus forgetting curve intervals in days
REVIEW_INTERVALS = [1, 2, 4, 7, 15]

# Maximum accuracy history entries to keep
MAX_ACCURACY_HISTORY = 10


class MasteryEngine:
    """Tracks mastery level, weak points, and spaced repetition schedule."""

    def update_mastery(
        self,
        existing_records: dict[str, MasteryRecord],
        questions: list[Question],
        results: list[AnswerResult],
    ) -> dict[str, MasteryRecord]:
        """Update mastery records based on quiz results.

        - Correct answer at current level → level up (max 3)
        - Wrong answer → level down (min 1)
        - First time → forced to level 1
        - Weak marking: accuracy < 0.5 or 2 consecutive wrong → is_weak = True
        - Strong recovery: accuracy >= 0.8 for 2 consecutive → is_weak = False
        - Updates Ebbinghaus review schedule
        """
        question_map = {q.id: q for q in questions}
        now_str = datetime.now().strftime("%Y-%m-%d")

        # Group results by knowledge point
        kp_scores: dict[str, list[float]] = {}
        for r in results:
            q = question_map.get(r.question_id)
            if q is None:
                continue
            # Skip short_answer that needs review (score is None)
            if r.score is None:
                continue
            for kp_id in q.knowledge_point_ids:
                if kp_id not in kp_scores:
                    kp_scores[kp_id] = []
                kp_scores[kp_id].append(r.score)

        for kp_id, scores in kp_scores.items():
            record = existing_records.get(kp_id)
            if record is None:
                record = MasteryRecord(knowledge_point_id=kp_id, current_level=1)
                existing_records[kp_id] = record

            accuracy = sum(scores) / len(scores) if scores else 0.0

            # Update basic stats
            record.attempts += 1
            record.last_accuracy = accuracy
            record.best_accuracy = max(record.best_accuracy, accuracy)
            record.last_reviewed_at = now_str

            # Update accuracy history (keep last 10)
            record.accuracy_history.append(accuracy)
            if len(record.accuracy_history) > MAX_ACCURACY_HISTORY:
                record.accuracy_history = record.accuracy_history[-MAX_ACCURACY_HISTORY:]

            # Update level: correct → up, wrong → down
            is_correct = accuracy >= 0.6  # threshold for "correct" at current level
            if is_correct:
                record.current_level = min(record.current_level + 1, 3)
            else:
                record.current_level = max(record.current_level - 1, 1)

            # Update weak status
            self._update_weak_status(record)

            # Update Ebbinghaus review schedule
            self._update_review_schedule(record, is_correct, now_str)

        return existing_records

    def _update_weak_status(self, record: MasteryRecord) -> None:
        """Mark or unmark a knowledge point as weak.

        Weak if: accuracy < 0.5 OR last 2 attempts both wrong
        Recover if: accuracy >= 0.8 for last 2 consecutive attempts
        """
        history = record.accuracy_history

        # Check for consecutive failures (last 2 both < 0.6)
        if len(history) >= 2 and history[-1] < 0.6 and history[-2] < 0.6:
            record.is_weak = True
            return

        # Check overall recent accuracy
        if record.last_accuracy < 0.5:
            record.is_weak = True
            return

        # Check for recovery: last 2 both >= 0.8
        if len(history) >= 2 and history[-1] >= 0.8 and history[-2] >= 0.8:
            record.is_weak = False

    def _update_review_schedule(
        self, record: MasteryRecord, is_correct: bool, today_str: str
    ) -> None:
        """Update Ebbinghaus spaced repetition schedule.

        Correct → advance review_stage (max 4)
        Wrong → reset review_stage to 0
        """
        if is_correct:
            record.review_stage = min(record.review_stage + 1, len(REVIEW_INTERVALS) - 1)
        else:
            record.review_stage = 0

        interval_days = REVIEW_INTERVALS[record.review_stage]
        today = datetime.strptime(today_str, "%Y-%m-%d")
        next_review = today + timedelta(days=interval_days)
        record.next_review_at = next_review.strftime("%Y-%m-%d")

    def get_review_candidates(
        self,
        records: dict[str, MasteryRecord],
        today_str: str,
    ) -> list[str]:
        """Return knowledge point IDs that need review.

        Criteria:
        - next_review_at <= today (due for review)
        - is_weak=True and last_reviewed_at within last 3 days
        """
        candidates = set()
        today = datetime.strptime(today_str, "%Y-%m-%d")
        three_days_ago = (today - timedelta(days=3)).strftime("%Y-%m-%d")

        for kp_id, record in records.items():
            # Due for review based on Ebbinghaus schedule
            if record.next_review_at and record.next_review_at <= today_str:
                candidates.add(kp_id)

            # Weak and recently reviewed (within 3 days)
            if record.is_weak and record.last_reviewed_at:
                if record.last_reviewed_at >= three_days_ago:
                    candidates.add(kp_id)

        return list(candidates)
