from __future__ import annotations

import json as _json
import logging

import nested_admin
from django.contrib import admin, messages
from django.db.models import Avg, Count, DurationField, ExpressionWrapper, F, Q
from django.urls import path as _path, reverse
from django.utils import timezone
from django.utils.html import format_html

from .models import (
    Answer, AttemptStatus, GradingStatus, Question, QuestionOption,
    QuestionType, StudentAttempt, Test, TestSession,
)
from .resources import (
    AnswerResource, QuestionOptionResource, QuestionResource,
    StudentAttemptResource, TestResource, TestSessionResource,
)

logger = logging.getLogger(__name__)

PASS_SCORE = 75


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
GRADING_COLORS = {
    'pending':    '#7f8c8d',
    'processing': '#f39c12',
    'auto':       '#3498db',
    'ai':         '#9b59b6',
    'done':       '#27ae60',
    'failed':     '#e74c3c',
    'manual':     '#e67e22',
}
CHOICE_TYPES = {QuestionType.SINGLE_CHOICE, QuestionType.MULTIPLE_CHOICE}



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
    verbose_name        = 'Ответ студента'
    verbose_name_plural = 'Ответы студента'
    readonly_fields     = [
        'question_display', 'answer_display',
        'correctness_badge', 'grading_status_badge', 'answered_at',
        'review_link',
    ]
    fields = [
        'question_display', 'answer_display',
        'correctness_badge', 'grading_status_badge', 'answered_at',
        'review_link',
    ]

    def get_queryset(self, request):
        return (
            super().get_queryset(request)
            .select_related('question')
        )

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
        return _badge(
            obj.get_grading_status_display(),
            GRADING_COLORS.get(obj.grading_status, '#7f8c8d'),
        )
    grading_status_badge.short_description = 'Статус проверки'

    def review_link(self, obj):
        if not obj or not obj.pk:
            return '—'
        if obj.question.question_type not in ('text', 'code'):
            return '—'
        if obj.grading_status not in ('pending', 'failed'):
            return _badge('Проверено', '#27ae60')
        url = reverse('admin:testing_manual_review_detail', args=[obj.pk])
        return format_html(
            '<a href="{}" style="background:#e74c3c;color:#fff;padding:3px 10px;'
            'border-radius:6px;font-size:11px;font-weight:700;text-decoration:none;">'
            '🔍 Проверить</a>',
            url,
        )
    review_link.short_description = 'Действие'


class AttemptInline(admin.TabularInline):
    model               = StudentAttempt
    extra               = 0
    can_delete          = False
    max_num             = 0
    show_change_link    = True
    verbose_name        = 'Попытка'
    verbose_name_plural = 'Попытки'
    readonly_fields     = [
        'student_name', 'status_badge', 'score_display',
        'started_at', 'finished_at', 'review_answers_link',
    ]
    fields = [
        'student_name', 'status_badge', 'score_display',
        'started_at', 'finished_at', 'review_answers_link',
    ]

    def status_badge(self, obj):
        if not obj:
            return '—'
        return _badge(obj.get_status_display(), STATUS_COLORS.get(obj.status, '#7f8c8d'))
    status_badge.short_description = 'Статус'

    def score_display(self, obj):
        if not obj or not obj.is_finished:
            return '—'
        color = '#27ae60' if obj.score >= 70 else '#e74c3c'
        return format_html('<strong style="color:{};">{:.1f}%</strong>', color, obj.score)
    score_display.short_description = 'Балл'

    def review_answers_link(self, obj):
        if not obj or not obj.pk:
            return '—'
        url = reverse('admin:testing_studentattempt_change', args=[obj.pk])
        return format_html(
            '<a href="{}">📋 Ответы</a>', url
        )
    review_answers_link.short_description = 'Ответы'


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
                self.message_user(request, 'Предупреждение: вопрос с выбором должен иметь минимум 2 варианта.', messages.WARNING)
            if not opts.filter(is_correct=True).exists():
                self.message_user(request, 'Предупреждение: не отмечен ни один правильный вариант ответа.', messages.WARNING)
        elif obj.options.exists():
            obj.options.all().delete()
            self.message_user(request, 'Варианты ответов удалены — тип вопроса не поддерживает варианты.', messages.WARNING)

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



