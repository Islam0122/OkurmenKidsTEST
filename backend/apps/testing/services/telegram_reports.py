from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from typing import Optional

import httpx
from django.conf import settings
from django.db.models import (
    Avg,
    Case,
    Count,
    DurationField,
    ExpressionWrapper,
    F,
    FloatField,
    Q,
    When,
)
from django.utils import timezone

logger = logging.getLogger(__name__)


TELEGRAM_API_BASE = "https://api.telegram.org/bot{token}/sendMessage"
MESSAGE_LIMIT = 4000
PASS_THRESHOLD = 75.0
TOP_STUDENTS_COUNT = 3
LOW_KPI_THRESHOLD = 60.0
HTTP_TIMEOUT = 15

QUESTION_TYPE_LABELS: dict[str, str] = {
    "single_choice":   "Single Choice",
    "multiple_choice": "Multiple Choice",
    "code":            "Code Questions",
    "text":            "Text Questions",
}



def _get_bot_token() -> str:
    return getattr(settings, "TELEGRAM_BOT_TOKEN", "") or ""


def _get_group_id() -> str:
    return getattr(settings, "TELEGRAM_GROUP_ID", "") or ""


def _reports_enabled() -> bool:
    if not getattr(settings, "SEND_TELEGRAM_REPORTS", True):
        return False
    if not _get_bot_token():
        return False
    if not _get_group_id():
        return False
    return True



@dataclass
class QuestionTypeStats:
    question_type: str
    label: str
    total: int
    correct: int
    rate: float    # 0–100


@dataclass
class StudentStats:
    student_name: str
    status: str
    status_display: str
    score: float
    total_questions: int
    correct_answers: int
    wrong_answers: int
    ai_score: Optional[float]
    ai_confidence: Optional[float]
    started_at: Optional[object]
    finished_at: Optional[object]
    duration_seconds: Optional[float]
    question_type_breakdown: list[QuestionTypeStats] = field(default_factory=list)


@dataclass
class SessionReport:
    session_id: str
    session_title: str
    test_title: str
    group_label: str
    created_at: object
    duration_hours: Optional[float]

    total_students: int
    finished_count: int
    not_finished_count: int
    expired_count: int

    avg_kpi: float
    best_kpi: float
    worst_kpi: float
    pass_rate: float

    top_students: list[tuple[str, float]]     # [(name, score), ...]
    low_kpi_students: list[tuple[str, float]] # [(name, score), ...]

    question_type_stats: list[QuestionTypeStats]

    ai_total_checked: int
    ai_errors: int
    ai_manual_review: int
    ai_avg_score: Optional[float]

    active_attempts: int
    expired_attempts: int
    avg_duration_seconds: Optional[float]
    total_answers: int

    students: list[StudentStats]


