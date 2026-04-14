import uuid
import secrets
from datetime import timedelta
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError


class QuestionType(models.TextChoices):
    SINGLE_CHOICE   = 'single_choice',   'Один вариант'
    MULTIPLE_CHOICE = 'multiple_choice', 'Несколько вариантов'
    TEXT            = 'text',            'Текстовый ответ'
    CODE            = 'code',            'Код'


class DifficultyLevel(models.TextChoices):
    EASY   = 'easy',   'Лёгкий'
    MEDIUM = 'medium', 'Средний'
    HARD   = 'hard',   'Сложный'


class ProgrammingLanguage(models.TextChoices):
    PYTHON     = 'python',     'Python'
    JAVASCRIPT = 'javascript', 'JavaScript'
    HTML       = 'html',       'HTML'
    CSS        = 'css',        'CSS'
    NONE       = '',           '—'


class SessionType(models.TextChoices):
    EXAM     = 'exam',     'Экзамен'
    TRAINING = 'training', 'Тренажёр'


class SessionStatus(models.TextChoices):
    CREATED  = 'created',  'Создана'
    RUNNING  = 'running',  'Идёт'
    FINISHED = 'finished', 'Завершена'


class AttemptStatus(models.TextChoices):
    ACTIVE   = 'active',   'Активна'
    FINISHED = 'finished', 'Завершена'
    EXPIRED  = 'expired',  'Просрочена'


class Test(models.Model):
    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title       = models.CharField(max_length=255, unique=True, verbose_name='Название')
    description = models.TextField(blank=True, verbose_name='Описание')
    level       = models.CharField(
        max_length=10, choices=DifficultyLevel.choices,
        default=DifficultyLevel.MEDIUM, verbose_name='Уровень',
    )
    is_active   = models.BooleanField(default=True, verbose_name='Активен')
    created_at  = models.DateTimeField(auto_now_add=True, verbose_name='Создан')
    updated_at  = models.DateTimeField(auto_now=True, verbose_name='Обновлён')

    class Meta:
        ordering            = ['title']
        verbose_name        = 'Тест'
        verbose_name_plural = 'Тесты'

    def __str__(self):
        return self.title

    @property
    def question_count(self):
        return self.questions.count()


# ── Question ──────────────────────────────────────────────────────────────────

class Question(models.Model):
    id            = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    test          = models.ForeignKey(
        Test, on_delete=models.CASCADE, related_name='questions',
        verbose_name='Тест',
    )
    text          = models.TextField(verbose_name='Текст вопроса')
    question_type = models.CharField(
        max_length=20, choices=QuestionType.choices,
        default=QuestionType.SINGLE_CHOICE, verbose_name='Тип',
    )
    language      = models.CharField(
        max_length=20, choices=ProgrammingLanguage.choices,
        default=ProgrammingLanguage.NONE, blank=True, verbose_name='Язык',
    )
    difficulty    = models.CharField(
        max_length=10, choices=DifficultyLevel.choices,
        default=DifficultyLevel.MEDIUM, verbose_name='Сложность',
    )
    order         = models.PositiveIntegerField(default=0, verbose_name='Порядок')
    metadata      = models.JSONField(default=dict, blank=True, verbose_name='Метаданные')
    created_at    = models.DateTimeField(auto_now_add=True, verbose_name='Создан')

    class Meta:
        ordering            = ['test', 'order', 'created_at']
        verbose_name        = 'Вопрос'
        verbose_name_plural = 'Вопросы'
        indexes = [
            models.Index(fields=['test', 'order'], name='question_test_order_idx'),
            models.Index(fields=['question_type'],  name='question_type_idx'),
        ]
        constraints = [
            # Заменяет устаревший unique_together
            models.UniqueConstraint(
                fields=['test', 'text'],
                name='unique_question_text_per_test',
            ),
        ]

    def __str__(self):
        return f'[{self.test.title}] {self.text[:60]}'

    def clean(self):
        if self.question_type == QuestionType.CODE and not self.language:
            raise ValidationError({'language': 'Для code-вопроса обязателен язык.'})

    @property
    def is_auto_gradable(self) -> bool:
        """True если вопрос можно проверить автоматически (без AI)."""
        return self.question_type in (
            QuestionType.SINGLE_CHOICE, QuestionType.MULTIPLE_CHOICE
        )


