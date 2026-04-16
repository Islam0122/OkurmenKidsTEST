from __future__ import annotations
import logging
from dataclasses import dataclass
from typing import Optional
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone

logger = logging.getLogger(__name__)


def _models():
    from ..models import (
        Test, TestSession, StudentAttempt, Answer,
        Question, QuestionOption, AttemptStatus, SessionStatus,
        SessionType, GradingStatus,
    )
    return (
        Test, TestSession, StudentAttempt, Answer,
        Question, QuestionOption, AttemptStatus, SessionStatus,
        SessionType, GradingStatus,
    )


# ─── DTOs ─────────────────────────────────────────────────────────────────────

@dataclass
class SessionCreateResult:
    session_id:   str
    key:          str
    title:        str
    session_type: str
    test_title:   str
    expires_at:   str
    status:       str


@dataclass
class AttemptStartResult:
    attempt_id:   str
    student_name: str
    test_title:   str
    session_type: str
    questions:    list


@dataclass
class AnswerResult:
    answer_id:      str
    is_correct:     Optional[bool]
    grading_status: str
    message:        str


@dataclass
class FinishResult:
    attempt_id:       str
    student_name:     str
    score:            float
    total_questions:  int
    answered:         int
    correct:          int
    pending_grading:  int
    duration_seconds: Optional[float]


# ─── SessionService ───────────────────────────────────────────────────────────

class SessionService:

    @staticmethod
    def create_session(
        test_id: str,
        title: str = '',
        session_type: str = 'exam',
        max_attempts_per_student: Optional[int] = None,
    ) -> SessionCreateResult:
        Test, TestSession, *_ = _models()
        try:
            test = Test.objects.get(pk=test_id, is_active=True)
        except Test.DoesNotExist:
            raise ValidationError(f'Test {test_id} not found or inactive.')

        # Для exam дефолтный лимит = 1 если не передан явно
        if session_type == 'exam' and max_attempts_per_student is None:
            max_attempts_per_student = 1

        session = TestSession.objects.create(
            test=test,
            title=title.strip(),
            session_type=session_type,
            max_attempts_per_student=max_attempts_per_student,
        )
        logger.info(
            'Session %s [%s] created for test "%s"',
            session.key, session_type, test.title,
        )
        return SessionCreateResult(
            session_id=str(session.id),
            key=session.key,
            title=session.title,
            session_type=session.session_type,
            test_title=test.title,
            expires_at=session.expires_at.isoformat(),
            status=session.status,
        )

    @staticmethod
    def validate_session(key: str):
        _, TestSession, *_ = _models()
        try:
            session = TestSession.objects.select_related('test').get(key=key)
        except TestSession.DoesNotExist:
            raise ValidationError('Invalid session key.')
        if not session.is_valid:
            raise ValidationError('Session expired or deactivated.')
        return session

    @staticmethod
    def expire_session(session_id: str) -> None:
        _, TestSession, *_ = _models()
        try:
            session = TestSession.objects.get(pk=session_id)
        except TestSession.DoesNotExist:
            raise ValidationError('Session not found.')
        session.deactivate()
        logger.info('Session %s force-expired.', session_id)

    @staticmethod
    def get_session_data(key: str) -> dict:
        session   = SessionService.validate_session(key)
        questions = _serialize_questions(session.test)
        return {
            'session_id':   str(session.id),
            'test_id':      str(session.test.id),
            'test_title':   session.test.title,
            'title':        session.title,
            'session_type': session.session_type,
            'status':       session.status,
            'expires_at':   session.expires_at.isoformat(),
            'questions':    questions,
        }


# ─── AttemptService ───────────────────────────────────────────────────────────

