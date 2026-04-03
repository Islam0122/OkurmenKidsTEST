from django.contrib import admin, messages
from django.db.models import Count
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html

from .models import (
    Answer, AttemptStatus, Question, QuestionOption,
    QuestionType, StudentAttempt, Test, TestSession,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _badge(text, color):
    return format_html(
        '<span style="background:{};color:#fff;padding:2px 8px;'
        'border-radius:10px;font-size:11px;font-weight:600;">{}</span>',
        color, text,
    )


DIFFICULTY_COLORS = {
    'easy':   '#27ae60',
    'medium': '#f39c12',
    'hard':   '#e74c3c',
}

STATUS_COLORS = {
    'created':  '#3498db',
    'running':  '#27ae60',
    'finished': '#95a5a6',
    'active':   '#27ae60',
    'expired':  '#e74c3c',
}

CHOICE_TYPES = {QuestionType.SINGLE_CHOICE, QuestionType.MULTIPLE_CHOICE}


# ── Inlines ───────────────────────────────────────────────────────────────────

class QuestionInline(admin.TabularInline):
    model               = Question
    extra               = 0
    fields              = ['text', 'question_type', 'difficulty', 'order', 'language']
    ordering            = ['order']
    show_change_link    = True
    verbose_name        = 'Вопрос'
    verbose_name_plural = 'Вопросы'


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
    verbose_name        = 'Ответ'
    verbose_name_plural = 'Ответы студента'
    readonly_fields     = ['question_display', 'answer_display', 'correctness_badge', 'answered_at']
    fields              = ['question_display', 'answer_display', 'correctness_badge', 'answered_at']

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
            return _badge('На проверке', '#95a5a6')
        return _badge('✓ Верно', '#27ae60') if obj.is_correct else _badge('✗ Неверно', '#e74c3c')
    correctness_badge.short_description = 'Результат'


class AttemptInline(admin.TabularInline):
    model               = StudentAttempt
    extra               = 0
    can_delete          = False
    max_num             = 0
    show_change_link    = True
    verbose_name        = 'Попытка'
    verbose_name_plural = 'Попытки студентов'
    readonly_fields     = ['student_name', 'status_badge', 'score_display', 'started_at', 'finished_at']
    fields              = ['student_name', 'status_badge', 'score_display', 'started_at', 'finished_at']

    def status_badge(self, obj):
        if not obj:
            return '—'
        color = STATUS_COLORS.get(obj.status, '#95a5a6')
        return _badge(obj.get_status_display(), color)
    status_badge.short_description = 'Статус'

    def score_display(self, obj):
        if not obj or not obj.is_finished:
            return '—'
        color = '#27ae60' if obj.score >= 70 else '#e74c3c'
        return format_html('<strong style="color:{};">{:.1f}%</strong>', color, obj.score)
    score_display.short_description = 'Балл'


# ── Test ──────────────────────────────────────────────────────────────────────

@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    list_display    = ['title', 'level_badge', 'active_badge', 'question_count_display', 'created_at']
    list_filter     = ['level', 'is_active']
    search_fields   = ['title', 'description']
    ordering        = ['title']
    inlines         = [QuestionInline]
    readonly_fields = ['created_at', 'updated_at', 'question_count_display']
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
        color = DIFFICULTY_COLORS.get(obj.level, '#95a5a6')
        return _badge(obj.get_level_display(), color)
    level_badge.short_description = 'Уровень'

    def active_badge(self, obj):
        return _badge('Активен', '#27ae60') if obj.is_active else _badge('Скрыт', '#95a5a6')
    active_badge.short_description = 'Статус'

    def question_count_display(self, obj):
        count = getattr(obj, '_qcount', None)
        if count is None:
            count = obj.questions.count()
        return format_html('<strong>{}</strong> вопросов', count)
    question_count_display.short_description = 'Вопросов'
    question_count_display.admin_order_field = '_qcount'


# ── Question ──────────────────────────────────────────────────────────────────

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display    = [
        'short_text', 'test', 'type_badge', 'difficulty_badge',
        'language', 'order', 'options_link',
    ]
    list_filter     = ['question_type', 'difficulty', 'language', 'test']
    search_fields   = ['text', 'test__title']
    ordering        = ['test', 'order']
    inlines         = [QuestionOptionInline]
    readonly_fields = ['created_at', 'options_link']
    fieldsets = [
        ('Основное',   {'fields': ['test', 'text', 'question_type', 'difficulty', 'order']}),
        ('Код / Язык', {'fields': ['language', 'metadata']}),
        ('Системное',  {'fields': ['created_at', 'options_link'], 'classes': ['collapse']}),
    ]

    class Media:
        js = ('admin/js/question_options_toggle.js',)

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
        else:
            if obj.options.exists():
                obj.options.all().delete()
                self.message_user(
                    request,
                    'Варианты ответов удалены — тип вопроса не поддерживает варианты.',
                    messages.WARNING,
                )

    def short_text(self, obj):
        return obj.text[:70]
    short_text.short_description = 'Вопрос'

    def type_badge(self, obj):
        colors = {
            'single_choice':   '#3498db',
            'multiple_choice': '#9b59b6',
            'text':            '#f39c12',
            'code':            '#e74c3c',
        }
        return _badge(obj.get_question_type_display(), colors.get(obj.question_type, '#95a5a6'))
    type_badge.short_description = 'Тип'

    def difficulty_badge(self, obj):
        return _badge(
            obj.get_difficulty_display(),
            DIFFICULTY_COLORS.get(obj.difficulty, '#95a5a6'),
        )
    difficulty_badge.short_description = 'Сложность'

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
    list_display  = ['text_short', 'question', 'correct_badge', 'order']
    list_filter   = ['is_correct', 'question__question_type']
    search_fields = ['text', 'question__text']
    ordering      = ['question', 'order']

    def text_short(self, obj):
        return obj.text[:80]
    text_short.short_description = 'Вариант'

    def correct_badge(self, obj):
        return _badge('✓ Верный', '#27ae60') if obj.is_correct else _badge('✗', '#bdc3c7')
    correct_badge.short_description = 'Правильный'


# ── TestSession ───────────────────────────────────────────────────────────────

@admin.register(TestSession)
class TestSessionAdmin(admin.ModelAdmin):
    list_display    = [
        'session_label', 'test', 'status_badge', 'valid_indicator',
        'expires_display', 'attempts_display', 'created_at',
    ]
    list_filter     = ['status', 'is_active', 'test']
    search_fields   = ['key', 'title', 'test__title']
    ordering        = ['-created_at']
    inlines         = [AttemptInline]
    actions         = ['force_expire']
    readonly_fields = [
        'id', 'key', 'created_at', 'expires_at',
        'valid_indicator', 'expires_display', 'attempts_display',
    ]
    fieldsets = [
        ('Сессия', {'fields': ['id', 'key', 'test', 'title', 'status', 'is_active']}),
        ('Время',  {'fields': ['created_at', 'expires_at', 'valid_indicator', 'expires_display']}),
        ('Попытки', {'fields': ['attempts_display']}),
    ]

    def session_label(self, obj):
        """Show title if set, otherwise truncated key."""
        if obj.title:
            return format_html(
                '{} <span style="color:#999;font-size:11px;">({})</span>',
                obj.title, obj.key[:12] + '…',
            )
        return obj.key
    session_label.short_description = 'Сессия'

    def status_badge(self, obj):
        color = STATUS_COLORS.get(obj.status, '#95a5a6')
        return _badge(obj.get_status_display(), color)
    status_badge.short_description = 'Статус'

    def valid_indicator(self, obj):
        if not obj or not obj.pk:
            return '—'
        return _badge('✓ Активна', '#27ae60') if obj.is_valid else _badge('✗ Истекла', '#e74c3c')
    valid_indicator.short_description = 'Действительна'

    def expires_display(self, obj):
        if not obj or not obj.pk:
            return '—'
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
        return format_html('{} активных / {} всего', active, total)
    attempts_display.short_description = 'Попытки'

    @admin.action(description='⛔ Принудительно завершить сессию')
    def force_expire(self, request, queryset):
        count = 0
        for session in queryset.filter(is_active=True):
            session.deactivate()
            count += 1
        self.message_user(request, f'Завершено сессий: {count}.', messages.SUCCESS)


# ── StudentAttempt ────────────────────────────────────────────────────────────

@admin.register(StudentAttempt)
class StudentAttemptAdmin(admin.ModelAdmin):
    list_display    = [
        'student_name', 'test_title', 'status_badge',
        'score_display', 'started_at', 'finished_at', 'duration_display',
    ]
    list_filter     = ['status', 'session__test', 'started_at']
    search_fields   = ['student_name', 'session__test__title', 'session__key', 'session__title']
    ordering        = ['-started_at']
    inlines         = [AnswerInline]
    readonly_fields = [
        'id', 'session', 'student_name', 'started_at',
        'finished_at', 'score', 'status', 'duration_display', 'score_display',
    ]
    fieldsets = [
        ('Студент',   {'fields': ['id', 'student_name', 'session']}),
        ('Результат', {'fields': ['status', 'score_display', 'started_at',
                                   'finished_at', 'duration_display']}),
    ]

    def has_add_permission(self, request):
        return False

    def test_title(self, obj):
        return obj.session.test.title if obj and obj.session_id else '—'
    test_title.short_description = 'Тест'

    def status_badge(self, obj):
        if not obj:
            return '—'
        color = STATUS_COLORS.get(obj.status, '#95a5a6')
        return _badge(obj.get_status_display(), color)
    status_badge.short_description = 'Статус'

    def score_display(self, obj):
        if not obj or not obj.is_finished:
            return '—'
        color = '#27ae60' if obj.score >= 70 else '#f39c12' if obj.score >= 40 else '#e74c3c'
        return format_html(
            '<strong style="font-size:16px;color:{};">{:.1f}%</strong>',
            color, obj.score,
        )
    score_display.short_description = 'Балл'

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
    list_display    = ['student_name', 'question_short', 'answer_preview',
                       'correctness_badge', 'answered_at']
    list_filter     = ['is_correct', 'question__question_type']
    search_fields   = ['attempt__student_name', 'question__text']
    ordering        = ['-answered_at']
    readonly_fields = [f.name for f in Answer._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def student_name(self, obj):
        return obj.attempt.student_name if obj and obj.attempt_id else '—'
    student_name.short_description = 'Студент'

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
            return _badge('На проверке', '#95a5a6')
        return _badge('✓ Верно', '#27ae60') if obj.is_correct else _badge('✗ Неверно', '#e74c3c')
    correctness_badge.short_description = 'Результат'