# ── QuestionOption ────────────────────────────────────────────────────────────

class QuestionOption(models.Model):
    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question   = models.ForeignKey(
        Question, on_delete=models.CASCADE, related_name='options',
        verbose_name='Вопрос',
    )
    text       = models.CharField(max_length=1024, verbose_name='Текст варианта')
    is_correct = models.BooleanField(default=False, verbose_name='Правильный')
    order      = models.PositiveSmallIntegerField(default=0, verbose_name='Порядок')

    class Meta:
        ordering            = ['order']
        verbose_name        = 'Вариант ответа'
        verbose_name_plural = 'Варианты ответов'
        indexes = [
            models.Index(fields=['question', 'is_correct'], name='option_question_correct_idx'),
        ]

    def __str__(self):
        return f'{"✓" if self.is_correct else "✗"} {self.text[:60]}'


# ── TestSession ───────────────────────────────────────────────────────────────

SESSION_TTL_HOURS = 2


def _default_expires():
    return timezone.now() + timedelta(hours=SESSION_TTL_HOURS)


def _generate_key():
    return secrets.token_urlsafe(16)


class TestSession(models.Model):
    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    test         = models.ForeignKey(
        Test, on_delete=models.CASCADE, related_name='sessions', verbose_name='Тест',
    )
    session_type = models.CharField(
        max_length=10,
        choices=SessionType.choices,
        default=SessionType.EXAM,
        verbose_name='Тип сессии',
        db_index=True,
    )
    title        = models.CharField(
        max_length=255, blank=True, verbose_name='Название сессии',
        help_text='Необязательное название (напр. "Группа A, 01.04.2026")',
    )
    key          = models.CharField(
        max_length=64, unique=True, default=_generate_key,
        verbose_name='Ключ сессии', db_index=True,
    )
    status       = models.CharField(
        max_length=10, choices=SessionStatus.choices,
        default=SessionStatus.CREATED, verbose_name='Статус',
    )
    created_at   = models.DateTimeField(auto_now_add=True, verbose_name='Создана')
    expires_at   = models.DateTimeField(default=_default_expires, verbose_name='Истекает')
    is_active    = models.BooleanField(default=True, verbose_name='Активна')

    # Training-specific: максимальное кол-во попыток на одного студента.
    # None = без ограничений (используется в training-режиме).
    max_attempts_per_student = models.PositiveSmallIntegerField(
        null=True, blank=True,
        verbose_name='Макс. попыток на студента',
        help_text='Только для режима exam. Пусто = без ограничений.',
    )

    class Meta:
        ordering            = ['-created_at']
        verbose_name        = 'Сессия тестирования'
        verbose_name_plural = 'Сессии тестирования'
        indexes = [
            models.Index(fields=['status', 'is_active'], name='session_status_active_idx'),
        ]

    def __str__(self):
        label = self.title or self.key
        return f'{self.test.title} [{self.get_session_type_display()}] / {label}'

    # ── Properties ────────────────────────────────────────────────────────────

    @property
    def is_exam(self) -> bool:
        return self.session_type == SessionType.EXAM

    @property
    def is_training(self) -> bool:
        return self.session_type == SessionType.TRAINING

    @property
    def is_time_expired(self) -> bool:
        """Только для exam: время вышло."""
        return self.is_exam and timezone.now() >= self.expires_at

    @property
    def is_valid(self) -> bool:
        """
        Exam:     активна + не истёк expires_at
        Training: активна (expires_at не важен)
        """
        if not self.is_active:
            return False
        if self.is_exam:
            return timezone.now() < self.expires_at
        return True  # training — всегда доступен

    @property
    def active_attempt_count(self) -> int:
        return self.attempts.filter(status=AttemptStatus.ACTIVE).count()

    # ── Methods ───────────────────────────────────────────────────────────────

    def can_student_attempt(self, student_name: str) -> bool:
        """
        Exam:     одна попытка на (session, student_name) — если max_attempts_per_student=1 (дефолт).
        Training: без ограничений, если max_attempts_per_student is None.
        """
        if self.max_attempts_per_student is None:
            return True
        student_count = self.attempts.filter(
            student_name=student_name,
        ).exclude(status=AttemptStatus.EXPIRED).count()
        return student_count < self.max_attempts_per_student

    def deactivate(self) -> None:
        """
        Exam:     деактивирует полностью.
        Training: просто ставит finished, но is_active не трогает —
                  тренажёр не «умирает» при завершении сессии.
        """
        self.status = SessionStatus.FINISHED
        if self.is_exam:
            self.is_active = False
        self.save(update_fields=['status', 'is_active'])


