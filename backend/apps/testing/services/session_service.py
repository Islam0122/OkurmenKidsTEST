from __future__ import annotations
import logging
from dataclasses import dataclass, field
from typing import Optional
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone

logger = logging.getLogger(__name__)


def _models():
    from ..models import Test, TestSession, StudentAttempt, Answer, Question, QuestionOption
    return Test, TestSession, StudentAttempt, Answer, Question, QuestionOption

@dataclass
class SessionCreateResult:
    session_id: str
    key: str
    test_title: str
    expires_at: str


def create_session(test_id: str) -> SessionCreateResult:
    """Create a new TestSession for an active test."""
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
    )


def get_valid_session(key: str):
    """
    Return a TestSession if the key is valid and not expired.
    Raises ValidationError otherwise.
    """
    _, TestSession, *_ = _models()
    try:
        session = TestSession.objects.select_related('test').get(key=key)
    except TestSession.DoesNotExist:
        raise ValidationError('Invalid session key.')
    if not session.is_valid:
        raise ValidationError('Session has expired or been deactivated.')
    return session


@dataclass
class AttemptStartResult:
    attempt_id: str
    student_name: str
    test_title: str
    questions: list


def start_attempt(key: str, student_name: str) -> AttemptStartResult:
    """
    Start a new attempt for a student in a session.
    Enforces: one attempt per (session, student_name).
    """
    _, _, StudentAttempt, _, _, _ = _models()
    student_name = student_name.strip()
    if not student_name:
        raise ValidationError('student_name is required.')

    session = get_valid_session(key)

    with transaction.atomic():
        if StudentAttempt.objects.filter(session=session, student_name=student_name).exists():
            raise ValidationError(
                f'Student "{student_name}" already has an attempt for this session.'
            )
        attempt = StudentAttempt.objects.create(session=session, student_name=student_name)

    questions = _serialize_questions(session.test)
    return AttemptStartResult(
        attempt_id=str(attempt.id),
        student_name=student_name,
        test_title=session.test.title,
        questions=questions,
    )


def _serialize_questions(test) -> list:
    """Return questions without correct answer indicators (for students)."""
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
            'id':         str(q.id),
            'text':       q.text,
            'type':       q.question_type,
            'difficulty': q.difficulty,
            'order':      q.order,
        }
        if q.language:
            item['language'] = q.language
        if q.question_type in ('single_choice', 'multiple_choice'):
            item['options'] = [
                {'id': str(o.id), 'text': o.text, 'order': o.order}
                for o in q.options.order_by('order')
            ]
        result.append(item)
    return result


@dataclass
class AnswerResult:
    answer_id: str
    is_correct: Optional[bool]
    message: str


def submit_answer(
    attempt_id: str,
    question_id: str,
    answer_text: str = '',
    selected_options: list[str] | None = None,
) -> AnswerResult:

    _, _, StudentAttempt, Answer, Question, _ = _models()
    selected_options = selected_options or []

    try:
        attempt = StudentAttempt.objects.select_related('session__test').get(pk=attempt_id)
    except StudentAttempt.DoesNotExist:
        raise ValidationError('Attempt not found.')

    if attempt.is_finished:
        raise ValidationError('Attempt already finished. No more answers accepted.')

    if not attempt.session.is_valid:
        raise ValidationError('Session expired.')

    try:
        question = Question.objects.prefetch_related('options').get(
            pk=question_id, test=attempt.session.test
        )
    except Question.DoesNotExist:
        raise ValidationError('Question not found in this test.')

    is_correct = _evaluate_answer(question, answer_text, selected_options)

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
            'Answer saved.'
            if is_correct is None
            else ('Correct!' if is_correct else 'Incorrect.')
        ),
    )


def _evaluate_answer(
    question,
    answer_text: str,
    selected_options: list[str],
) -> Optional[bool]:
    qtype = question.question_type

    if qtype == 'single_choice':
        correct_ids = {str(o.id) for o in question.options.filter(is_correct=True)}
        return len(selected_options) == 1 and set(selected_options) == correct_ids

    if qtype == 'multiple_choice':
        correct_ids = {str(o.id) for o in question.options.filter(is_correct=True)}
        return set(selected_options) == correct_ids

    return None  # text / code


@dataclass
class FinishResult:
    attempt_id: str
    student_name: str
    score: float
    total_questions: int
    answered: int
    correct: int
    duration_seconds: Optional[float]


def finish_attempt(attempt_id: str) -> FinishResult:
    _, _, StudentAttempt, _, _, _ = _models()

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

    return FinishResult(
        attempt_id=str(attempt.id),
        student_name=attempt.student_name,
        score=attempt.score,
        total_questions=total,
        answered=answered,
        correct=correct,
        duration_seconds=attempt.duration_seconds,
    )


def get_attempt_result(attempt_id: str) -> dict:
    _, _, StudentAttempt, _, _, _ = _models()

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
        'attempt_id':      str(attempt.id),
        'student_name':    attempt.student_name,
        'test_title':      attempt.session.test.title,
        'score':           attempt.score,
        'started_at':      attempt.started_at.isoformat(),
        'finished_at':     attempt.finished_at.isoformat() if attempt.finished_at else None,
        'is_finished':     attempt.is_finished,
        'duration_seconds': attempt.duration_seconds,
        'answers':         answer_data,
    }