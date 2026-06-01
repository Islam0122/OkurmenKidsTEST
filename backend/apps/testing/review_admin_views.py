from __future__ import annotations

import json
import logging
from datetime import date, timedelta

from django.contrib import messages
from django.contrib.admin import site as _admin_site
from django.contrib.admin.views.decorators import staff_member_required
from django.db import transaction
from django.db.models import Avg, Count, DurationField, ExpressionWrapper, F, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

logger = logging.getLogger(__name__)

# ── Helpers ───────────────────────────────────────────────────────────────────

class _FakeOpts:
    app_label = "testing"
    model_name = "manualreview"
    verbose_name = "Ручная проверка"
    verbose_name_plural = "Ручная проверка"


def _recalculate_attempt_score(attempt) -> None:
    """Re-run score calculation and save. Mirrors StudentAttempt._recalculate_score()."""
    from apps.testing.services.question_selector import TOTAL_QUESTIONS
    answers = list(attempt.answers.all())
    gradable = [a for a in answers if a.is_correct is not None]
    if not gradable:
        attempt.score = 0.0
    else:
        correct = sum(1 for a in gradable if a.is_correct)
        attempt.score = round((correct / TOTAL_QUESTIONS) * 100, 2)
    attempt.save(update_fields=["score"])


# ── Dashboard ─────────────────────────────────────────────────────────────────

@staff_member_required
def review_dashboard_view(request):
    from apps.testing.models import Answer, StudentAttempt, TestSession, GradingStatus

    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # Pending answers (text + code only)
    pending_qs = Answer.objects.filter(
        grading_status=GradingStatus.PENDING,
        question__question_type__in=["text", "code"],
    )
    pending_count = pending_qs.count()

    # Reviewed today (manual grading today)
    reviewed_today = Answer.objects.filter(
        grading_status=GradingStatus.MANUAL,
        answered_at__gte=today_start,
    ).count()

    # Active exams right now
    active_exams = TestSession.objects.filter(
        is_active=True,
        expires_at__gt=now,
        session_type="exam",
    ).count()

    # Students currently on tests (active attempts)
    from apps.testing.models import AttemptStatus
    students_online = StudentAttempt.objects.filter(
        status=AttemptStatus.ACTIVE,
    ).count()

    # Pending by test for the breakdown table
    pending_by_test = (
        pending_qs
        .values("attempt__session__test__title")
        .annotate(cnt=Count("id"))
        .order_by("-cnt")[:10]
    )

    # Recent manual graded answers (last 20)
    recent_graded = (
        Answer.objects
        .filter(grading_status=GradingStatus.MANUAL)
        .select_related("attempt", "question", "attempt__session__test")
        .order_by("-answered_at")[:20]
    )

    # Average estimated review time (manual answers only, in seconds)
    # We approximate as avg time between answered_at and now for today's batch
    avg_review_time = None  # We don't track explicit review timestamps — show "—"

    ctx = {
        **_admin_site.each_context(request),
        "title": "Дашборд преподавателя",
        "opts": _FakeOpts(),
        "pending_count": pending_count,
        "reviewed_today": reviewed_today,
        "active_exams": active_exams,
        "students_online": students_online,
        "avg_review_time": avg_review_time,
        "pending_by_test": list(pending_by_test),
        "recent_graded": recent_graded,
        "now": now,
    }
    return render(request, "admin/testing/review_dashboard.html", ctx)


# ── Manual Review List ────────────────────────────────────────────────────────

