from __future__ import annotations

import logging
from collections import defaultdict
from typing import Any

from django.core.exceptions import ValidationError

logger = logging.getLogger(__name__)

# ── Types ─────────────────────────────────────────────────────────────────────

OptionDict  = dict[str, str]           # {"id": "...", "text": "..."}
MistakeDict = dict[str, Any]
ReviewDict  = dict[str, Any]

# Minimum AI score (0–10) to count as "correct" for text/code
AI_PASS_THRESHOLD = 6.0

# ── Private helpers ────────────────────────────────────────────────────────────


def _accuracy(correct: int, total: int) -> float | None:
    """Return percentage or None if no data."""
    if total == 0:
        return None
    return round(correct / total * 100, 1)


def _fmt_option(opt) -> OptionDict:
    return {"id": str(opt.id), "text": opt.text}


def _selected_option_dicts(answer, all_options: list) -> list[OptionDict]:
    """
    Map answer.selected_options (list of UUID strings) back to option objects.
    all_options is the prefetched list for the question — no extra query.
    """
    selected_ids = {str(uid) for uid in (answer.selected_options or [])}
    return [_fmt_option(o) for o in all_options if str(o.id) in selected_ids]


def _correct_option_dicts(all_options: list) -> list[OptionDict]:
    return [_fmt_option(o) for o in all_options if o.is_correct]


def _build_explanation(question_type: str, is_correct: bool | None) -> str:
    """
    Generate a short human-readable explanation.
    In production you'd pull this from the Question.metadata field or AI.
    """
    if is_correct:
        return ""
    templates = {
        "single_choice":   "The selected option is incorrect. Review the correct answer above.",
        "multiple_choice": "One or more selected options are wrong, or a correct option was missed.",
        "text":            "The text answer did not fully meet the expected criteria.",
        "code":            "The code solution does not correctly solve the task.",
    }
    return templates.get(question_type, "The answer was marked incorrect.")


# ── Core service ───────────────────────────────────────────────────────────────


