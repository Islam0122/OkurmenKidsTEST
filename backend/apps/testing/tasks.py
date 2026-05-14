from __future__ import annotations

import logging

from celery import shared_task
from celery.exceptions import MaxRetriesExceededError

logger = logging.getLogger(__name__)


_MAX_RETRIES    = 3
_RETRY_BACKOFF  = 60          # seconds — doubles each retry (60 → 120 → 240)
_SOFT_TIME_LIMIT = 120        # seconds — Celery will raise SoftTimeLimitExceeded

# Telegram-specific
_TG_MAX_RETRIES   = 5
_TG_RETRY_BACKOFF = 30        # 30 → 60 → 120 → 240 → 480
_TG_SOFT_LIMIT    = 180       # 3 min — несколько сообщений могут занять время


# ══════════════════════════════════════════════════════════════════════════════
# СУЩЕСТВУЮЩИЕ ЗАДАЧИ (не изменены)
# ══════════════════════════════════════════════════════════════════════════════

@shared_task(
    bind=True,
    name="testing.grade_answer_task",
    max_retries=_MAX_RETRIES,
    soft_time_limit=_SOFT_TIME_LIMIT,
    acks_late=True,
    reject_on_worker_lost=True,
)
def grade_answer_task(self, answer_id: str) -> dict:
    """
    Async Celery task: call GigaChat AI to grade a text/code answer.

    Lifecycle:
      1. Mark Answer.grading_status = 'processing'
      2. Call ai_grader.grade_answer(answer_id)
      3a. On success → persist GradeResult fields, set status = 'done'
      3b. On retriable failure → retry with back-off
      3c. On final failure → set status = 'failed'
    """
    from apps.testing.models import Answer, GradingStatus
    from apps.testing.services.ai_grader import grade_answer

    logger.info(
        "[grade_answer_task] Starting for answer_id=%s (attempt %d/%d)",
        answer_id, self.request.retries + 1, _MAX_RETRIES + 1,
    )

    try:
        answer = Answer.objects.select_related("question", "attempt").get(pk=answer_id)
    except Answer.DoesNotExist:
        logger.error("[grade_answer_task] Answer %s not found — aborting.", answer_id)
        return {"status": "not_found", "answer_id": answer_id}

    if answer.grading_status == GradingStatus.DONE:
        logger.info("[grade_answer_task] Answer %s already graded — skipping.", answer_id)
        return {"status": "already_done", "answer_id": answer_id}

    answer.grading_status = GradingStatus.PROCESSING
    answer.save(update_fields=["grading_status"])

    try:
        result = grade_answer(answer_id)
    except Exception as exc:
        logger.exception("[grade_answer_task] Unexpected error for answer %s: %s", answer_id, exc)
        result = None

    if result is not None:
        try:
            _persist_grade(answer, result)
            logger.info(
                "[grade_answer_task] Done: answer=%s score=%.1f is_correct=%s",
                answer_id, result.score, result.is_correct,
            )
            return {
                "status":     "done",
                "answer_id":  answer_id,
                "score":      result.score,
                "is_correct": result.is_correct,
            }
        except Exception as exc:
            logger.exception(
                "[grade_answer_task] Failed to persist result for %s: %s", answer_id, exc,
            )

    try:
        backoff = _RETRY_BACKOFF * (2 ** self.request.retries)
        logger.warning(
            "[grade_answer_task] Retrying answer %s in %ds (retry %d/%d).",
            answer_id, backoff, self.request.retries + 1, _MAX_RETRIES,
        )
        Answer.objects.filter(pk=answer_id).update(grading_status=GradingStatus.PENDING)
        raise self.retry(countdown=backoff)
    except MaxRetriesExceededError:
        logger.error(
            "[grade_answer_task] Max retries exceeded for answer %s — marking failed.",
            answer_id,
        )
        Answer.objects.filter(pk=answer_id).update(
            grading_status=GradingStatus.FAILED,
            ai_feedback="AI grading failed after multiple attempts. Awaiting manual review.",
        )
        return {"status": "failed", "answer_id": answer_id}


@shared_task(name="testing.regrade_pending_answers_task")
def regrade_pending_answers_task() -> dict:
    """
    Periodic task: re-enqueue any answers stuck in 'pending' or 'failed' state.
    """
    from apps.testing.models import Answer, GradingStatus, QuestionType

    stuck = Answer.objects.filter(
        grading_status__in=[GradingStatus.PENDING, GradingStatus.FAILED],
        question__question_type__in=[QuestionType.TEXT, QuestionType.CODE],
    ).values_list("id", flat=True)

    count = 0
    for answer_id in stuck:
        grade_answer_task.delay(str(answer_id))
        count += 1

    logger.info("[regrade_pending_answers_task] Enqueued %d answers for re-grading.", count)
    return {"enqueued": count}