class _SessionStatsCollector:
    def __init__(self, session_id: str) -> None:
        self.session_id = session_id

    def collect(self) -> SessionReport:
        from apps.testing.models import (
            TestSession, StudentAttempt, Answer,
            AttemptStatus, GradingStatus, QuestionType,
        )

        session = (
            TestSession.objects
            .select_related("test")
            .get(pk=self.session_id)
        )
        test = session.test
        total_questions = test.questions.count()

        # Длительность сессии (с момента создания до now/expires_at)
        end_time = min(timezone.now(), session.expires_at) if session.expires_at else timezone.now()
        duration_hours = (end_time - session.created_at).total_seconds() / 3600

        # ── Round-trip 2: attempt-level aggregations ───────────────────────
        base_qs = StudentAttempt.objects.filter(session_id=self.session_id)

        agg = base_qs.aggregate(
            total=Count("id"),
            finished=Count("id", filter=Q(status=AttemptStatus.FINISHED)),
            expired=Count("id", filter=Q(status=AttemptStatus.EXPIRED)),
            active=Count("id", filter=Q(status=AttemptStatus.ACTIVE)),
            avg_score=Avg("score", filter=Q(status=AttemptStatus.FINISHED)),
            best_score=Avg(
                Case(When(status=AttemptStatus.FINISHED, then=F("score")),
                     default=None, output_field=FloatField())
            ),
            avg_dur=Avg(
                ExpressionWrapper(
                    F("finished_at") - F("started_at"),
                    output_field=DurationField(),
                ),
                filter=Q(status=AttemptStatus.FINISHED, finished_at__isnull=False),
            ),
        )

        # best/worst score — нужны точные значения, а не avg
        from django.db.models import Max, Min
        minmax = base_qs.filter(status=AttemptStatus.FINISHED).aggregate(
            best=Max("score"), worst=Min("score")
        )

        finished_count = agg["finished"] or 0
        total_count = agg["total"] or 0
        not_finished = total_count - finished_count
        expired_count = agg["expired"] or 0
        active_count = agg["active"] or 0
        avg_kpi = round(agg["avg_score"] or 0, 1)
        best_kpi = round(minmax["best"] or 0, 1)
        worst_kpi = round(minmax["worst"] or 0, 1)
        pass_rate = round(
            finished_count / total_count * 100, 1
        ) if total_count else 0.0
        avg_dur_secs = (
            agg["avg_dur"].total_seconds() if agg["avg_dur"] else None
        )

        # ── Round-trip 3: answer-level aggregations ────────────────────────
        answer_base = Answer.objects.filter(attempt__session_id=self.session_id)

        answer_agg = answer_base.aggregate(
            total_answers=Count("id"),
            ai_checked=Count(
                "id",
                filter=Q(grading_status__in=["ai", "done"]),
            ),
            ai_failed=Count("id", filter=Q(grading_status="failed")),
            manual=Count("id", filter=Q(grading_status="manual")),
            avg_ai_score=Avg("ai_score", filter=Q(ai_score__isnull=False)),
        )

        # ── Round-trip 4: question type breakdown ──────────────────────────
        qt_rows = (
            answer_base
            .values("question__question_type")
            .annotate(
                total=Count("id"),
                correct=Count("id", filter=Q(is_correct=True)),
            )
            .order_by("question__question_type")
        )

        question_type_stats: list[QuestionTypeStats] = []
        for row in qt_rows:
            qt = row["question__question_type"]
            total = row["total"] or 1
            correct = row["correct"] or 0
            question_type_stats.append(QuestionTypeStats(
                question_type=qt,
                label=QUESTION_TYPE_LABELS.get(qt, qt),
                total=row["total"],
                correct=correct,
                rate=round(correct / total * 100, 1),
            ))

        # ── Round-trip 5: top & low students ──────────────────────────────
        finished_qs = (
            base_qs
            .filter(status=AttemptStatus.FINISHED)
            .values("student_name", "score")
            .order_by("-score")
        )
        top_students = [
            (r["student_name"], round(r["score"], 1))
            for r in finished_qs[:TOP_STUDENTS_COUNT]
        ]
        low_kpi_students = [
            (r["student_name"], round(r["score"], 1))
            for r in finished_qs
            if r["score"] < LOW_KPI_THRESHOLD
        ]

        # ── Round-trip 6: per-student stats ───────────────────────────────
        students = self._collect_student_stats(
            session_id=self.session_id,
            total_questions=total_questions,
        )

        return SessionReport(
            session_id=str(session.id),
            session_title=session.title or session.key,
            test_title=test.title,
            group_label=session.title or session.key[:16],
            created_at=session.created_at,
            duration_hours=round(duration_hours, 2),
            total_students=total_count,
            finished_count=finished_count,
            not_finished_count=not_finished,
            expired_count=expired_count,
            avg_kpi=avg_kpi,
            best_kpi=best_kpi,
            worst_kpi=worst_kpi,
            pass_rate=pass_rate,
            top_students=top_students,
            low_kpi_students=low_kpi_students,
            question_type_stats=question_type_stats,
            ai_total_checked=answer_agg["ai_checked"] or 0,
            ai_errors=answer_agg["ai_failed"] or 0,
            ai_manual_review=answer_agg["manual"] or 0,
            ai_avg_score=(
                round(answer_agg["avg_ai_score"], 1)
                if answer_agg["avg_ai_score"] is not None else None
            ),
            active_attempts=active_count,
            expired_attempts=expired_count,
            avg_duration_seconds=avg_dur_secs,
            total_answers=answer_agg["total_answers"] or 0,
            students=students,
        )

    def _collect_student_stats(
        self,
        session_id: str,
        total_questions: int,
    ) -> list[StudentStats]:
        """
        Один запрос для всех студентов + один запрос для ответов.
        Без N+1.
        """
        from apps.testing.models import StudentAttempt, Answer, AttemptStatus

        # Все попытки одним запросом
        attempts = list(
            StudentAttempt.objects
            .filter(session_id=session_id)
            .order_by("-score", "started_at")
        )

        attempt_ids = [a.id for a in attempts]

        # Ответы всех студентов одним запросом, группируем в Python
        answer_rows = list(
            Answer.objects
            .filter(attempt_id__in=attempt_ids)
            .values(
                "attempt_id",
                "question__question_type",
                "is_correct",
                "ai_score",
                "ai_confidence",
            )
        )

        # Сгруппируем по attempt_id
        from collections import defaultdict
        answers_by_attempt: dict = defaultdict(list)
        for row in answer_rows:
            answers_by_attempt[row["attempt_id"]].append(row)

        STATUS_DISPLAY = {
            "active": "Active",
            "finished": "Finished",
            "expired": "Expired",
        }

        result: list[StudentStats] = []
        for attempt in attempts:
            answers = answers_by_attempt.get(attempt.id, [])
            correct = sum(1 for a in answers if a["is_correct"] is True)
            wrong = sum(1 for a in answers if a["is_correct"] is False)

            ai_scores = [a["ai_score"] for a in answers if a["ai_score"] is not None]
            ai_confs = [a["ai_confidence"] for a in answers if a["ai_confidence"] is not None]
            avg_ai_score = round(sum(ai_scores) / len(ai_scores), 1) if ai_scores else None
            avg_ai_conf = round(sum(ai_confs) / len(ai_confs) * 100, 1) if ai_confs else None

            # Per-type breakdown для этого студента
            type_counts: dict[str, dict] = defaultdict(lambda: {"total": 0, "correct": 0})
            for a in answers:
                qt = a["question__question_type"]
                type_counts[qt]["total"] += 1
                if a["is_correct"] is True:
                    type_counts[qt]["correct"] += 1

            qt_breakdown: list[QuestionTypeStats] = []
            for qt_key, counts in type_counts.items():
                t = counts["total"] or 1
                c = counts["correct"]
                qt_breakdown.append(QuestionTypeStats(
                    question_type=qt_key,
                    label=QUESTION_TYPE_LABELS.get(qt_key, qt_key),
                    total=counts["total"],
                    correct=c,
                    rate=round(c / t * 100, 1),
                ))

            dur_secs = attempt.duration_seconds

            result.append(StudentStats(
                student_name=attempt.student_name,
                status=attempt.status,
                status_display=STATUS_DISPLAY.get(attempt.status, attempt.status.capitalize()),
                score=round(attempt.score, 1),
                total_questions=total_questions,
                correct_answers=correct,
                wrong_answers=wrong,
                ai_score=avg_ai_score,
                ai_confidence=avg_ai_conf,
                started_at=attempt.started_at,
                finished_at=attempt.finished_at,
                duration_seconds=dur_secs,
                question_type_breakdown=qt_breakdown,
            ))

        return result