@staff_member_required
def review_list_view(request):
    from apps.testing.models import Answer, GradingStatus, QuestionType

    # Filters from GET
    filter_type = request.GET.get("type", "")       # "text" | "code" | ""
    filter_status = request.GET.get("status", "pending")   # "pending" | "manual" | "done" | ""
    search_q = request.GET.get("q", "").strip()

    # Base queryset: only text/code, pending for manual review
    qs = (
        Answer.objects
        .filter(
            question__question_type__in=[QuestionType.TEXT, QuestionType.CODE],
        )
        .select_related(
            "attempt",
            "attempt__session",
            "attempt__session__test",
            "question",
        )
        .order_by("-answered_at")
    )

    # Status filter
    if filter_status == "pending":
        qs = qs.filter(grading_status=GradingStatus.PENDING)
    elif filter_status == "manual":
        qs = qs.filter(grading_status=GradingStatus.MANUAL)
    elif filter_status == "done":
        qs = qs.filter(grading_status=GradingStatus.DONE)
    elif filter_status == "failed":
        qs = qs.filter(grading_status=GradingStatus.FAILED)

    # Type filter
    if filter_type in ("text", "code"):
        qs = qs.filter(question__question_type=filter_type)

    # Search
    if search_q:
        qs = qs.filter(
            Q(attempt__student_name__icontains=search_q)
            | Q(question__text__icontains=search_q)
            | Q(attempt__session__test__title__icontains=search_q)
            | Q(attempt__session__title__icontains=search_q)
        )

    # Count totals for the status pills
    from apps.testing.models import QuestionType as QT
    base_text_code = Answer.objects.filter(
        question__question_type__in=[QT.TEXT, QT.CODE],
    )
    counts = base_text_code.aggregate(
        pending=Count("id", filter=Q(grading_status=GradingStatus.PENDING)),
        manual=Count("id", filter=Q(grading_status=GradingStatus.MANUAL)),
        done=Count("id", filter=Q(grading_status=GradingStatus.DONE)),
        failed=Count("id", filter=Q(grading_status=GradingStatus.FAILED)),
    )

    ctx = {
        **_admin_site.each_context(request),
        "title": "Ручная проверка",
        "opts": _FakeOpts(),
        "answers": qs[:200],
        "filter_type": filter_type,
        "filter_status": filter_status,
        "search_q": search_q,
        "counts": counts,
    }
    return render(request, "admin/testing/review_list.html", ctx)


# ── Detail Review ─────────────────────────────────────────────────────────────

@staff_member_required
def review_detail_view(request, answer_id):
    from apps.testing.models import Answer, GradingStatus

    answer = get_object_or_404(
        Answer.objects
        .select_related(
            "attempt",
            "attempt__session",
            "attempt__session__test",
            "question",
        ),
        pk=answer_id,
    )

    # Find next pending answer for fast navigation
    next_pending = (
        Answer.objects
        .filter(
            grading_status=GradingStatus.PENDING,
            question__question_type__in=["text", "code"],
            answered_at__lt=answer.answered_at,
        )
        .select_related("attempt", "question")
        .order_by("-answered_at")
        .first()
    )

    # Sibling answers from the same attempt for context
    sibling_answers = (
        Answer.objects
        .filter(attempt=answer.attempt)
        .select_related("question")
        .order_by("answered_at")
    )

    ctx = {
        **_admin_site.each_context(request),
        "title": f"Проверка ответа — {answer.attempt.student_name}",
        "opts": _FakeOpts(),
        "answer": answer,
        "next_pending": next_pending,
        "sibling_answers": sibling_answers,
        "question": answer.question,
        "attempt": answer.attempt,
        "session": answer.attempt.session,
        "test": answer.attempt.session.test,
    }
    return render(request, "admin/testing/review_detail.html", ctx)


# ── Grade (from detail page) ──────────────────────────────────────────────────