class AttemptService:

    @staticmethod
    def start_attempt(key: str, student_name: str) -> AttemptStartResult:
        _, _, StudentAttempt, _, _, _, AttemptStatus, SessionStatus, *_ = _models()

        student_name = student_name.strip()
        if not student_name:
            raise ValidationError('student_name is required.')

        session = SessionService.validate_session(key)

        # 🔥 EXAM RULE: only 1 attempt per student
        if session.session_type == "exam":
            exists = StudentAttempt.objects.filter(
                session=session,
                student_name=student_name,
                status__in=["active", "finished"]
            ).exists()

            if exists:
                raise ValidationError(
                    f'Student "{student_name}" already has attempt in this EXAM session.'
                )


        with transaction.atomic():
            attempt = StudentAttempt.objects.create(
                session=session,
                student_name=student_name,
            )

            if session.status == SessionStatus.CREATED:
                session.status = SessionStatus.RUNNING
                session.save(update_fields=['status'])

        logger.info(
            'Attempt %s started by "%s" [session_type=%s]',
            attempt.id, student_name, session.session_type,
        )
        from .question_selector import build_attempt_questions

        questions = build_attempt_questions(
            test_id=str(session.test_id),
            attempt_id=str(attempt.id),
        )

        return AttemptStartResult(
            attempt_id=str(attempt.id),
            student_name=student_name,
            test_title=session.test.title,
            session_type=session.session_type,
            questions=questions,
        )

    @staticmethod
    def finish_attempt(attempt_id: str) -> FinishResult:
        _, _, StudentAttempt, *_ = _models()
        try:
            attempt = StudentAttempt.objects.select_related('session__test').get(pk=attempt_id)
        except StudentAttempt.DoesNotExist:
            raise ValidationError('Attempt not found.')
        if attempt.is_finished:
            raise ValidationError('Attempt already finished.')

        attempt.finish()

        answers         = attempt.answers.all()
        answered        = answers.count()
        correct         = answers.filter(is_correct=True).count()
        pending_grading = answers.filter(is_correct=None).count()
        total           = attempt.session.test.question_count

        logger.info('Attempt %s finished. Score: %.2f', attempt_id, attempt.score)
        return FinishResult(
            attempt_id=str(attempt.id),
            student_name=attempt.student_name,
            score=attempt.score,
            total_questions=total,
            answered=answered,
            correct=correct,
            pending_grading=pending_grading,
            duration_seconds=attempt.duration_seconds,
        )

    @staticmethod
    def get_attempt_result(attempt_id: str) -> dict:
        _, _, StudentAttempt, *_ = _models()
        try:
            attempt = (
                StudentAttempt.objects
                .select_related('session__test')
                .get(pk=attempt_id)
            )
        except StudentAttempt.DoesNotExist:
            raise ValidationError('Attempt not found.')

        answers = (
            attempt.answers
            .select_related('question')
            .prefetch_related('question__options')
            .all()
        )

        answer_data = []
        for a in answers:
            item = {
                'question_id':      str(a.question.id),
                'question_text':    a.question.text,
                'question_type':    a.question.question_type,
                'is_correct':       a.is_correct,
                'grading_status':   a.grading_status,
                'answer_text':      a.answer_text,
                'selected_options': a.selected_options,
                'answered_at':      a.answered_at.isoformat(),
            }
            if a.question.question_type in ('single_choice', 'multiple_choice'):
                item['correct_options'] = [
                    str(o.id) for o in a.question.options.filter(is_correct=True)
                ]
            if a.ai_grade is not None:
                item['ai_grade']    = a.ai_grade
                item['ai_feedback'] = a.ai_feedback
            answer_data.append(item)

        return {
            'attempt_id':       str(attempt.id),
            'student_name':     attempt.student_name,
            'test_title':       attempt.session.test.title,
            'session_title':    attempt.session.title,
            'session_type':     attempt.session.session_type,
            'score':            attempt.score,
            'status':           attempt.status,
            'started_at':       attempt.started_at.isoformat(),
            'finished_at':      attempt.finished_at.isoformat() if attempt.finished_at else None,
            'is_finished':      attempt.is_finished,
            'duration_seconds': attempt.duration_seconds,
            'answers':          answer_data,
        }



# ── Paste this class into services.py, replacing the existing AnswerService ────