# ── Message builder ────────────────────────────────────────────────────────────

class _ReportBuilder:
    """
    Строит HTML-сообщения для Telegram.
    parse_mode=HTML.
    """

    SEP = "━━━━━━━━━━━━━━"

    @classmethod
    def build_session_report(cls, report: SessionReport) -> str:
        """Первое сообщение — общая аналитика сессии."""
        lines: list[str] = []
        a = lines.append
        sep = cls.SEP

        a("📊 <b>Отчет по тестовой сессии</b>")
        a(f"📚 <b>Тест:</b> {_esc(report.test_title)}")
        a(f"👥 <b>Группа:</b> {_esc(report.group_label)}")
        a(f"🕒 <b>Дата:</b> {report.created_at.strftime('%d.%m.%Y %H:%M')}")
        dur = _fmt_hours(report.duration_hours)
        a(f"⏳ <b>Длительность сессии:</b> {dur}")
        a(f"👨‍🎓 <b>Всего студентов:</b> {report.total_students}")
        a(f"✅ <b>Завершили:</b> {report.finished_count}")
        a(f"❌ <b>Не завершили:</b> {report.not_finished_count}")
        a(f"⌛ <b>Expired:</b> {report.expired_count}")
        a(f"📈 <b>Средний KPI:</b> {report.avg_kpi}%")
        a(f"🏆 <b>Лучший результат:</b> {report.best_kpi}%")
        a(f"📉 <b>Худший результат:</b> {report.worst_kpi}%")
        a(f"🔥 <b>Процент прохождения теста:</b> {report.pass_rate}%")
        if report.top_students:
            a("🥇 <b>ТОП студентов:</b>")
            medals = ["1️⃣", "2️⃣", "3️⃣"]
            for i, (name, score) in enumerate(report.top_students):
                medal = medals[i] if i < len(medals) else f"{i+1}."
                a(f"{medal} {_esc(name)} — <b>{score}%</b>")
        if report.question_type_stats:
            a("📌 <b>Статистика по вопросам:</b>")
            for qt in report.question_type_stats:
                icon = "✅" if qt.rate >= 70 else "⚠️"
                a(f"{icon} {qt.label}: <b>{qt.rate}%</b>")

        a("📊 <b>Дополнительно:</b>")
        a(f"🟢 <b>Active attempts:</b> {report.active_attempts}")
        a(f"🔴 <b>Expired attempts:</b> {report.expired_attempts}")
        avg_dur_str = _fmt_seconds(report.avg_duration_seconds) if report.avg_duration_seconds else "—"
        a(f"⏱ <b>Среднее время прохождения:</b> {avg_dur_str}")
        a(f"📦 <b>Всего ответов:</b> {report.total_answers}")

        return "\n".join(lines)

    @classmethod
    def build_students_report(cls, students: list[StudentStats]) -> list[str]:
        """
        Возвращает список строк-блоков (один блок = один студент).
        chunk_telegram_message() объединит их в сообщения.
        """
        blocks: list[str] = []
        sep = cls.SEP

        for student in students:
            lines: list[str] = []
            a = lines.append

            # Иконка по статусу / результату
            if student.status == "finished" and student.score >= PASS_THRESHOLD:
                header_icon = "🥇"
                fire = " 🔥" if student.score >= 90 else ""
            elif student.status == "expired":
                header_icon = "⚠️"
                fire = ""
            else:
                header_icon = "❌"
                fire = ""

            a(sep)
            a(f"{header_icon} <b>{_esc(student.student_name)}</b>{fire}")
            a(sep)
            a("")

            # Статус
            status_icon = {
                "finished": "✅",
                "active":   "🟡",
                "expired":  "❌",
            }.get(student.status, "•")
            a(f"{status_icon} <b>Статус:</b> {student.status_display}")
            a(f"📈 <b>KPI:</b> {student.score}%")
            a(
                f"✔️ <b>Правильных ответов:</b> "
                f"{student.correct_answers}/20"
            )
            a(f"❌ <b>Ошибок:</b> {student.wrong_answers}")


            # Breakdown по типам вопросов
            if student.question_type_breakdown:
                a("📚 <b>Статистика вопросов:</b>")
                for qt in student.question_type_breakdown:
                    a(f"• {qt.label}: <b>{qt.correct}/{qt.total}</b>")

            # Время
            a("")
            started_str = (
                student.started_at.strftime("%H:%M")
                if student.started_at else "—"
            )
            finished_str = (
                student.finished_at.strftime("%H:%M")
                if student.finished_at else "—"
            )
            dur_str = _fmt_seconds(student.duration_seconds) if student.duration_seconds else "—"

            a(f"🕒 <b>Начал:</b> {started_str}")
            a(f"🏁 <b>Завершил:</b> {finished_str}")
            a(f"⏱ <b>Время прохождения:</b> {dur_str}")
            a("")

            blocks.append("\n".join(lines))

        return blocks