@admin.register(TestSession)
class TestSessionAdmin(admin.ModelAdmin):
    resource_classes = [TestSessionResource]
    list_display     = [
        'session_label', 'test_link', 'session_type_badge',
        'status_badge',
        'expires_display', 'pending_answers_display',
        'created_at', 'review_link',
    ]
    list_filter      = ['session_type', 'status', 'is_active', 'test']
    search_fields    = ['key', 'title', 'test__title']
    ordering         = ['-created_at']
    inlines          = [AttemptInline]
    actions          = ['force_expire']
    readonly_fields  = [
        'id', 'key', 'created_at', 'expires_at',
        'valid_indicator', 'expires_display',
        'attempts_display', 'kpi_summary', 'pending_answers_display',
        'review_link',
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
        ('Попытки', {'fields': ['attempts_display', 'pending_answers_display']}),
        ('Навигация', {'fields': ['review_link']}),
        ('KPI', {'fields': ['kpi_summary']}),
    ]

    def get_queryset(self, request):
        return (
            super().get_queryset(request)
            .select_related('test')
            .annotate(
                _pending_answers=Count(
                    'attempts__answers',
                    filter=Q(
                        attempts__answers__grading_status='pending',
                        attempts__answers__question__question_type__in=['text', 'code'],
                    ),
                )
            )
        )

    def pending_answers_display(self, obj):
        count = getattr(obj, '_pending_answers', None)
        if count is None:
            count = Answer.objects.filter(
                attempt__session=obj,
                grading_status=GradingStatus.PENDING,
                question__question_type__in=['text', 'code'],
            ).count()
        if count == 0:
            return _badge('0 ожидают', '#27ae60')
        return format_html(
            '<span style="background:#e74c3c;color:#fff;padding:2px 10px;'
            'border-radius:12px;font-size:11px;font-weight:700;">'
            ' {} ожидают</span>', count
        )
    pending_answers_display.short_description = 'На проверке'

    def review_link(self, obj):
        if not obj or not obj.pk:
            return '—'

        url = reverse('admin:testing_manual_review_list') + f'?session={obj.pk}'

        return format_html(
            '''
            <a href="{}" class="btn btn-danger btn-sm">
                <i class="bi bi-clipboard-check"></i>
                Ответы на проверке
            </a>
            ''',
            url
        )
    review_link.short_description = 'Проверка'

    def kpi_summary(self, obj):
        if not obj or not obj.pk:
            return "—"
        from django.db.models import Avg as _Avg
        stats = obj.attempts.filter(status='finished').aggregate(
            total=Count('id'),
            passed=Count('id', filter=Q(score__gte=PASS_SCORE)),
            failed=Count('id', filter=Q(score__lt=PASS_SCORE)),
            avg=_Avg('score'),
        )
        total   = stats['total'] or 0
        passed  = stats['passed'] or 0
        failed  = stats['failed'] or 0
        avg     = round(stats['avg'] or 0, 2)
        percent = round((passed / total) * 100, 1) if total > 0 else 0
        color   = '#dc2626' if percent < 50 else '#f59e0b' if percent < 75 else '#16a34a'

        return format_html(
            '''<div style="background:#fff;border:1px solid #e5e7eb;border-radius:10px;
                padding:14px;max-width:340px;">
               <div style="font-size:12px;color:#9ca3af;margin-bottom:6px;">Статистика сессии</div>
               <table style="width:100%;font-size:13px;border-collapse:collapse;">
                 <tr><td style="padding:5px 0;color:#6b7280;">Всего студентов</td>
                     <td style="padding:5px 0;text-align:right;"><b>{total}</b></td></tr>
                 <tr><td style="padding:5px 0;color:#6b7280;">Успешно завершили</td>
                     <td style="padding:5px 0;text-align:right;color:#16a34a;"><b>{passed}</b></td></tr>
                 <tr><td style="padding:5px 0;color:#6b7280;">Не прошли</td>
                     <td style="padding:5px 0;text-align:right;color:#dc2626;"><b>{failed}</b></td></tr>
                 <tr><td style="padding:7px 0;border-top:1px solid #f1f5f9;color:#6b7280;">Доля прохождения</td>
                     <td style="padding:7px 0;border-top:1px solid #f1f5f9;text-align:right;color:{color};"><b>{percent}%</b></td></tr>
                 <tr><td style="padding:5px 0;color:#6b7280;">Средний результат</td>
                     <td style="padding:5px 0;text-align:right;"><b>{avg}</b></td></tr>
               </table>
               <div style="margin-top:8px;height:6px;background:#f1f5f9;border-radius:4px;overflow:hidden;">
                 <div style="width:{percent}%;height:100%;background:{color};"></div>
               </div>
             </div>''',
            total=total, passed=passed, failed=failed,
            percent=percent, avg=avg, color=color,
        )
    kpi_summary.short_description = "KPI"

    def session_label(self, obj):
        if obj.title:
            return format_html(
                '{} <span style="color:#999;font-size:11px;">({})</span>',
                obj.title, obj.key[:12] + '…',
            )
        return obj.key
    session_label.short_description = 'Сессия'

    def session_type_badge(self, obj):
        return _badge(obj.get_session_type_display(), SESSION_TYPE_COLORS.get(obj.session_type, '#7f8c8d'))
    session_type_badge.short_description = 'Тип'
    session_type_badge.admin_order_field = 'session_type'

    def test_link(self, obj):
        url = reverse('admin:testing_test_change', args=[obj.test_id])
        return format_html('<a href="{}">{}</a>', url, obj.test.title)
    test_link.short_description = 'Тест'
    test_link.admin_order_field = 'test__title'

    def status_badge(self, obj):
        effective = obj.effective_status
        return _badge(
            obj.get_status_display() if effective == obj.status else 'Завершена',
            STATUS_COLORS.get(effective, '#7f8c8d'),
        )
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
        if obj.is_training:
            return format_html('<span style="color:#9b59b6;">∞ Тренажёр</span>')
        now = timezone.now()
        if obj.expires_at < now:
            return format_html('<span style="color:#e74c3c;">Истекла {}</span>', obj.expires_at.strftime('%d.%m %H:%M'))
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


