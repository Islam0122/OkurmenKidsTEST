import uuid
import secrets
from datetime import timedelta
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError


class QuestionType(models.TextChoices):
    SINGLE_CHOICE   = 'single_choice',   'Один вариант ответа'
    MULTIPLE_CHOICE = 'multiple_choice', 'Несколько вариантов ответа'
    TEXT            = 'text',            'Текстовый ответ'
    CODE            = 'code',            'Код (программирование)'


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


class Test(models.Model):
    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title       = models.CharField(max_length=255, unique=True, verbose_name='Название теста')
    description = models.TextField(blank=True, verbose_name='Описание')
    level       = models.CharField(
        max_length=10, choices=DifficultyLevel.choices,
        default=DifficultyLevel.MEDIUM, verbose_name='Уровень сложности'
    )
    is_active   = models.BooleanField(default=True, verbose_name='Активен')
    created_at  = models.DateTimeField(auto_now_add=True, verbose_name='Создан')
    updated_at  = models.DateTimeField(auto_now=True,     verbose_name='Обновлён')

    class Meta:
        ordering        = ['title']
        verbose_name    = 'Тест'
        verbose_name_plural = 'Тесты'

    def __str__(self):
        return self.title

    @property
    def question_count(self):
        return self.questions.count()


class Question(models.Model):
    id            = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    test          = models.ForeignKey(
        Test, on_delete=models.CASCADE, related_name='questions', verbose_name='Тест'
    )
    text          = models.TextField(verbose_name='Текст вопроса')
    question_type = models.CharField(
        max_length=20, choices=QuestionType.choices,
        default=QuestionType.SINGLE_CHOICE, verbose_name='Тип вопроса'
    )
    language      = models.CharField(
        max_length=20, choices=ProgrammingLanguage.choices,
        default=ProgrammingLanguage.NONE, blank=True,
        verbose_name='Язык программирования'
    )
    difficulty    = models.CharField(
        max_length=10, choices=DifficultyLevel.choices,
        default=DifficultyLevel.MEDIUM, verbose_name='Сложность'
    )
    order         = models.PositiveIntegerField(default=0, verbose_name='Порядок')
    created_at    = models.DateTimeField(auto_now_add=True, verbose_name='Создан')

    class Meta:
        ordering        = ['test', 'order', 'created_at']
        verbose_name    = 'Вопрос'
        verbose_name_plural = 'Вопросы'

    def __str__(self):
        return f'[{self.test.title}] {self.text[:60]}'


class QuestionOption(models.Model):
    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question   = models.ForeignKey(
        Question, on_delete=models.CASCADE, related_name='options', verbose_name='Вопрос'
    )
    text       = models.CharField(max_length=1024, verbose_name='Текст варианта')
    is_correct = models.BooleanField(default=False, verbose_name='Правильный ответ')
    order      = models.PositiveSmallIntegerField(default=0, verbose_name='Порядок')

    class Meta:
        ordering        = ['order']
        verbose_name    = 'Вариант ответа'
        verbose_name_plural = 'Варианты ответов'

    def __str__(self):
        mark = '✓' if self.is_correct else '✗'
        return f'{mark} {self.text[:60]}'


SESSION_TTL_HOURS = 2


def _default_expires():
    return timezone.now() + timedelta(hours=SESSION_TTL_HOURS)


def _generate_key():
    return secrets.token_urlsafe(16)


class TestSession(models.Model):
    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    test       = models.ForeignKey(
        Test, on_delete=models.CASCADE, related_name='sessions', verbose_name='Тест'
    )
    key        = models.CharField(
        max_length=64, unique=True, default=_generate_key, verbose_name='Ключ сессии'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создан')
    expires_at = models.DateTimeField(default=_default_expires, verbose_name='Истекает')
    is_active  = models.BooleanField(default=True, verbose_name='Активна')

    class Meta:
        ordering        = ['-created_at']
        verbose_name    = 'Сессия теста'
        verbose_name_plural = 'Сессии тестов'

    def __str__(self):
        return f'{self.test.title} / {self.key}'

    @property
    def is_valid(self):
        return self.is_active and timezone.now() < self.expires_at

    def deactivate(self):
        self.is_active = False
        self.save(update_fields=['is_active'])



class StudentAttempt(models.Model):
    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session      = models.ForeignKey(
        TestSession, on_delete=models.CASCADE,
        related_name='attempts', verbose_name='Сессия'
    )
    student_name = models.CharField(max_length=255, verbose_name='Имя студента')
    started_at   = models.DateTimeField(auto_now_add=True, verbose_name='Начат')
    finished_at  = models.DateTimeField(null=True, blank=True, verbose_name='Завершён')
    score        = models.FloatField(default=0.0, verbose_name='Балл (0–100)')

    class Meta:
        ordering        = ['-started_at']
        unique_together = [('session', 'student_name')]
        verbose_name    = 'Попытка студента'
        verbose_name_plural = 'Попытки студентов'

    def __str__(self):
        return f'{self.student_name} → {self.session}'

    @property
    def is_finished(self):
        return self.finished_at is not None

    @property
    def duration_seconds(self):
        if self.finished_at:
            return (self.finished_at - self.started_at).total_seconds()
        return None

    def finish(self):
        if self.is_finished:
            raise ValidationError('Attempt already finished.')
        self.finished_at = timezone.now()
        self._recalculate_score()
        self.save(update_fields=['finished_at', 'score'])

    def _recalculate_score(self):
        answers = self.answers.select_related('question').all()
        if not answers.exists():
            self.score = 0.0
            return
        correct = answers.filter(is_correct=True).count()
        self.score = round((correct / answers.count()) * 100, 2)


class Answer(models.Model):
    id               = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    attempt          = models.ForeignKey(
        StudentAttempt, on_delete=models.CASCADE,
        related_name='answers', verbose_name='Попытка'
    )
    question         = models.ForeignKey(
        Question, on_delete=models.CASCADE,
        related_name='answers', verbose_name='Вопрос'
    )
    answer_text      = models.TextField(blank=True, verbose_name='Текстовый ответ')
    selected_options = models.JSONField(default=list, verbose_name='Выбранные варианты (UUID)')
    is_correct       = models.BooleanField(null=True, blank=True, verbose_name='Верно?')
    answered_at      = models.DateTimeField(auto_now_add=True, verbose_name='Отвечено')

    class Meta:
        ordering        = ['answered_at']
        unique_together = [('attempt', 'question')]
        verbose_name    = 'Ответ'
        verbose_name_plural = 'Ответы'

    def __str__(self):
        return f'{self.attempt.student_name} → Q:{self.question_id}'