# ── Message chunking ───────────────────────────────────────────────────────────

def chunk_telegram_message(
    blocks: list[str],
    limit: int = MESSAGE_LIMIT,
) -> list[str]:
    """
    Объединяет блоки (строки) в сообщения ≤ limit символов.

    Гарантирует:
    - студент никогда не разрезается посередине
    - первый блок (summary) всегда идёт отдельно если он уже передан обёрнутым
    """
    messages: list[str] = []
    current_parts: list[str] = []
    current_len = 0

    for block in blocks:
        block_len = len(block)

        # Если один блок больше limit — отправляем как есть (telegram сам обрежет)
        if block_len > limit:
            if current_parts:
                messages.append("\n".join(current_parts))
                current_parts = []
                current_len = 0
            messages.append(block[:limit])
            continue

        # Не влезает в текущий chunk — сохраняем и начинаем новый
        if current_len + block_len + 1 > limit:
            messages.append("\n".join(current_parts))
            current_parts = [block]
            current_len = block_len
        else:
            current_parts.append(block)
            current_len += block_len + 1  # +1 для \n

    if current_parts:
        messages.append("\n".join(current_parts))

    return messages


# ── Telegram HTTP sender ───────────────────────────────────────────────────────

class _TelegramSender:
    """Синхронный HTTP-клиент для Telegram Bot API."""

    def __init__(self, token: str, chat_id: str) -> None:
        self.token = token
        self.chat_id = chat_id
        self._url = TELEGRAM_API_BASE.format(token=token)

    def send(self, text: str) -> dict:
        """
        Отправить одно сообщение.
        Возвращает Telegram API response dict.
        Бросает httpx.HTTPError при сетевых ошибках.
        """
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }

        with httpx.Client(timeout=HTTP_TIMEOUT) as client:
            resp = client.post(self._url, json=payload)
            resp.raise_for_status()
            data = resp.json()

        if not data.get("ok"):
            raise RuntimeError(
                f"Telegram API error: {data.get('description', 'unknown')}"
            )

        return data


