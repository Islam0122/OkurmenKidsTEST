"""
admin.py — Testing app.
"""
from __future__ import annotations

import nested_admin
from django.contrib import admin, messages
from django.db.models import Count
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html

from .models import (
    Answer, AttemptStatus, Question, QuestionOption,
    QuestionType, StudentAttempt, Test, TestSession,
)
from .resources import (
    AnswerResource, QuestionOptionResource, QuestionResource,
    StudentAttemptResource, TestResource, TestSessionResource,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _badge(text: str, color: str) -> str:
    return format_html(
        '<span style="background:{};color:#fff;padding:2px 10px;'
        'border-radius:12px;font-size:11px;font-weight:600;'
        'letter-spacing:.03em;white-space:nowrap;">{}</span>',
        color, text,
    )


DIFFICULTY_COLORS = {'easy': '#2ecc71', 'medium': '#f39c12', 'hard': '#e74c3c'}
STATUS_COLORS = {
    'created': '#3498db', 'running': '#27ae60', 'finished': '#7f8c8d',
    'active':  '#27ae60', 'expired': '#e74c3c',
}
SESSION_TYPE_COLORS = {
    'exam':     '#e74c3c',
    'training': '#9b59b6',
}
CHOICE_TYPES = {QuestionType.SINGLE_CHOICE, QuestionType.MULTIPLE_CHOICE}


# ── Inlines ───────────────────────────────────────────────────────────────────

class QuestionOptionNestedInline(nested_admin.NestedTabularInline):
    model               = QuestionOption
    extra               = 2
    fields              = ['text', 'is_correct', 'order']
    ordering            = ['order']
    verbose_name        = 'Вариант ответа'
    verbose_name_plural = 'Варианты ответов'


class QuestionNestedInline(nested_admin.NestedStackedInline):
    model               = Question
    extra               = 0
    fields              = ['text', 'question_type', 'difficulty', 'language', 'order']
    ordering            = ['order']
    show_change_link    = True
    verbose_name        = 'Вопрос'
    verbose_name_plural = 'Вопросы'
    inlines             = [QuestionOptionNestedInline]


class QuestionOptionInline(admin.TabularInline):
    model               = QuestionOption
    extra               = 2
    fields              = ['text', 'is_correct', 'order']
    ordering            = ['order']
    verbose_name        = 'Вариант ответа'
    verbose_name_plural = 'Варианты ответов'


class AnswerInline(admin.TabularInline):
    model               = Answer
    extra               = 0
    can_delete          = False
    max_num             = 0
    verbose_name        = 'Ответ пользователя'
    verbose_name_plural = 'Ответы пользователя'
    readonly_fields     = [
        'question_display', 'answer_display',
        'correctness_badge', 'grading_status_badge', 'answered_at',
    ]
    fields = [
        'question_display', 'answer_display',
        'correctness_badge', 'grading_status_badge', 'answered_at',
    ]

    def question_display(self, obj):
        return obj.question.text[:80] if obj and obj.question_id else '—'
    question_display.short_description = 'Вопрос'

    def answer_display(self, obj):
        if not obj:
            return '—'
        if obj.answer_text:
            return obj.answer_text[:120]
        if obj.selected_options:
            return f'Варианты: {", ".join(str(v) for v in obj.selected_options)}'
        return '—'
    answer_display.short_description = 'Ответ'

    def correctness_badge(self, obj):
        if not obj or obj.is_correct is None:
            return _badge('На проверке', '#7f8c8d')
        return _badge('✓ Верно', '#27ae60') if obj.is_correct else _badge('✗ Неверно', '#e74c3c')
    correctness_badge.short_description = 'Результат'

    def grading_status_badge(self, obj):
        if not obj:
            return '—'
        colors = {
            'pending': '#7f8c8d',
            'auto':    '#3498db',
            'ai':      '#9b59b6',
            'manual':  '#f39c12',
        }
        return _badge(
            obj.get_grading_status_display(),
            colors.get(obj.grading_status, '#7f8c8d'),
        )
    grading_status_badge.short_description = 'Проверка'


class AttemptInline(admin.TabularInline):
    model               = StudentAttempt
    extra               = 0
    can_delete          = False
    max_num             = 0
    show_change_link    = True
    verbose_name        = 'Попытка прохождения'
    verbose_name_plural = 'Попытки прохождения'
    readonly_fields     = ['student_name', 'status_badge', 'score', 'started_at', 'finished_at']
    fields              = ['student_name', 'status_badge', 'score', 'started_at', 'finished_at']

    def status_badge(self, obj):
        if not obj:
            return '—'
        return _badge(obj.get_status_display(), STATUS_COLORS.get(obj.status, '#7f8c8d'))
    status_badge.short_description = 'Статус'

    def score_display(self, obj):
        # if not obj or not obj.is_finished:
        #     return '—'
        color = '#27ae60' if obj.score >= 70 else '#e74c3c'
        return format_html('<strong style="color:{};">{:.1f}%</strong>', color, obj.score)
    score_display.short_description = 'Балл'


# ── Test ──────────────────────────────────────────────────────────────────────

@admin.register(Test)
class TestAdmin(nested_admin.NestedModelAdmin):
    resource_classes = [TestResource]
    list_display     = ['title', 'level_badge', 'active_badge', 'question_count_display', 'created_at']
    list_filter      = ['level', 'is_active']
    search_fields    = ['title', 'description']
    ordering         = ['title']
    inlines          = [QuestionNestedInline]
    readonly_fields  = ['created_at', 'updated_at', 'question_count_display']
    fieldsets = [
        ('Основное',   {'fields': ['title', 'description', 'level', 'is_active']}),
        ('Статистика', {
            'fields':  ['question_count_display', 'created_at', 'updated_at'],
            'classes': ['collapse'],
        }),
    ]

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(_qcount=Count('questions'))

    def level_badge(self, obj):
        return _badge(obj.get_level_display(), DIFFICULTY_COLORS.get(obj.level, '#7f8c8d'))
    level_badge.short_description = 'Уровень'
    level_badge.admin_order_field = 'level'

    def active_badge(self, obj):
        return _badge('Активен', '#27ae60') if obj.is_active else _badge('Скрыт', '#7f8c8d')
    active_badge.short_description = 'Статус'
    active_badge.admin_order_field = 'is_active'

    def question_count_display(self, obj):
        count = getattr(obj, '_qcount', None)
        if count is None:
            count = obj.questions.count()
        return format_html('<strong>{}</strong> вопросов', count)
    question_count_display.short_description = 'Кол-во вопросов'
    question_count_display.admin_order_field = '_qcount'


# ── Question ──────────────────────────────────────────────────────────────────

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    resource_classes     = [QuestionResource]
    change_list_template = 'admin/testing/question_change_list.html'

    list_display  = [
        'short_text', 'test_link', 'type_badge', 'difficulty_badge',
        'language', 'order', 'options_link',
    ]
    list_filter   = ['question_type', 'difficulty', 'language', 'test']
    search_fields = ['text', 'test__title']
    ordering      = ['test', 'order']
    inlines       = [QuestionOptionInline]
    readonly_fields = ['created_at', 'options_link']
    fieldsets = [
        ('Основное',   {'fields': ['test', 'text', 'question_type', 'difficulty', 'order']}),
        ('Код / Язык', {'fields': ['language', 'metadata']}),
        ('Системное',  {'fields': ['created_at', 'options_link'], 'classes': ['collapse']}),
    ]

    def get_changeform_initial_data(self, request):
        initial = super().get_changeform_initial_data(request)
        if 'test' in request.GET:
            initial['test'] = request.GET['test']
        return initial

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        obj = form.instance
        if obj.question_type in CHOICE_TYPES:
            opts = obj.options.all()
            if opts.count() < 2:
                self.message_user(
                    request,
                    'Предупреждение: вопрос с выбором должен иметь минимум 2 варианта.',
                    messages.WARNING,
                )
            if not opts.filter(is_correct=True).exists():
                self.message_user(
                    request,
                    'Предупреждение: не отмечен ни один правильный вариант ответа.',
                    messages.WARNING,
                )
        elif obj.options.exists():
            obj.options.all().delete()
            self.message_user(
                request,
                'Варианты ответов удалены — тип вопроса не поддерживает варианты.',
                messages.WARNING,
            )

    def short_text(self, obj):
        return obj.text[:70]
    short_text.short_description = 'Вопрос'

    def test_link(self, obj):
        url = reverse('admin:testing_test_change', args=[obj.test_id])
        return format_html('<a href="{}">{}</a>', url, obj.test.title)
    test_link.short_description = 'Тест'
    test_link.admin_order_field = 'test__title'

    def type_badge(self, obj):
        colors = {
            'single_choice':   '#3498db',
            'multiple_choice': '#9b59b6',
            'text':            '#f39c12',
            'code':            '#e74c3c',
        }
        return _badge(obj.get_question_type_display(), colors.get(obj.question_type, '#7f8c8d'))
    type_badge.short_description = 'Тип'
    type_badge.admin_order_field = 'question_type'

    def difficulty_badge(self, obj):
        return _badge(obj.get_difficulty_display(), DIFFICULTY_COLORS.get(obj.difficulty, '#7f8c8d'))
    difficulty_badge.short_description = 'Сложность'
    difficulty_badge.admin_order_field = 'difficulty'

    def options_link(self, obj):
        if not obj or not obj.pk:
            return '—'
        url   = reverse('admin:testing_questionoption_changelist') + f'?question__id__exact={obj.pk}'
        count = obj.options.count()
        return format_html('<a href="{}">Варианты ({})</a>', url, count)
    options_link.short_description = 'Варианты ответов'


# ── QuestionOption ────────────────────────────────────────────────────────────

@admin.register(QuestionOption)
class QuestionOptionAdmin(admin.ModelAdmin):
    resource_classes = [QuestionOptionResource]
    list_display     = ['text_short', 'question_link', 'correct_badge', 'order']
    list_filter      = ['is_correct', 'question__question_type']
    search_fields    = ['text', 'question__text']
    ordering         = ['question', 'order']

    def text_short(self, obj):
        return obj.text[:80]
    text_short.short_description = 'Вариант'

    def question_link(self, obj):
        url = reverse('admin:testing_question_change', args=[obj.question_id])
        return format_html('<a href="{}">{}</a>', url, obj.question.text[:50])
    question_link.short_description = 'Вопрос'
    question_link.admin_order_field = 'question__text'

    def correct_badge(self, obj):
        return _badge('✓ Верный', '#27ae60') if obj.is_correct else _badge('✗', '#bdc3c7')
    correct_badge.short_description = 'Правильный'
    correct_badge.admin_order_field = 'is_correct'


# ── TestSession ───────────────────────────────────────────────────────────────

@admin.register(TestSession)
class TestSessionAdmin(admin.ModelAdmin):
    resource_classes = [TestSessionResource]
    list_display     = [
        'session_label', 'test_link', 'session_type_badge',
        'status_badge', 'valid_indicator',
        'expires_display', 'attempts_display', 'created_at',
    ]
    list_filter      = ['session_type', 'status', 'is_active', 'test']
    search_fields    = ['key', 'title', 'test__title']
    ordering         = ['-created_at']
    inlines          = [AttemptInline]
    actions          = ['force_expire']
    readonly_fields  = [
        'id', 'key', 'created_at', 'expires_at',
        'valid_indicator', 'expires_display', 'attempts_display',
    ]
    fieldsets = [
        ('Сессия', {
            'fields': [
                'id', 'key', 'test', 'title',
                'session_type', 'max_attempts_per_student',
                'status', 'is_active',
            ],
        }),
        ('Время',   {'fields': ['created_at', 'expires_at', 'valid_indicator', 'expires_display']}),
        ('Попытки', {'fields': ['attempts_display']}),
    ]

    def has_change_permission(self, request, obj=None):
        return True

    def has_delete_permission(self, request, obj=None):
        return False

    def session_label(self, obj):
        if obj.title:
            return format_html(
                '{} <span style="color:#999;font-size:11px;">({})</span>',
                obj.title, obj.key[:12] + '…',
            )
        return obj.key
    session_label.short_description = 'Сессия'

    def session_type_badge(self, obj):
        return _badge(
            obj.get_session_type_display(),
            SESSION_TYPE_COLORS.get(obj.session_type, '#7f8c8d'),
        )
    session_type_badge.short_description = 'Тип'
    session_type_badge.admin_order_field = 'session_type'

    def test_link(self, obj):
        url = reverse('admin:testing_test_change', args=[obj.test_id])
        return format_html('<a href="{}">{}</a>', url, obj.test.title)
    test_link.short_description = 'Тест'
    test_link.admin_order_field = 'test__title'

    def status_badge(self, obj):
        return _badge(obj.get_status_display(), STATUS_COLORS.get(obj.status, '#7f8c8d'))
    status_badge.short_description = 'Статус'
    status_badge.admin_order_field = 'status'

    def valid_indicator(self, obj):
        if not obj or not obj.pk:
            return '—'
        return _badge('✓ Активна', '#27ae60') if obj.is_valid else _badge('✗ Истекла', '#e74c3c')
    valid_indicator.short_description = 'Действительна'

    def expires_display(self, obj):
        if not obj or not obj.pk:
            return '—'
        # Training: время не критично — показываем иначе
        if obj.is_training:
            return format_html('<span style="color:#9b59b6;">∞ Тренажёр</span>')
        now = timezone.now()
        if obj.expires_at < now:
            return format_html(
                '<span style="color:#e74c3c;">Истекла {}</span>',
                obj.expires_at.strftime('%d.%m %H:%M'),
            )
        mins  = int((obj.expires_at - now).total_seconds() / 60)
        color = '#e74c3c' if mins < 15 else '#f39c12' if mins < 60 else '#27ae60'
        return format_html(
            '<span style="color:{};">{}м до истечения ({})</span>',
            color, mins, obj.expires_at.strftime('%H:%M'),
        )
    expires_display.short_description = 'Истекает'

    def attempts_display(self, obj):
        if not obj or not obj.pk:
            return '—'
        total  = obj.attempts.count()
        active = obj.attempts.filter(status=AttemptStatus.ACTIVE).count()
        limit  = obj.max_attempts_per_student
        limit_str = f' / лимит: {limit}' if limit is not None else ' / лимит: ∞'
        return format_html('{} активных / {} всего{}', active, total, limit_str)
    attempts_display.short_description = 'Попытки'

    @admin.action(description='Принудительно завершить сессию')
    def force_expire(self, request, queryset):
        count = 0
        for s in queryset.filter(is_active=True):
            s.deactivate()
            count += 1
        self.message_user(request, f'Завершено сессий: {count}.', messages.SUCCESS)


# ── StudentAttempt ────────────────────────────────────────────────────────────

@admin.register(StudentAttempt)
class StudentAttemptAdmin(admin.ModelAdmin):
    resource_classes = [StudentAttemptResource]
    list_display     = [
        'student_name', 'test_title', 'session_link', 'session_type_badge',
        'status_badge', 'score_display', 'started_at', 'finished_at', 'duration_display',
    ]
    list_filter      = ['status', 'session__session_type', 'session__test', 'started_at']
    search_fields    = ['student_name', 'session__test__title', 'session__key', 'session__title']
    ordering         = ['-started_at']
    inlines          = [AnswerInline]
    readonly_fields  = [
        'id', 'session', 'student_name', 'started_at',
        'finished_at', 'score', 'status', 'duration_display', 'score_display',
    ]
    fieldsets = [
        ('Студент',   {'fields': ['id', 'student_name', 'session']}),
        ('Результат', {
            'fields': ['status', 'score_display', 'started_at', 'finished_at', 'duration_display'],
        }),
    ]

    def has_add_permission(self, request):
        return False

    def test_title(self, obj):
        return obj.session.test.title if obj and obj.session_id else '—'
    test_title.short_description = 'Тест'
    test_title.admin_order_field = 'session__test__title'

    def session_link(self, obj):
        if not obj or not obj.session_id:
            return '—'
        url   = reverse('admin:testing_testsession_change', args=[obj.session_id])
        label = obj.session.title or obj.session.key[:16]
        return format_html('<a href="{}">{}</a>', url, label)
    session_link.short_description = 'Сессия'

    def session_type_badge(self, obj):
        if not obj or not obj.session_id:
            return '—'
        return _badge(
            obj.session.get_session_type_display(),
            SESSION_TYPE_COLORS.get(obj.session.session_type, '#7f8c8d'),
        )
    session_type_badge.short_description = 'Тип сессии'
    session_type_badge.admin_order_field = 'session__session_type'

    def status_badge(self, obj):
        if not obj:
            return '—'
        return _badge(obj.get_status_display(), STATUS_COLORS.get(obj.status, '#7f8c8d'))
    status_badge.short_description = 'Статус'
    status_badge.admin_order_field = 'status'

    def score_display(self, obj):
        if not obj or not obj.is_finished:
            return '—'
        color = '#27ae60' if obj.score >= 70 else '#f39c12' if obj.score >= 40 else '#e74c3c'
        return format_html('<strong style="font-size:15px;color:{};">{}%</strong>', color, obj.score)

    score_display.short_description = 'Балл'
    score_display.admin_order_field = 'score'

    def duration_display(self, obj):
        if not obj:
            return '—'
        secs = obj.duration_seconds
        if secs is None:
            return '—'
        m, s = divmod(int(secs), 60)
        return f'{m}м {s}с'
    duration_display.short_description = 'Длительность'


# ── Answer ────────────────────────────────────────────────────────────────────

@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    resource_classes = [AnswerResource]
    list_display     = [
        'student_name', 'question_short', 'answer_preview',
        'correctness_badge', 'grading_status_badge', 'answered_at',
    ]
    list_filter      = ['is_correct', 'grading_status', 'question__question_type']
    search_fields    = ['attempt__student_name', 'question__text']
    ordering         = ['-answered_at']
    readonly_fields  = [f.name for f in Answer._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def student_name(self, obj):
        return obj.attempt.student_name if obj and obj.attempt_id else '—'
    student_name.short_description = 'Студент'
    student_name.admin_order_field = 'attempt__student_name'

    def question_short(self, obj):
        return obj.question.text[:60] if obj and obj.question_id else '—'
    question_short.short_description = 'Вопрос'

    def answer_preview(self, obj):
        if not obj:
            return '—'
        if obj.answer_text:
            return obj.answer_text[:80]
        if obj.selected_options:
            return f'{len(obj.selected_options)} вариант(а/ов)'
        return '—'
    answer_preview.short_description = 'Ответ'

    def correctness_badge(self, obj):
        if not obj or obj.is_correct is None:
            return _badge('На проверке', '#7f8c8d')
        return _badge('✓ Верно', '#27ae60') if obj.is_correct else _badge('✗ Неверно', '#e74c3c')
    correctness_badge.short_description = 'Результат'
    correctness_badge.admin_order_field = 'is_correct'

    def grading_status_badge(self, obj):
        if not obj:
            return '—'
        colors = {
            'pending': '#7f8c8d',
            'auto':    '#3498db',
            'ai':      '#9b59b6',
            'manual':  '#f39c12',
        }
        return _badge(
            obj.get_grading_status_display(),
            colors.get(obj.grading_status, '#7f8c8d'),
        )
    grading_status_badge.short_description = 'Проверка'
    grading_status_badge.admin_order_field = 'grading_status'


from django.contrib.auth.models import Group, User  # noqa: E402
from django.contrib import admin
from django_celery_beat.models import CrontabSchedule
from django_celery_beat.models import IntervalSchedule, SolarSchedule

admin.site.unregister(IntervalSchedule)
admin.site.unregister(SolarSchedule)
admin.site.unregister(CrontabSchedule)
admin.site.unregister(Group)
admin.site.unregister(User)