@admin.register(StudentAttempt)
class StudentAttemptAdmin(admin.ModelAdmin):
    resource_classes = [StudentAttemptResource]
    list_display     = [
        'student_name',  'session_link', 'session_type_badge',
        'status_badge', 'score_display',
        'pending_count_display',
        'started_at', 'duration_display',
        'review_answers_btn',
    ]
    list_filter      = ['status', 'session__session_type', 'session__test', 'started_at']
    search_fields    = ['student_name', 'session__test__title', 'session__key', 'session__title']
    ordering         = ['-started_at']
    inlines          = [AnswerInline]
    actions          = ['bulk_approve_pending', 'bulk_reject_pending']
    readonly_fields  = [
        'id', 'session', 'student_name', 'started_at', 'finished_at',
        'score', 'status', 'duration_display', 'score_display',
        'correct_count_display', 'wrong_count_display', 'pending_count_display',
        'completion_display', 'review_answers_btn',
    ]
    fieldsets = [
        ('Студент',    {'fields': ['id', 'student_name', 'session']}),
        ('Результат',  {'fields': ['status', 'score_display', 'started_at', 'finished_at', 'duration_display']}),
        ('Ответы',     {'fields': ['correct_count_display', 'wrong_count_display', 'pending_count_display', 'completion_display']}),
        ('Навигация',  {'fields': ['review_answers_btn']}),
    ]

    def get_queryset(self, request):
        return (
            super().get_queryset(request)
            .select_related('session', 'session__test')
            .annotate(
                _correct=Count('answers', filter=Q(answers__is_correct=True)),
                _wrong=Count('answers', filter=Q(answers__is_correct=False)),
                _pending=Count(
                    'answers',
                    filter=Q(
                        answers__grading_status='pending',
                        answers__question__question_type__in=['text', 'code'],
                    )
                ),
                _total_answers=Count('answers'),
            )
        )

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
        return _badge(obj.session.get_session_type_display(), SESSION_TYPE_COLORS.get(obj.session.session_type, '#7f8c8d'))
    session_type_badge.short_description = 'Тип сессии'

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

    def correct_count_display(self, obj):
        count = getattr(obj, '_correct', None)
        if count is None:
            count = obj.answers.filter(is_correct=True).count()
        return format_html(
            '<span style="background:#d1fae5;color:#065f46;padding:2px 8px;'
            'border-radius:10px;font-size:12px;font-weight:700;">✓ {}</span>', count
        )
    correct_count_display.short_description = 'Правильных'
    correct_count_display.admin_order_field = '_correct'

    def wrong_count_display(self, obj):
        count = getattr(obj, '_wrong', None)
        if count is None:
            count = obj.answers.filter(is_correct=False).count()
        return format_html(
            '<span style="background:#fee2e2;color:#991b1b;padding:2px 8px;'
            'border-radius:10px;font-size:12px;font-weight:700;">✗ {}</span>', count
        )
    wrong_count_display.short_description = 'Неправильных'
    wrong_count_display.admin_order_field = '_wrong'

    def pending_count_display(self, obj):
        count = getattr(obj, '_pending', None)

        if count is None:
            count = obj.answers.filter(
                grading_status='pending',
                question__question_type__in=['text', 'code'],
            ).count()

        if count == 0:
            return format_html(
                '''
                <span style="
                    background:#ecfdf5;
                    color:#059669;
                    border:1px solid #a7f3d0;
                    padding:5px 12px;
                    border-radius:999px;
                    font-size:12px;
                    font-weight:600;
                ">
                    <i class="bi bi-check-circle-fill"></i>
                    0
                </span>
                '''
            )

        return format_html(
            '''
            <span style="
                background:#fffbeb;
                color:#b45309;
                border:1px solid #fde68a;
                padding:5px 12px;
                border-radius:999px;
                font-size:12px;
                font-weight:600;
            ">
                <i class="bi bi-hourglass-split"></i>
                {}
            </span>
            ''',
            count
        )
    pending_count_display.short_description = 'На проверке'
    pending_count_display.admin_order_field = '_pending'

    def completion_display(self, obj):
        total_answers = getattr(obj, '_total_answers', None)
        if total_answers is None:
            total_answers = obj.answers.count()
        from apps.testing.services.question_selector import TOTAL_QUESTIONS
        pct = round((total_answers / TOTAL_QUESTIONS) * 100) if TOTAL_QUESTIONS else 0
        color = '#27ae60' if pct >= 100 else '#f39c12' if pct >= 50 else '#e74c3c'
        return format_html(
            '<div style="display:flex;align-items:center;gap:6px;">'
            '<div style="width:60px;height:6px;background:#f1f5f9;border-radius:3px;overflow:hidden;">'
            '<div style="width:{}%;height:100%;background:{};border-radius:3px;"></div></div>'
            '<span style="font-size:12px;font-weight:700;color:{};">{}%</span>'
            '</div>',
            min(pct, 100), color, color, pct,
        )
    completion_display.short_description = '% выполнения'

    def review_answers_btn(self, obj):
        if not obj or not obj.pk:
            return '—'

        url = reverse('admin:testing_answer_changelist') + f'?attempt__id__exact={obj.pk}'

        return format_html(
            '''
            <a href="{}"
               style="
                    background:#eff6ff;
                    color:#2563eb;
                    border:1px solid #bfdbfe;
                    padding:8px 14px;
                    border-radius:12px;
                    font-size:13px;
                    font-weight:600;
                    text-decoration:none;
                    display:inline-flex;
                    align-items:center;
                    gap:6px;
               ">
               <i class="fas fa-check-circle"></i>
               Проверить ответы
            </a>
            ''',
            url,
        )
    review_answers_btn.short_description = 'Действие'

    def duration_display(self, obj):
        if not obj:
            return '—'
        secs = obj.duration_seconds
        if secs is None:
            return '—'
        m, s = divmod(int(secs), 60)
        return f'{m}м {s}с'
    duration_display.short_description = 'Длительность'

    @admin.action(description='✅ Засчитать все pending-ответы выбранных попыток')
    def bulk_approve_pending(self, request, queryset):
        self._bulk_grade_pending(request, queryset, is_correct=True)

    @admin.action(description='❌ Не засчитать все pending-ответы выбранных попыток')
    def bulk_reject_pending(self, request, queryset):
        self._bulk_grade_pending(request, queryset, is_correct=False)

    def _bulk_grade_pending(self, request, queryset, is_correct: bool):
        from django.db import transaction as _tx
        count = 0
        with _tx.atomic():
            for attempt in queryset.prefetch_related('answers'):
                pending = attempt.answers.filter(
                    grading_status=GradingStatus.PENDING,
                    question__question_type__in=['text', 'code'],
                )
                updated = pending.update(
                    is_correct=is_correct,
                    grading_status=GradingStatus.MANUAL,
                )
                count += updated
                if updated:
                    attempt._recalculate_score()
                    attempt.save(update_fields=['score'])
        label = 'Засчитано' if is_correct else 'Не засчитано'
        self.message_user(request, f'{label}: {count} ответов. Баллы пересчитаны.', messages.SUCCESS)