class AnswerService:

    @staticmethod
    def submit_answer(
        attempt_id: str,
        question_id: str,
        answer_text: str = '',
        selected_options: list[str] | None = None,
    ):  # → AnswerResult (imported from same file)
        """
        Save a student answer.

        Choice questions  → evaluated immediately (unchanged behaviour).
        Text / code       → saved with grading_status='pending',
                            Celery task enqueued for AI grading.

        The API response is IDENTICAL in both cases.  Frontend checks
        grading_status to know whether to poll for a result.
        """
        # Local imports to match existing pattern in services.py
        from ..models import (
            Answer, Question, StudentAttempt,
            GradingStatus, QuestionType,
        )
        # AnswerResult is defined in the same file
        from .services import AnswerResult  # adjust path if needed

        selected_options = selected_options or []

        try:
            attempt = StudentAttempt.objects.select_related('session__test').get(pk=attempt_id)
        except StudentAttempt.DoesNotExist:
            from django.core.exceptions import ValidationError
            raise ValidationError('Attempt not found.')

        if attempt.is_finished:
            from django.core.exceptions import ValidationError
            raise ValidationError('Attempt already finished.')
        if not attempt.session.is_valid:
            from django.core.exceptions import ValidationError
            raise ValidationError('Session expired.')

        try:
            question = Question.objects.prefetch_related('options').get(
                pk=question_id, test=attempt.session.test,
            )
        except Question.DoesNotExist:
            from django.core.exceptions import ValidationError
            raise ValidationError('Question not found in this test.')

        is_correct, grading_status = AnswerService._evaluate(
            question, answer_text, selected_options
        )

        from django.db import transaction
        with transaction.atomic():
            answer, _ = Answer.objects.update_or_create(
                attempt=attempt,
                question=question,
                defaults={
                    'answer_text':      answer_text,
                    'selected_options': [str(o) for o in selected_options],
                    'is_correct':       is_correct,
                    'grading_status':   grading_status,
                },
            )

        # ── Async AI grading (only for text/code) ────────────────────────────────
        if grading_status == GradingStatus.PENDING:
            AnswerService._enqueue_ai_grading(str(answer.id))

        # ── Build response (identical shape to original) ──────────────────────────
        if is_correct is None:
            message = 'Answer saved, pending AI grading.'
        else:
            message = 'Correct!' if is_correct else 'Incorrect.'

        return AnswerResult(
            answer_id=str(answer.id),
            is_correct=is_correct,
            grading_status=grading_status,
            message=message,
        )

    @staticmethod
    def _evaluate(
        question,
        answer_text: str,
        selected_options: list[str],
    ) -> tuple[Optional[bool], str]:
        """
        Returns (is_correct, grading_status).
        Unchanged logic for choice questions.
        Text/code now returns ('pending') instead of (None, 'pending') — same value.
        """
        from ..models import GradingStatus, QuestionType

        if question.question_type == QuestionType.SINGLE_CHOICE:
            correct_ids = {str(o.id) for o in question.options.filter(is_correct=True)}
            result = len(selected_options) == 1 and set(selected_options) == correct_ids
            return result, GradingStatus.AUTO

        if question.question_type == QuestionType.MULTIPLE_CHOICE:
            correct_ids = {str(o.id) for o in question.options.filter(is_correct=True)}
            result = set(selected_options) == correct_ids
            return result, GradingStatus.AUTO

        # text / code — defer to AI
        return None, GradingStatus.PENDING

    @staticmethod
    def _enqueue_ai_grading(answer_id: str) -> None:
        """
        Fire-and-forget: enqueue Celery task.
        Failure to enqueue is logged but never propagates to the API caller.
        """
        try:
            from ..tasks import grade_answer_task
            grade_answer_task.delay(answer_id)
            logger.info("AI grading task enqueued for answer %s.", answer_id)
        except Exception as exc:
            # Celery broker might be down; the periodic regrade task will pick this up.
            logger.error(
                "Failed to enqueue AI grading task for answer %s: %s. "
                "Will be retried by regrade_pending_answers_task.",
                answer_id, exc,
            )


# ─── SyncService ──────────────────────────────────────────────────────────────

class SyncService:

    @staticmethod
    def prepare_data_for_fastapi(session_key: str) -> dict:
        return SessionService.get_session_data(session_key)

    @staticmethod
    def push_attempt_update(attempt_id: str, payload: dict) -> dict:
        return AnswerService.submit_answer(
            attempt_id=attempt_id,
            question_id=payload.get('question_id', ''),
            answer_text=payload.get('answer_text', ''),
            selected_options=payload.get('selected_options', []),
        ).__dict__

    @staticmethod
    def sync_attempt_results(attempt_id: str) -> dict:
        return AttemptService.get_attempt_result(attempt_id)

    @staticmethod
    def finalize_results(attempt_id: str) -> dict:
        return AttemptService.finish_attempt(attempt_id).__dict__


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _serialize_questions(test) -> list:
    from ..models import Question
    qs = (
        Question.objects
        .filter(test=test)
        .prefetch_related('options')
        .order_by('order', 'created_at')
    )
    result = []
    for q in qs:
        item = {
            'id':               str(q.id),
            'text':             q.text,
            'type':             q.question_type,
            'difficulty':       q.difficulty,
            'order':            q.order,
            'is_auto_gradable': q.is_auto_gradable,
        }
        if q.language:
            item['language'] = q.language
        if q.metadata:
            item['metadata'] = q.metadata
        if q.question_type in ('single_choice', 'multiple_choice'):
            item['options'] = [
                {'id': str(o.id), 'text': o.text, 'order': o.order}
                for o in q.options.order_by('order')
            ]
        result.append(item)
    return result


# ─── Public aliases ───────────────────────────────────────────────────────────

def create_session(
    test_id: str,
    title: str = '',
    session_type: str = 'exam',
    max_attempts_per_student: Optional[int] = None,
) -> SessionCreateResult:
    return SessionService.create_session(test_id, title, session_type, max_attempts_per_student)


def get_valid_session(key: str):
    return SessionService.validate_session(key)


def start_attempt(key: str, student_name: str) -> AttemptStartResult:
    return AttemptService.start_attempt(key, student_name)


def submit_answer(
    attempt_id: str,
    question_id: str,
    answer_text: str = '',
    selected_options: list | None = None,
) -> AnswerResult:
    return AnswerService.submit_answer(attempt_id, question_id, answer_text, selected_options)


def finish_attempt(attempt_id: str) -> FinishResult:
    return AttemptService.finish_attempt(attempt_id)


def get_attempt_result(attempt_id: str) -> dict:
    return AttemptService.get_attempt_result(attempt_id)