from __future__ import annotations

from datetime import datetime, timedelta

from .models import KnowledgePoint, MasteryRecord


class Planner:
    """Recommends knowledge points for review based on Ebbinghaus
    forgetting curve and weak-point tracking."""

    def recommend_review(
        self,
        knowledge_points: list[KnowledgePoint],
        mastery_records: dict[str, MasteryRecord],
        today_str: str,
    ) -> list[dict]:
        """Return a list of review recommendations.

        Combines:
        1. Knowledge points due for review (next_review_at <= today)
        2. Weak knowledge points reviewed in the last 3 days

        Returns:
            List of dicts with 'knowledge_point_id', 'title', 'reason',
            'current_level', 'is_weak'.
        """
        today = datetime.strptime(today_str, "%Y-%m-%d")
        three_days_ago_str = (today - timedelta(days=3)).strftime("%Y-%m-%d")

        # Build a title lookup
        kp_title_map = {kp.id: kp.title for kp in knowledge_points}

        seen_ids: set[str] = set()
        recommendations: list[dict] = []

        for kp_id, record in mastery_records.items():
            reasons: list[str] = []

            # Check Ebbinghaus due
            if record.next_review_at and record.next_review_at <= today_str:
                reasons.append("遗忘曲线到期，需要复习")

            # Check weak + recently reviewed
            if record.is_weak and record.last_reviewed_at:
                if record.last_reviewed_at >= three_days_ago_str:
                    reasons.append("薄弱知识点，最近3天内有练习记录")
                elif not record.next_review_at:
                    # Weak but no review schedule yet
                    reasons.append("薄弱知识点，建议复习")

            if reasons and kp_id not in seen_ids:
                seen_ids.add(kp_id)
                recommendations.append({
                    "knowledge_point_id": kp_id,
                    "title": kp_title_map.get(kp_id, kp_id),
                    "reason": "；".join(reasons),
                    "current_level": record.current_level,
                    "is_weak": record.is_weak,
                })

        return recommendations
