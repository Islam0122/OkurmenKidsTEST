from __future__ import annotations
import logging
from dataclasses import dataclass, field
from typing import Optional
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone

logger = logging.getLogger(__name__)


def _models():
    from ..models import (
        Test, TestSession, StudentAttempt, Answer,
        Question, QuestionOption, AttemptStatus, SessionStatus,
    )
    return Test, TestSession, StudentAttempt, Answer, Question, QuestionOption, AttemptStatus, SessionStatus


# ─── DTOs ─────────────────────────────────────────────────────────────────────

@dataclass
class SessionCreateResult:
    session_id: str
    key: str
    test_title: str
    expires_at: str
    status: str


@dataclass
class AttemptStartResult:
    attempt_id: str
    student_name: str
    test_title: str
    questions: list


@dataclass
class AnswerResult:
    answer_id: str
    is_correct: Optional[bool]
    message: str


@dataclass
class FinishResult:
    attempt_id: str
    student_name: str
    score: float
    total_questions: int
    answered: int
    correct: int
    duration_seconds: Optional[float]


# ─── SessionService ───────────────────────────────────────────────────────────

class SessionService:

    @staticmethod
    def create_session(test_id: str) -> SessionCreateResult:
        Test, TestSession, *_ = _models()
        try:
            test = Test.objects.get(pk=test_id, is_active=True)
        except Test.DoesNotExist:
            raise ValidationError(f'Test {test_id} not found or inactive.')

        session = TestSession.objects.create(test=test)
        logger.info('Session %s created for test "%s"', session.key, test.title)
        return SessionCreateResult(
            session_id=str(session.id),
            key=session.key,
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
        """FastAPI-facing: minimal JSON payload for a session."""
        session = SessionService.validate_session(key)
        questions = _serialize_questions(session.test)
        return {
            'session_id':   str(session.id),
            'test_id':      str(session.test.id),
            'test_title':   session.test.title,
            'status':       session.status,
            'expires_at':   session.expires_at.isoformat(),
            'questions':    questions,
        }


# ─── AttemptService ───────────────────────────────────────────────────────────

class AttemptService:

    @staticmethod
    def start_attempt(key: str, student_name: str) -> AttemptStartResult:
        _, _, StudentAttempt, _, _, _, AttemptStatus, _ = _models()
        student_name = student_name.strip()
        if not student_name:
            raise ValidationError('student_name is required.')

        session = SessionService.validate_session(key)

        with transaction.atomic():
            if StudentAttempt.objects.filter(session=session, student_name=student_name).exists():
                raise ValidationError(
                    f'Student "{student_name}" already has an attempt for this session.'
                )
            attempt = StudentAttempt.objects.create(
                session=session, student_name=student_name
            )
            # Mark session as running on first attempt
            if session.status == 'created':
                from .models import SessionStatus
                session.status = SessionStatus.RUNNING
                session.save(update_fields=['status'])

        logger.info('Attempt %s started by "%s"', attempt.id, student_name)
        questions = _serialize_questions(session.test)
        return AttemptStartResult(
            attempt_id=str(attempt.id),
            student_name=student_name,
            test_title=session.test.title,
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

        answers  = attempt.answers.all()
        answered = answers.count()
        correct  = answers.filter(is_correct=True).count()
        total    = attempt.session.test.question_count

        logger.info('Attempt %s finished. Score: %.2f', attempt_id, attempt.score)
        return FinishResult(
            attempt_id=str(attempt.id),
            student_name=attempt.student_name,
            score=attempt.score,
            total_questions=total,
            answered=answered,
            correct=correct,
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
                'answer_text':      a.answer_text,
                'selected_options': a.selected_options,
                'answered_at':      a.answered_at.isoformat(),
            }
            if a.question.question_type in ('single_choice', 'multiple_choice'):
                item['correct_options'] = [
                    str(o.id) for o in a.question.options.filter(is_correct=True)
                ]
            answer_data.append(item)

        return {
            'attempt_id':       str(attempt.id),
            'student_name':     attempt.student_name,
            'test_title':       attempt.session.test.title,
            'score':            attempt.score,
            'status':           attempt.status,
            'started_at':       attempt.started_at.isoformat(),
            'finished_at':      attempt.finished_at.isoformat() if attempt.finished_at else None,
            'is_finished':      attempt.is_finished,
            'duration_seconds': attempt.duration_seconds,
            'answers':          answer_data,
        }


# ─── AnswerService ────────────────────────────────────────────────────────────

class AnswerService:

    @staticmethod
    def submit_answer(
        attempt_id: str,
        question_id: str,
        answer_text: str = '',
        selected_options: list[str] | None = None,
    ) -> AnswerResult:
        _, _, StudentAttempt, Answer, Question, _, AttemptStatus, _ = _models()
        selected_options = selected_options or []

        try:
            attempt = StudentAttempt.objects.select_related('session__test').get(pk=attempt_id)
        except StudentAttempt.DoesNotExist:
            raise ValidationError('Attempt not found.')

        if attempt.is_finished:
            raise ValidationError('Attempt already finished.')
        if not attempt.session.is_valid:
            raise ValidationError('Session expired.')

        try:
            question = Question.objects.prefetch_related('options').get(
                pk=question_id, test=attempt.session.test
            )
        except Question.DoesNotExist:
            raise ValidationError('Question not found in this test.')

        is_correct = AnswerService._evaluate(question, answer_text, selected_options)

        with transaction.atomic():
            answer, _ = Answer.objects.update_or_create(
                attempt=attempt,
                question=question,
                defaults={
                    'answer_text':      answer_text,
                    'selected_options': [str(o) for o in selected_options],
                    'is_correct':       is_correct,
                },
            )

        return AnswerResult(
            answer_id=str(answer.id),
            is_correct=is_correct,
            message=(
                'Answer saved.' if is_correct is None
                else ('Correct!' if is_correct else 'Incorrect.')
            ),
        )

    @staticmethod
    def _evaluate(question, answer_text: str, selected_options: list[str]) -> Optional[bool]:
        qtype = question.question_type
        if qtype == 'single_choice':
            correct_ids = {str(o.id) for o in question.options.filter(is_correct=True)}
            return len(selected_options) == 1 and set(selected_options) == correct_ids
        if qtype == 'multiple_choice':
            correct_ids = {str(o.id) for o in question.options.filter(is_correct=True)}
            return set(selected_options) == correct_ids
        return None  # text / code — requires AI grading


# ─── SyncService (FastAPI integration) ───────────────────────────────────────

class SyncService:

    @staticmethod
    def prepare_data_for_fastapi(session_key: str) -> dict:
        """Full session payload for FastAPI engine bootstrap."""
        return SessionService.get_session_data(session_key)

    @staticmethod
    def push_attempt_update(attempt_id: str, payload: dict) -> dict:
        """
        Called by FastAPI to sync answer updates back to Django.
        payload: {question_id, answer_text, selected_options}
        """
        return AnswerService.submit_answer(
            attempt_id=attempt_id,
            question_id=payload.get('question_id', ''),
            answer_text=payload.get('answer_text', ''),
            selected_options=payload.get('selected_options', []),
        ).__dict__

    @staticmethod
    def sync_attempt_results(attempt_id: str) -> dict:
        """FastAPI calls this to get current attempt state."""
        return AttemptService.get_attempt_result(attempt_id)

    @staticmethod
    def finalize_results(attempt_id: str) -> dict:
        """FastAPI calls this to finish an attempt."""
        result = AttemptService.finish_attempt(attempt_id)
        return result.__dict__


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _serialize_questions(test) -> list:
    from .models import Question
    qs = (
        Question.objects
        .filter(test=test)
        .prefetch_related('options')
        .order_by('order', 'created_at')
    )
    result = []
    for q in qs:
        item = {
            'id':         str(q.id),
            'text':       q.text,
            'type':       q.question_type,
            'difficulty': q.difficulty,
            'order':      q.order,
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


# ─── Public aliases (backwards compat with existing api_views.py) ─────────────

def create_session(test_id: str) -> SessionCreateResult:
    return SessionService.create_session(test_id)


def get_valid_session(key: str):
    return SessionService.validate_session(key)


def start_attempt(key: str, student_name: str) -> AttemptStartResult:
    return AttemptService.start_attempt(key, student_name)


def submit_answer(attempt_id, question_id, answer_text='', selected_options=None) -> AnswerResult:
    return AnswerService.submit_answer(attempt_id, question_id, answer_text, selected_options)


def finish_attempt(attempt_id: str) -> FinishResult:
    return AttemptService.finish_attempt(attempt_id)


def get_attempt_result(attempt_id: str) -> dict:
    return AttemptService.get_attempt_result(attempt_id)