class AttemptReviewService:
    """
    Orchestrates collection of all data needed for the attempt review endpoint.

    Usage:
        data = AttemptReviewService.build_review(attempt_id)
        # data is a plain dict ready to pass to AttemptReviewSerializer

    DB round-trips: 2
      1. StudentAttempt + session + test
      2. Answer queryset with select_related(question) + prefetch_related(question__options)
    """

    @staticmethod
    def build_review(attempt_id: str) -> ReviewDict:
        """
        Main entry point.  Returns a dict that matches AttemptReviewSerializer.

        Raises django.core.exceptions.ValidationError on bad attempt_id or
        if the attempt has not been finished yet.
        """
        from apps.testing.models import StudentAttempt, AttemptStatus

        # ── Round-trip 1: attempt meta ────────────────────────────────────────
        try:
            attempt = (
                StudentAttempt.objects
                .select_related("session__test")
                .get(pk=attempt_id)
            )
        except StudentAttempt.DoesNotExist:
            raise ValidationError(f"Attempt {attempt_id} not found.")

        if attempt.status not in (AttemptStatus.FINISHED, AttemptStatus.EXPIRED):
            raise ValidationError("Review is only available for finished or expired attempts.")

        # ── Round-trip 2: answers with all related data ───────────────────────
        answers = list(
            attempt.answers
            .select_related("question")
            .prefetch_related("question__options")
            .order_by("answered_at")
        )

        mistakes      = AttemptReviewService._collect_mistakes(answers)
        statistics    = AttemptReviewService._compute_statistics(answers)
        summary       = AttemptReviewService._build_summary(answers, mistakes)

        # Counters (over ALL answers, not just mistakes)
        correct_count = sum(1 for a in answers if a.is_correct is True)
        wrong_count   = sum(1 for a in answers if a.is_correct is False)
        total_graded  = correct_count + wrong_count
        success_rate  = _accuracy(correct_count, total_graded) or 0.0

        return {
            "attempt_id":       attempt.id,
            "student_name":     attempt.student_name,
            "test":             attempt.session.test.title,
            "score":            attempt.score,
            "correct_answers":  correct_count,
            "wrong_answers":    wrong_count,
            "success_rate":     success_rate,
            "duration_seconds": attempt.duration_seconds,
            "mistakes":         mistakes,
            "statistics":       statistics,
            "summary":          summary,
        }

    # ── Mistakes collection ───────────────────────────────────────────────────

    @staticmethod
    def _collect_mistakes(answers: list) -> list[MistakeDict]:
        """
        Build the mistakes list.

        An answer is included when answer.is_correct is False
        (per spec: "Ошибка считается если answer.is_correct is False").

        For choice questions: populate selected_options / correct_options.
        For text/code:        populate student_answer / expected_answer / ai_*.
        """
        mistakes: list[MistakeDict] = []

        for answer in answers:
            if answer.is_correct is not False:
                # Skip correct answers and pending (not graded yet)
                continue

            question    = answer.question
            all_options = list(question.options.all())   # already prefetched
            q_type      = question.question_type

            mistake: MistakeDict = {
                "question_id":   question.id,
                "question_type": q_type,
                "question":      question.text,
                "difficulty":    question.difficulty,
                "is_correct":    answer.is_correct,
                "answered_at":   answer.answered_at,

                # Shared AI / explanation fields
                "explanation":    _build_explanation(q_type, answer.is_correct),
                "ai_feedback":    answer.ai_feedback  or "",
                "ai_suggestion":  answer.ai_suggestion or "",

                # Defaults (overridden below by type)
                "selected_options": [],
                "correct_options":  [],
                "student_answer":   "",
                "expected_answer":  "",
                "ai_score":         None,
                "ai_confidence":    None,
            }

            if q_type in ("single_choice", "multiple_choice"):
                mistake["selected_options"] = _selected_option_dicts(answer, all_options)
                mistake["correct_options"]  = _correct_option_dicts(all_options)

            else:  # text / code
                # expected_answer: first correct option text (if stored), else empty
                expected = ""
                if all_options:
                    correct_opts = [o for o in all_options if o.is_correct]
                    if correct_opts:
                        expected = correct_opts[0].text

                mistake["student_answer"]  = answer.answer_text or ""
                mistake["expected_answer"] = expected
                mistake["ai_score"]        = answer.ai_score
                mistake["ai_confidence"]   = answer.ai_confidence

            mistakes.append(mistake)

        return mistakes

    # ── Statistics computation ────────────────────────────────────────────────

    @staticmethod
    def _compute_statistics(answers: list) -> dict:
        """
        Per-type accuracy + additional analytics — all in Python,
        zero extra DB queries (data already in `answers`).
        """
        type_buckets: dict[str, dict] = defaultdict(lambda: {"correct": 0, "total": 0})
        ai_scores: list[float]        = []

        # Per-question mistake counter (question_id → wrong count)
        question_wrong: dict[str, dict] = {}

        for a in answers:
            q_type = a.question.question_type

            if a.is_correct is not None:
                type_buckets[q_type]["total"] += 1
                if a.is_correct:
                    type_buckets[q_type]["correct"] += 1

            if a.ai_score is not None:
                ai_scores.append(a.ai_score)

            # Track most-failed questions
            qid = str(a.question.id)
            if qid not in question_wrong:
                question_wrong[qid] = {
                    "question_id":   qid,
                    "question_text": a.question.text[:80],
                    "question_type": a.question.question_type,
                    "wrong_count":   0,
                    "total":         0,
                }
            question_wrong[qid]["total"] += 1
            if a.is_correct is False:
                question_wrong[qid]["wrong_count"] += 1

        def _acc(q_type: str) -> float | None:
            b = type_buckets.get(q_type)
            if not b:
                return None
            return _accuracy(b["correct"], b["total"])

        # Most-failed: questions where wrong_count > 0, sorted by fail count
        failed_qs = sorted(
            [q for q in question_wrong.values() if q["wrong_count"] > 0],
            key=lambda x: x["wrong_count"],
            reverse=True,
        )

        avg_ai = round(sum(ai_scores) / len(ai_scores), 2) if ai_scores else None

        # Mistake breakdown by question type
        mistake_by_type: dict[str, int] = {
            qt: b["total"] - b["correct"]
            for qt, b in type_buckets.items()
        }

        return {
            "single_choice_accuracy":   _acc("single_choice"),
            "multiple_choice_accuracy": _acc("multiple_choice"),
            "code_accuracy":            _acc("code"),
            "text_accuracy":            _acc("text"),
            "hardest_questions":        failed_qs[:5],   # top-5 most missed
            "most_failed":              failed_qs[:3],
            "avg_ai_score":             avg_ai,
            "mistake_by_type":          mistake_by_type,
        }

    # ── Summary builder ───────────────────────────────────────────────────────

    @staticmethod
    def _build_summary(answers: list, mistakes: list[MistakeDict]) -> dict:
        """
        Derive strong/weak topics and recommended focus from answers.

        "Topics" are approximated by question_type here.
        In a richer schema you'd use question.metadata['topic'].
        """
        from apps.testing.models import QuestionType

        TYPE_LABELS = {
            QuestionType.SINGLE_CHOICE:   "Multiple Choice",
            QuestionType.MULTIPLE_CHOICE: "Multiple Select",
            QuestionType.TEXT:            "Text Answers",
            QuestionType.CODE:            "Coding Tasks",
        }

        FOCUS_HINTS = {
            QuestionType.SINGLE_CHOICE:   "Review theoretical concepts and definitions.",
            QuestionType.MULTIPLE_CHOICE: "Practice identifying all correct options.",
            QuestionType.TEXT:            "Write more detailed and precise answers.",
            QuestionType.CODE:            "Solve more coding exercises and review edge cases.",
        }

        type_buckets: dict[str, dict] = defaultdict(lambda: {"correct": 0, "total": 0})
        for a in answers:
            qt = a.question.question_type
            if a.is_correct is not None:
                type_buckets[qt]["total"] += 1
                if a.is_correct:
                    type_buckets[qt]["correct"] += 1

        strong: list[str] = []
        weak:   list[str] = []
        focus:  list[str] = []

        for qt, b in type_buckets.items():
            if b["total"] == 0:
                continue
            acc = b["correct"] / b["total"] * 100
            label = TYPE_LABELS.get(qt, qt)
            if acc >= 70:
                strong.append(label)
            else:
                weak.append(label)
                hint = FOCUS_HINTS.get(qt)
                if hint:
                    focus.append(hint)

        return {
            "strong_topics":     strong,
            "weak_topics":       weak,
            "recommended_focus": focus,
        }