# ── StudentAttempt ────────────────────────────────────────────────────────────

class StudentAttempt(models.Model):
    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session      = models.ForeignKey(
        TestSession, on_delete=models.CASCADE,
        related_name='attempts', verbose_name='Сессия',
    )
    student_name = models.CharField(max_length=255, verbose_name='Имя студента')
    started_at   = models.DateTimeField(auto_now_add=True, verbose_name='Начата')
    finished_at  = models.DateTimeField(null=True, blank=True, verbose_name='Завершена')
    score        = models.FloatField(default=0.0, verbose_name='Балл (0–100)')
    status       = models.CharField(
        max_length=10, choices=AttemptStatus.choices,
        default=AttemptStatus.ACTIVE, verbose_name='Статус', db_index=True,
    )

    class Meta:
        ordering            = ['-started_at']
        verbose_name        = 'Попытка прохождения'
        verbose_name_plural = 'Попытки прохождения'
        indexes = [
            models.Index(fields=['session', 'student_name'], name='attempt_session_student_idx'),
            models.Index(fields=['status', 'started_at'],    name='attempt_status_started_idx'),
        ]
        constraints = [
            # Для exam: один студент = одна попытка в рамках сессии.
            # Для training UniqueConstraint снимается через condition.
            models.UniqueConstraint(
                fields=['session', 'student_name'],
                condition=models.Q(status__in=['active', 'finished']),
                name='unique_active_attempt_per_student_per_session',
            ),
        ]

    def __str__(self):
        return f'{self.student_name} → {self.session}'

    # ── Properties ────────────────────────────────────────────────────────────

    @property
    def is_finished(self) -> bool:
        return self.status == AttemptStatus.FINISHED

    @property
    def duration_seconds(self) -> float | None:
        if self.finished_at:
            return (self.finished_at - self.started_at).total_seconds()
        return None

    # ── Score calculation (явный, безопасный) ─────────────────────────────────

    def _recalculate_score(self) -> None:
        """
        Считаем score только по auto-gradable вопросам.
        Для text/code (is_correct=None) — исключаем из знаменателя,
        чтобы не занижать балл за ещё не проверенные ответы.
        """
        answers = list(self.answers.select_related('question').all())
        if not answers:
            self.score = 0.0
            return

        gradable = [a for a in answers if a.is_correct is not None]
        if not gradable:
            # Все вопросы требуют ручной/AI проверки
            self.score = 0.0
            return

        correct = sum(1 for a in gradable if a.is_correct)
        self.score = round((correct / len(gradable)) * 100, 2)

    def finish(self) -> None:
        if self.is_finished:
            raise ValidationError('Attempt already finished.')
        self.finished_at = timezone.now()
        self.status      = AttemptStatus.FINISHED
        self._recalculate_score()
        self.save(update_fields=['finished_at', 'status', 'score'])

    def expire(self) -> None:
        """Принудительно истекает попытка (например, по таймауту сессии)."""
        if self.is_finished:
            return
        self.status = AttemptStatus.EXPIRED
        self.save(update_fields=['status'])