def send_telegram_message(text: str) -> dict:
    """
    Публичная обёртка для отправки одного сообщения.
    Читает токен и group_id из settings.
    """
    sender = _TelegramSender(
        token=_get_bot_token(),
        chat_id=_get_group_id(),
    )
    return sender.send(text)


# ── Orchestrator ───────────────────────────────────────────────────────────────

class TelegramReportService:
    """
    Публичный API. Вызывается из Celery task.

    Usage:
        TelegramReportService.send_report(session_id)
    """

    @staticmethod
    def send_report(session_id: str) -> dict:
        """
        Собрать статистику, сформировать сообщения, отправить в Telegram.

        Returns:
            dict с полями status, session_id, messages_sent
        """
        log = logger.bind(session_id=session_id) if hasattr(logger, "bind") else logger

        if not _reports_enabled():
            logger.info(
                "[TelegramReport] Skipped (disabled or missing credentials). "
                "session_id=%s", session_id,
            )
            return {"status": "skipped", "session_id": session_id, "messages_sent": 0}

        logger.info("[TelegramReport] Collecting stats. session_id=%s", session_id)

        try:
            collector = _SessionStatsCollector(session_id)
            report = collector.collect()
        except Exception as exc:
            logger.exception(
                "[TelegramReport] Failed to collect stats. session_id=%s error=%s",
                session_id, exc,
            )
            raise

        logger.info(
            "[TelegramReport] Stats collected. session_id=%s session_title=%s "
            "total_students=%d",
            session_id, report.session_title, report.total_students,
        )

        summary_text = _ReportBuilder.build_session_report(report)
        student_blocks = _ReportBuilder.build_students_report(report.students)
        student_messages = chunk_telegram_message(student_blocks)

        all_messages = [summary_text] + student_messages

        sender = _TelegramSender(
            token=_get_bot_token(),
            chat_id=_get_group_id(),
        )

        sent_count = 0
        for i, msg in enumerate(all_messages):
            try:
                resp = sender.send(msg)
                sent_count += 1
                logger.info(
                    "[TelegramReport] Sent message %d/%d. session_id=%s telegram_ok=%s",
                    i + 1, len(all_messages), session_id, resp.get("ok"),
                )
            except httpx.HTTPError as exc:
                logger.error(
                    "[TelegramReport] HTTP error sending message %d. session_id=%s error=%s",
                    i + 1, session_id, exc,
                )
                raise
            except RuntimeError as exc:
                logger.error(
                    "[TelegramReport] Telegram API error message %d. session_id=%s error=%s",
                    i + 1, session_id, exc,
                )
                raise

        logger.info(
            "[TelegramReport] Done. session_id=%s messages_sent=%d "
            "telegram_group=%s",
            session_id, sent_count, _get_group_id(),
        )

        return {
            "status": "sent",
            "session_id": session_id,
            "messages_sent": sent_count,
            "total_students": report.total_students,
            "telegram_group_id": _get_group_id(),
        }


def _esc(text: str) -> str:
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _fmt_seconds(seconds: Optional[float]) -> str:
    if seconds is None:
        return "—"
    total = int(seconds)
    h, remainder = divmod(total, 3600)
    m, s = divmod(remainder, 60)
    if h:
        return f"{h} ч {m} мин"
    if m:
        return f"{m} мин"
    return f"{s} сек"


def _fmt_hours(hours: Optional[float]) -> str:
    if hours is None:
        return "—"
    total_mins = int(hours * 60)
    h, m = divmod(total_mins, 60)
    if h and m:
        return f"{h} ч {m} мин"
    if h:
        return f"{h} ч"
    return f"{m} мин"