@staff_member_required
@require_POST
def review_grade_view(request, answer_id):
    from apps.testing.models import Answer, GradingStatus

    answer = get_object_or_404(Answer, pk=answer_id)
    verdict = request.POST.get("verdict")  # "correct" | "incorrect"

    if verdict not in ("correct", "incorrect"):
        messages.error(request, "Неверное значение вердикта.")
        return redirect("admin:testing_manual_review_detail", answer_id=answer_id)

    is_correct = verdict == "correct"

    with transaction.atomic():
        answer.is_correct = is_correct
        answer.grading_status = GradingStatus.MANUAL
        answer.save(update_fields=["is_correct", "grading_status"])
        _recalculate_attempt_score(answer.attempt)

    msg = "✅ Засчитан" if is_correct else "❌ Не засчитан"
    messages.success(
        request,
        f"{msg}: {answer.attempt.student_name} — «{answer.question.text[:60]}»",
    )

    # After grading, go to next pending or back to list
    next_pending = (
        Answer.objects
        .filter(
            grading_status=GradingStatus.PENDING,
            question__question_type__in=["text", "code"],
        )
        .order_by("-answered_at")
        .first()
    )
    if next_pending:
        return redirect("admin:testing_manual_review_detail", answer_id=next_pending.pk)
    return redirect("admin:testing_manual_review_list")


# ── Quick Grade (AJAX from list) ──────────────────────────────────────────────

@staff_member_required
@require_POST
def review_quick_grade_view(request):
    """
    POST /admin/testing/manual-review/quick-grade/
    Body: answer_id, verdict ("correct" | "incorrect")
    Returns JSON.
    """
    from apps.testing.models import Answer, GradingStatus

    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, AttributeError):
        data = request.POST

    answer_id = data.get("answer_id")
    verdict = data.get("verdict")

    if not answer_id or verdict not in ("correct", "incorrect"):
        return JsonResponse({"ok": False, "error": "Invalid params"}, status=400)

    try:
        answer = Answer.objects.select_related("attempt", "question").get(pk=answer_id)
    except Answer.DoesNotExist:
        return JsonResponse({"ok": False, "error": "Answer not found"}, status=404)

    is_correct = verdict == "correct"

    with transaction.atomic():
        answer.is_correct = is_correct
        answer.grading_status = GradingStatus.MANUAL
        answer.save(update_fields=["is_correct", "grading_status"])
        _recalculate_attempt_score(answer.attempt)

    return JsonResponse({
        "ok": True,
        "answer_id": str(answer.pk),
        "is_correct": is_correct,
        "new_score": answer.attempt.score,
        "student_name": answer.attempt.student_name,
    })


# ── Bulk Grade (admin action endpoint) ────────────────────────────────────────

@staff_member_required
@require_POST
def review_bulk_grade_view(request):
    """
    POST /admin/testing/manual-review/bulk-grade/
    Body form: answer_ids (comma-separated UUIDs), verdict
    """
    from apps.testing.models import Answer, GradingStatus

    verdict = request.POST.get("verdict")
    raw_ids = request.POST.get("answer_ids", "")
    answer_ids = [x.strip() for x in raw_ids.split(",") if x.strip()]

    if verdict not in ("correct", "incorrect") or not answer_ids:
        messages.error(request, "Неверные параметры запроса.")
        return redirect("admin:testing_manual_review_list")

    is_correct = verdict == "correct"

    answers = (
        Answer.objects
        .filter(pk__in=answer_ids)
        .select_related("attempt")
    )

    attempt_ids_to_recalc = set()
    updated = 0
    with transaction.atomic():
        for answer in answers:
            answer.is_correct = is_correct
            answer.grading_status = GradingStatus.MANUAL
            answer.save(update_fields=["is_correct", "grading_status"])
            attempt_ids_to_recalc.add(answer.attempt_id)
            updated += 1

        # Recalculate scores for affected attempts
        from apps.testing.models import StudentAttempt
        for attempt in StudentAttempt.objects.filter(pk__in=attempt_ids_to_recalc):
            _recalculate_attempt_score(attempt)

    label = "Засчитаны" if is_correct else "Не засчитаны"
    messages.success(request, f"{label}: {updated} ответов. Баллы пересчитаны.")
    return redirect("admin:testing_manual_review_list")