class GradingStatus(models.TextChoices):  # noqa: F821  (models imported in host file)
    PENDING    = 'pending',    'На проверке'
    PROCESSING = 'processing', 'Обрабатывается'  # NEW: Celery picked it up
    AUTO       = 'auto',       'Авто'
    AI         = 'ai',         'AI'              # kept for backward compat
    DONE       = 'done',       'Готово'          # NEW: AI grading finished
    FAILED     = 'failed',     'Ошибка AI'       # NEW: all retries exhausted
    MANUAL     = 'manual',     'Вручную'


# ── Replace only the Answer model ─────────────────────────────────────────────

class Answer(models.Model):  # noqa: F821
    id               = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    attempt          = models.ForeignKey(
        'StudentAttempt', on_delete=models.CASCADE,
        related_name='answers', verbose_name='Попытка',
    )
    question         = models.ForeignKey(
        'Question', on_delete=models.CASCADE,
        related_name='answers', verbose_name='Вопрос',
    )
    answer_text      = models.TextField(blank=True, verbose_name='Текстовый ответ')
    selected_options = models.JSONField(default=list, verbose_name='Выбранные варианты (UUID)')
    is_correct       = models.BooleanField(null=True, blank=True, verbose_name='Верно?')

    # ── Grading metadata ───────────────────────────────────────────────────────
    grading_status   = models.CharField(
        max_length=15,                        # widened from 10 to fit 'processing'
        choices=GradingStatus.choices,
        default=GradingStatus.PENDING,
        verbose_name='Статус проверки',
        db_index=True,
    )

    # Legacy field (from migration 0004) — kept as-is for backward compat
    ai_grade         = models.FloatField(null=True, blank=True, verbose_name='Оценка AI (0–10)')
    ai_feedback      = models.TextField(blank=True, verbose_name='Комментарий AI')

    # ── NEW fields (migration 0005) ────────────────────────────────────────────
    ai_score         = models.FloatField(null=True, blank=True, verbose_name='Балл AI (0–10)')
    ai_confidence    = models.FloatField(null=True, blank=True, verbose_name='Уверенность AI (0–1)')
    ai_suggestion    = models.TextField(blank=True, verbose_name='Подсказка AI')

    answered_at      = models.DateTimeField(auto_now_add=True, verbose_name='Отвечено')

    class Meta:
        ordering            = ['answered_at']
        verbose_name        = 'Ответ пользователя'
        verbose_name_plural = 'Ответы пользователей'
        indexes = [
            models.Index(fields=['attempt', 'question'],       name='answer_attempt_question_idx'),
            models.Index(fields=['grading_status'],            name='answer_grading_status_idx'),
            models.Index(fields=['grading_status', 'answered_at'],
                         name='answer_grading_status_time_idx'),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['attempt', 'question'],
                name='unique_answer_per_attempt_question',
            ),
        ]

    def __str__(self):
        return f'{self.attempt.student_name} → Q:{self.question_id}'

    # ── Grading helpers ────────────────────────────────────────────────────────

    def mark_auto_graded(self, is_correct: bool) -> None:
        """Used by AnswerService for choice questions — unchanged."""
        self.is_correct     = is_correct
        self.grading_status = GradingStatus.AUTO
        self.save(update_fields=['is_correct', 'grading_status'])

    def mark_ai_graded(self, grade: float, feedback: str) -> None:
        """
        Legacy method — still works.  New code uses tasks._persist_grade() instead,
        which also populates ai_score, ai_confidence, ai_suggestion.
        """
        self.ai_grade       = grade
        self.ai_feedback    = feedback
        self.is_correct     = grade >= 5.0
        self.grading_status = GradingStatus.DONE   # was 'ai'; 'done' is the new canonical value
        self.save(update_fields=['ai_grade', 'ai_feedback', 'is_correct', 'grading_status'])

    def mark_manual_graded(self, is_correct: bool) -> None:
        self.is_correct     = is_correct
        self.grading_status = GradingStatus.MANUAL
        self.save(update_fields=['is_correct', 'grading_status'])