@shared_task(name="testing.expire_stale_sessions_task")
def expire_stale_sessions_task() -> dict:
    """
    Переводит просроченные exam-сессии в status='finished', is_active=False.
    Запускать каждые 5 минут через Celery Beat.

    После деактивации автоматически запускает Telegram-отчёт
    для каждой завершённой сессии.
    """
    from django.utils import timezone
    from apps.testing.models import TestSession, SessionStatus, SessionType, StudentAttempt, AttemptStatus

    now = timezone.now()

    stale = list(
        TestSession.objects.filter(
            session_type=SessionType.EXAM,
            is_active=True,
            expires_at__lt=now,
        ).exclude(status=SessionStatus.FINISHED)
        .values_list("id", flat=True)
    )

    count = len(stale)

    if stale:
        TestSession.objects.filter(id__in=stale).update(
            status=SessionStatus.FINISHED,
            is_active=False,
        )
        StudentAttempt.objects.filter(
            session_id__in=stale,
            status=AttemptStatus.ACTIVE,
        ).update(status=AttemptStatus.EXPIRED)

        # Запускаем Telegram-отчёт для каждой завершённой сессии
        for session_id in stale:
            try:
                send_session_report_task.apply_async(
                    args=[str(session_id)],
                    countdown=10,  # небольшая задержка чтобы БД успела зафиксировать изменения
                )
                logger.info(
                    "[expire_stale_sessions_task] Scheduled Telegram report for session %s.",
                    session_id,
                )
            except Exception as exc:
                logger.error(
                    "[expire_stale_sessions_task] Failed to schedule report for session %s: %s",
                    session_id, exc,
                )

    logger.info("[expire_stale_sessions_task] Expired %d sessions.", count)
    return {"expired_sessions": count}


def _persist_grade(answer, result) -> None:
    from .models import GradingStatus

    answer.is_correct      = result.is_correct
    answer.ai_score        = result.score
    answer.ai_confidence   = result.confidence
    answer.ai_feedback     = result.feedback
    answer.ai_suggestion   = result.suggestion
    answer.grading_status  = GradingStatus.DONE

    answer.save(update_fields=[
        "is_correct",
        "ai_score",
        "ai_confidence",
        "ai_feedback",
        "ai_suggestion",
        "grading_status",
    ])

    attempt = answer.attempt
    attempt._recalculate_score()
    attempt.save(update_fields=["score"])


# ══════════════════════════════════════════════════════════════════════════════
# НОВАЯ ЗАДАЧА: Telegram Report
# ══════════════════════════════════════════════════════════════════════════════

@shared_task(
    bind=True,
    name="testing.send_session_report_task",
    max_retries=_TG_MAX_RETRIES,
    soft_time_limit=_TG_SOFT_LIMIT,
    acks_late=True,
    reject_on_worker_lost=True,
    # Автоматический retry при HTTP-ошибках и RuntimeError (Telegram API errors)
    autoretry_for=(Exception,),
    retry_backoff=True,           # exponential backoff (Celery built-in)
    retry_backoff_max=600,        # не более 10 минут между попытками
    retry_jitter=True,            # случайный jitter чтобы избежать thundering herd
    dont_autoretry_for=(),        # пустой — autoretry для всех Exception
)
def send_session_report_task(self, session_id: str) -> dict:
    """
    Celery task: сформировать и отправить Telegram-отчёт по сессии.

    Запускается автоматически:
    - из expire_stale_sessions_task (деактивация по времени)
    - из TestSession.deactivate() через сигнал (post_save)
    - вручную: send_session_report_task.delay(session_id)

    Retry policy:
    - max_retries = 5
    - exponential backoff с jitter
    - autoretry_for=Exception — retry при любой ошибке

    Если отправка отключена (SEND_TELEGRAM_REPORTS=False / пустые credentials) —
    задача завершается немедленно без ошибки.
    """
    logger.info(
        "[send_session_report_task] Starting. session_id=%s attempt=%d/%d",
        session_id,
        self.request.retries + 1,
        _TG_MAX_RETRIES + 1,
    )

    try:
        from apps.testing.services.telegram_reports import TelegramReportService
        result = TelegramReportService.send_report(session_id)
    except Exception as exc:
        logger.error(
            "[send_session_report_task] Error for session_id=%s: %s. "
            "Retry %d/%d.",
            session_id, exc,
            self.request.retries + 1,
            _TG_MAX_RETRIES,
        )
        raise  # autoretry перехватит и выполнит retry

    logger.info(
        "[send_session_report_task] Completed. session_id=%s status=%s "
        "messages_sent=%s",
        session_id,
        result.get("status"),
        result.get("messages_sent", 0),
    )
    return result