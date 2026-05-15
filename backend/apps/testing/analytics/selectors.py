
from __future__ import annotations

from django.db.models import (
    Avg,
    Case,
    Count,
    DurationField,
    ExpressionWrapper,
    F,
    FloatField,
    IntegerField,
    Max,
    Min,
    Q,
    Subquery,
    Value,
    When,
)
from django.db.models.functions import Coalesce


PASS_THRESHOLD = 75.0


def _duration_expr():
    return ExpressionWrapper(
        F("finished_at") - F("started_at"),
        output_field=DurationField(),
    )


def _to_seconds(td) -> float | None:
    if td is None:
        return None
    return round(td.total_seconds(), 1)



def get_sessions_for_selector():
    from apps.testing.models import TestSession, AttemptStatus

    return (
        TestSession.objects
        .select_related("test")
        .annotate(
            total_attempts=Count("attempts"),
            finished_attempts=Count(
                "attempts",
                filter=Q(attempts__status=AttemptStatus.FINISHED),
            ),
        )
        .order_by("-created_at")
    )



def get_session_ranking(session_id: str):
    from apps.testing.models import StudentAttempt, AttemptStatus

    qs = (
        StudentAttempt.objects
        .filter(session_id=session_id, status=AttemptStatus.FINISHED)
        .select_related("session__test")
        .annotate(duration=_duration_expr())
        .order_by("-score", "duration")
        .values(
            "id",
            "student_name",
            "score",
            "duration",
            "started_at",
            "finished_at",
            "status",
        )
    )

    rows = []
    for rank, row in enumerate(qs, start=1):
        rows.append(
            {
                "rank": rank,
                "attempt_id": row["id"],
                "student_name": row["student_name"],
                "score": row["score"],
                "duration_seconds": _to_seconds(row["duration"]),
                "started_at": row["started_at"],
                "finished_at": row["finished_at"],
            }
        )
    return rows



def get_session_kpis(session_id: str) -> dict:
    from apps.testing.models import (
        StudentAttempt,
        TestSession,
        AttemptStatus,
    )

    try:
        session = (
            TestSession.objects
            .select_related("test")
            .get(pk=session_id)
        )
    except TestSession.DoesNotExist:
        return {}

    total_questions = session.test.questions.count()

    base_qs = StudentAttempt.objects.filter(session_id=session_id)

    agg = base_qs.aggregate(
        total_count=Count("id"),
        active_count=Count("id", filter=Q(status=AttemptStatus.ACTIVE)),
        finished_count=Count("id", filter=Q(status=AttemptStatus.FINISHED)),
        expired_count=Count("id", filter=Q(status=AttemptStatus.EXPIRED)),
        passed_count=Count(
            "id",
            filter=Q(
                status=AttemptStatus.FINISHED,
                score__gte=PASS_THRESHOLD,
            ),
        ),
        failed_count=Count(
            "id",
            filter=Q(
                status=AttemptStatus.FINISHED,
                score__lt=PASS_THRESHOLD,
            ),
        ),
        avg_score=Avg(
            "score", filter=Q(status=AttemptStatus.FINISHED)
        ),
        max_score=Max(
            "score", filter=Q(status=AttemptStatus.FINISHED)
        ),
        min_score=Min(
            "score", filter=Q(status=AttemptStatus.FINISHED)
        ),
        avg_duration=Avg(
            ExpressionWrapper(
                F("finished_at") - F("started_at"),
                output_field=DurationField(),
            ),
            filter=Q(
                status=AttemptStatus.FINISHED,
                finished_at__isnull=False,
            ),
        ),
    )

    finished = agg["finished_count"] or 0
    total = agg["total_count"] or 0
    completion_rate = round(finished / total * 100, 1) if total > 0 else 0.0

    avg_dur_secs = None
    if agg["avg_duration"]:
        avg_dur_secs = int(agg["avg_duration"].total_seconds())

    return {
        "session_id": str(session.id),
        "session_key": session.key,
        "session_title": session.title or session.key,
        "session_type": session.session_type,
        "session_type_display": session.get_session_type_display(),
        "test_title": session.test.title,
        "expires_at": session.expires_at,
        "is_active": session.is_active,
        "created_at": session.created_at,
        "total_questions": total_questions,
        "total_count": total,
        "active_count": agg["active_count"] or 0,
        "finished_count": finished,
        "expired_count": agg["expired_count"] or 0,
        "avg_score": round(agg["avg_score"] or 0, 1),
        "max_score": round(agg["max_score"] or 0, 1),
        "min_score": round(agg["min_score"] or 0, 1),
        "passed_count": agg["passed_count"] or 0,
        "failed_count": agg["failed_count"] or 0,
        "pass_threshold": PASS_THRESHOLD,
        "completion_rate": completion_rate,
        "avg_duration_seconds": avg_dur_secs,
    }



def get_question_breakdown(session_id: str) -> list[dict]:
    from apps.testing.models import Answer, Question

    from apps.testing.models import TestSession
    try:
        test_id = TestSession.objects.values_list("test_id", flat=True).get(pk=session_id)
    except TestSession.DoesNotExist:
        return []

    rows = (
        Answer.objects
        .filter(attempt__session_id=session_id)
        .values(
            "question_id",
            "question__text",
            "question__question_type",
            "question__difficulty",
            "question__order",
        )
        .annotate(
            total_answers=Count("id"),
            correct_answers=Count("id", filter=Q(is_correct=True)),
            incorrect_answers=Count("id", filter=Q(is_correct=False)),
            pending_answers=Count("id", filter=Q(is_correct__isnull=True)),
        )
        .order_by("question__order", "question__created_at")
    )

    result = []
    for r in rows:
        total = r["total_answers"] or 1
        correct_rate = round(r["correct_answers"] / total * 100, 1)
        result.append(
            {
                "question_id": r["question_id"],
                "question_text": r["question__text"][:80],
                "question_type": r["question__question_type"],
                "difficulty": r["question__difficulty"],
                "total_answers": r["total_answers"],
                "correct_answers": r["correct_answers"],
                "incorrect_answers": r["incorrect_answers"],
                "pending_answers": r["pending_answers"],
                "correct_rate": correct_rate,
            }
        )
    return result