class GradingStatusFilter(admin.SimpleListFilter):
    title        = 'Статус проверки'
    parameter_name = 'grading_status'

    LABELS = {
        'pending':    '🔴 Ожидает проверки',
        'processing': '🟡 Обрабатывается',
        'auto':       '🔵 Авто',
        'done':       '🟢 Проверено (AI)',
        'manual':     '🟠 Проверено вручную',
        'failed':     '⚫ Ошибка AI',
    }

    def lookups(self, request, model_admin):
        return list(self.LABELS.items())

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(grading_status=self.value())
        return queryset


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    resource_classes = [AnswerResource]
    list_display     = [
        'student_name_link', 'test_name', 'session_name',
        'question_short', 'question_type_badge',
        'answer_preview', 'correctness_badge', 'grading_status_badge',
        'ai_score_display', 'answered_at', 'quick_grade_btn',
    ]
    list_filter      = [GradingStatusFilter, 'question__question_type', 'is_correct']
    search_fields    = [
        'attempt__student_name',
        'question__text',
        'attempt__session__test__title',
        'attempt__session__title',
    ]
    ordering         = ['-answered_at']
    actions          = ['action_approve', 'action_reject']
    readonly_fields  = [f.name for f in Answer._meta.fields] + ['student_detail_link']

    def get_queryset(self, request):
        return (
            super().get_queryset(request)
            .select_related(
                'attempt',
                'attempt__session',
                'attempt__session__test',
                'question',
            )
        )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return True

    def student_name_link(self, obj):
        if not obj or not obj.attempt_id:
            return '—'
        url = reverse('admin:testing_studentattempt_change', args=[obj.attempt_id])
        return format_html('<a href="{}">{}</a>', url, obj.attempt.student_name)
    student_name_link.short_description = 'Студент'
    student_name_link.admin_order_field = 'attempt__student_name'

    def test_name(self, obj):
        if not obj or not obj.attempt_id:
            return '—'
        return obj.attempt.session.test.title
    test_name.short_description = 'Тест'
    test_name.admin_order_field = 'attempt__session__test__title'

    def session_name(self, obj):
        if not obj or not obj.attempt_id:
            return '—'
        s = obj.attempt.session
        return s.title or s.key[:16]
    session_name.short_description = 'Сессия'

    def question_short(self, obj):
        return obj.question.text[:60] if obj and obj.question_id else '—'
    question_short.short_description = 'Вопрос'

    def question_type_badge(self, obj):
        if not obj or not obj.question_id:
            return '—'
        colors = {
            'single_choice':   '#3498db',
            'multiple_choice': '#9b59b6',
            'text':            '#f39c12',
            'code':            '#e74c3c',
        }
        return _badge(obj.question.get_question_type_display(), colors.get(obj.question.question_type, '#7f8c8d'))
    question_type_badge.short_description = 'Тип'

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
        return _badge(
            obj.get_grading_status_display(),
            GRADING_COLORS.get(obj.grading_status, '#7f8c8d'),
        )
    grading_status_badge.short_description = 'Статус проверки'
    grading_status_badge.admin_order_field = 'grading_status'

    def ai_score_display(self, obj):
        if not obj or obj.ai_score is None:
            return '—'
        color = '#27ae60' if obj.ai_score >= 6 else '#f39c12' if obj.ai_score >= 4 else '#e74c3c'
        conf = f' ({int((obj.ai_confidence or 0) * 100)}%)' if obj.ai_confidence else ''
        return format_html(
            '<span style="color:{};font-weight:700;">{}/10{}</span>',
            color, obj.ai_score, conf,
        )
    ai_score_display.short_description = 'AI оценка'

    def student_detail_link(self, obj):
        if not obj or not obj.attempt_id:
            return '—'
        url = reverse('admin:testing_studentattempt_change', args=[obj.attempt_id])
        return format_html('<a href="{}">Открыть попытку</a>', url)
    student_detail_link.short_description = 'Попытка студента'

    def quick_grade_btn(self, obj):
        if not obj or not obj.pk:
            return '—'

        if obj.question.question_type not in ('text', 'code'):
            return '—'

        if obj.grading_status not in ('pending', 'failed'):
            return format_html(
                '''
                <span style="
                    background:#ecfdf5;
                    color:#059669;
                    border:1px solid #a7f3d0;
                    padding:4px 10px;
                    border-radius:999px;
                    font-size:12px;
                    font-weight:600;
                ">
                    <i class="bi bi-check-circle-fill"></i>
                    Проверено
                </span>
                '''
            )

        url = reverse('admin:testing_manual_review_detail', args=[obj.pk])

        return format_html(
            '''
            <a href="{}"
               style="
                    background:#eff6ff;
                    color:#2563eb;
                    border:1px solid #bfdbfe;
                    padding:6px 12px;
                    border-radius:10px;
                    font-size:12px;
                    font-weight:600;
                    text-decoration:none;
                    display:inline-flex;
                    align-items:center;
                    gap:6px;
                ">
                <i class="bi bi-search"></i>
                Проверить
            </a>
            ''',
            url,
        )
    quick_grade_btn.short_description = 'Действие'

    @admin.action(description='✅ Засчитать выбранные ответы')
    def action_approve(self, request, queryset):
        self._grade_queryset(request, queryset, is_correct=True)

    @admin.action(description='❌ Отклонить выбранные ответы')
    def action_reject(self, request, queryset):
        self._grade_queryset(request, queryset, is_correct=False)

    def _grade_queryset(self, request, queryset, is_correct: bool):
        from django.db import transaction as _tx
        attempt_ids = set()
        count = 0
        with _tx.atomic():
            for answer in queryset.select_related('attempt'):
                answer.is_correct = is_correct
                answer.grading_status = GradingStatus.MANUAL
                answer.save(update_fields=['is_correct', 'grading_status'])
                attempt_ids.add(answer.attempt_id)
                count += 1
            for attempt in StudentAttempt.objects.filter(pk__in=attempt_ids):
                attempt._recalculate_score()
                attempt.save(update_fields=['score'])
        label = 'Засчитано' if is_correct else 'Не засчитано'
        self.message_user(request, f'{label}: {count} ответов. Баллы пересчитаны.', messages.SUCCESS)


from django.contrib.auth.models import Group, User  # noqa: E402
from django.contrib import admin  # noqa: F811

from django_celery_beat.models import CrontabSchedule, IntervalSchedule, SolarSchedule, ClockedSchedule, PeriodicTask
from django_celery_results.models import TaskResult, GroupResult

for _m in [GroupResult, TaskResult, PeriodicTask, ClockedSchedule, IntervalSchedule, SolarSchedule, CrontabSchedule, Group, User]:
    try:
        admin.site.unregister(_m)
    except admin.sites.NotRegistered:
        pass



from django.contrib.admin.views.decorators import staff_member_required as _smd
from django.http import HttpResponse as _HR
from django.urls import path as _path
from django.shortcuts import render as _render
from django.contrib.admin import site as _site


class _FakeOptsKPI:
    app_label = "testing"
    model_name = "kpidashboard"
    verbose_name = "KPI Dashboard"
    verbose_name_plural = "KPI Dashboard"


@_smd
def kpi_dashboard_view(request):
    from apps.testing.services.kpi_service import KPIService, KPIFilters

    period   = request.GET.get("period", "all")
    test_id  = request.GET.get("test_id") or None
    date_from = request.GET.get("date_from", "").strip() or None
    date_to   = request.GET.get("date_to", "").strip() or None
    if period not in ("today", "7d", "30d", "all", "custom"):
        period = "all"
    if date_from or date_to:
        period = "custom"

    filters = KPIFilters(period=period, test_id=test_id, date_from=date_from, date_to=date_to)
    data    = KPIService.get_dashboard(filters)

    ctx = {
        **_site.each_context(request),
        "title": "KPI Dashboard",
        "data": data,
        "filters": filters,
        "period": period,
        "test_id": test_id or "",
        "date_from": date_from or "",
        "date_to": date_to or "",
        "periods": [
            ("today", "Сегодня"), ("7d", "7 дней"),
            ("30d", "30 дней"), ("all", "Всё время"),
        ],
        "chart_attempts_json": _json.dumps(data["chart_attempts"]),
        "chart_scores_json":   _json.dumps(data["chart_scores"]),
        "question_types_json": _json.dumps(data["question_types"]),
        "difficulties_json":   _json.dumps(data["difficulties"]),
        "languages_json":      _json.dumps(data["languages"]),
        "opts": _FakeOptsKPI(),
        # Ссылка на ручную проверку с дашборда KPI
        "manual_review_url": "/admin/testing/manual-review/",
        "review_dashboard_url": "/admin/testing/review-dashboard/",
    }
    return _render(request, "admin/testing/kpi_dashboard.html", ctx)


@_smd
def kpi_export_view(request):
    from apps.testing.services.kpi_service import KPIService, KPIFilters, export_kpi_excel
    period   = request.GET.get("period", "all")
    test_id  = request.GET.get("test_id") or None
    date_from = request.GET.get("date_from", "").strip() or None
    date_to   = request.GET.get("date_to", "").strip() or None
    if date_from or date_to:
        period = "custom"
    filters = KPIFilters(period=period, test_id=test_id, date_from=date_from, date_to=date_to)
    data    = KPIService.get_dashboard(filters)
    xlsx    = export_kpi_excel(data)
    label   = f"{date_from or ''}__{date_to or ''}" if filters.is_custom_range else period
    resp = _HR(xlsx, content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    resp["Content-Disposition"] = f'attachment; filename="kpi_{label}.xlsx"'
    return resp


from django.contrib.admin import site as _admin_site
from .analytics.views import (
    session_list_view,
    session_detail_view,
    session_export_view,
    multi_session_analytics_view,
    multi_session_export_view,
)
from django.http import HttpResponseRedirect as _Redirect


def analyze_selected_sessions(modeladmin, request, queryset):
    ids = list(queryset.values_list("id", flat=True))
    if not ids:
        modeladmin.message_user(request, "Не выбрано ни одной сессии.", messages.WARNING)
        return
    ids_csv = ",".join(str(i) for i in ids)
    return _Redirect(f"/admin/analytics/multi/?sessions={ids_csv}")

analyze_selected_sessions.short_description = " Мультисессионная аналитика"

try:
    if analyze_selected_sessions not in (TestSessionAdmin.actions or []):
        TestSessionAdmin.actions = list(TestSessionAdmin.actions or []) + [analyze_selected_sessions]
except Exception:
    pass

from .review_admin_views import (
    review_dashboard_view,
    review_list_view,
    review_detail_view,
    review_grade_view,
    review_quick_grade_view,
    review_bulk_grade_view,
)

_original_get_urls = _admin_site.__class__.get_urls


def _patched_get_urls(self):
    custom = [
        _path("testing/kpi/",         kpi_dashboard_view, name="testing_kpi_dashboard"),
        _path("testing/kpi/export/",  kpi_export_view,    name="testing_kpi_export"),

        _path("testing/review-dashboard/",                    review_dashboard_view,    name="testing_review_dashboard"),
        _path("testing/manual-review/",                       review_list_view,         name="testing_manual_review_list"),
        _path("testing/manual-review/<uuid:answer_id>/",      review_detail_view,       name="testing_manual_review_detail"),
        _path("testing/manual-review/<uuid:answer_id>/grade/", review_grade_view,       name="testing_manual_review_grade"),
        _path("testing/manual-review/quick-grade/",           review_quick_grade_view,  name="testing_manual_review_quick_grade"),
        _path("testing/manual-review/bulk-grade/",            review_bulk_grade_view,   name="testing_manual_review_bulk_grade"),

        _path("analytics/sessions/",                        session_list_view,              name="analytics_session_list"),
        _path("analytics/sessions/<str:session_id>/",       session_detail_view,            name="analytics_session_detail"),
        _path("analytics/sessions/<str:session_id>/export/", session_export_view,           name="analytics_session_export"),
        _path("analytics/multi/",                           multi_session_analytics_view,   name="analytics_multi"),
        _path("analytics/multi/export/",                    multi_session_export_view,      name="analytics_multi_export"),
    ]
    return custom + _original_get_urls(self)


_admin_site.__class__.get_urls = _patched_get_urls