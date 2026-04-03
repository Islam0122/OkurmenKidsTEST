"""
resources.py — Import-Export resources for the Testing app.

Key fixes:
  - ForeignKeyWidget uses the correct lookup field for each relation
  - readonly computed fields use dehydrate_ prefix
  - import_id_fields uses 'id' (UUID primary key)
  - skip_unchanged + report_skipped enabled on all resources
"""

from __future__ import annotations

from import_export import fields, resources
from import_export.widgets import ForeignKeyWidget

from .models import (
    Answer,
    Question,
    QuestionOption,
    StudentAttempt,
    Test,
    TestSession,
)


# ── Test ──────────────────────────────────────────────────────────────────────

class TestResource(resources.ModelResource):
    question_count = fields.Field(
        column_name='question_count',
        attribute=None,
        readonly=True,
    )

    class Meta:
        model            = Test
        fields           = (
            'id', 'title', 'description', 'level',
            'is_active', 'question_count', 'created_at', 'updated_at',
        )
        export_order     = fields
        import_id_fields = ('id',)
        skip_unchanged   = True
        report_skipped   = True

    def dehydrate_question_count(self, obj: Test) -> int:
        return obj.questions.count()


# ── Question ──────────────────────────────────────────────────────────────────

class QuestionResource(resources.ModelResource):
    # Import by test title, export shows test title
    test = fields.Field(
        attribute='test',
        column_name='test_title',
        widget=ForeignKeyWidget(Test, field='title'),
    )
    # Export-only: the UUID so rows can be identified easily
    test_id = fields.Field(
        attribute='test_id',
        column_name='test_id',
        readonly=True,
    )

    class Meta:
        model            = Question
        fields           = (
            'id', 'test', 'test_id', 'text', 'question_type',
            'language', 'difficulty', 'order', 'metadata', 'created_at',
        )
        export_order     = fields
        import_id_fields = ('id',)
        skip_unchanged   = True
        report_skipped   = True


# ── QuestionOption ────────────────────────────────────────────────────────────

class QuestionOptionResource(resources.ModelResource):
    # Import by question UUID (safer than question text which could duplicate)
    question = fields.Field(
        attribute='question',
        column_name='question_id',
        widget=ForeignKeyWidget(Question, field='id'),
    )
    question_text = fields.Field(
        attribute=None,
        column_name='question_text',
        readonly=True,
    )
    test_title = fields.Field(
        attribute=None,
        column_name='test_title',
        readonly=True,
    )

    class Meta:
        model            = QuestionOption
        fields           = (
            'id', 'question', 'question_text', 'test_title',
            'text', 'is_correct', 'order',
        )
        export_order     = fields
        import_id_fields = ('id',)
        skip_unchanged   = True
        report_skipped   = True

    def dehydrate_question_text(self, obj: QuestionOption) -> str:
        return obj.question.text[:120] if obj.question_id else ''

    def dehydrate_test_title(self, obj: QuestionOption) -> str:
        return obj.question.test.title if obj.question_id else ''


# ── TestSession ───────────────────────────────────────────────────────────────

class TestSessionResource(resources.ModelResource):
    test = fields.Field(
        attribute='test',
        column_name='test_title',
        widget=ForeignKeyWidget(Test, field='title'),
    )
    attempt_count        = fields.Field(attribute=None, column_name='attempt_count',        readonly=True)
    active_attempt_count = fields.Field(attribute=None, column_name='active_attempt_count', readonly=True)
    is_valid             = fields.Field(attribute=None, column_name='is_valid',             readonly=True)

    class Meta:
        model            = TestSession
        fields           = (
            'id', 'test', 'title', 'key', 'status', 'is_active',
            'is_valid', 'created_at', 'expires_at',
            'attempt_count', 'active_attempt_count',
        )
        export_order     = fields
        import_id_fields = ('id',)
        skip_unchanged   = True
        report_skipped   = True

    def dehydrate_attempt_count(self, obj: TestSession) -> int:
        return obj.attempts.count()

    def dehydrate_active_attempt_count(self, obj: TestSession) -> int:
        return obj.active_attempt_count

    def dehydrate_is_valid(self, obj: TestSession) -> bool:
        return obj.is_valid


# ── StudentAttempt ────────────────────────────────────────────────────────────

class StudentAttemptResource(resources.ModelResource):
    session = fields.Field(
        attribute='session',
        column_name='session_id',
        widget=ForeignKeyWidget(TestSession, field='id'),
    )
    session_key   = fields.Field(attribute=None, column_name='session_key',   readonly=True)
    session_title = fields.Field(attribute=None, column_name='session_title', readonly=True)
    test_title    = fields.Field(attribute=None, column_name='test_title',    readonly=True)
    duration_secs = fields.Field(attribute=None, column_name='duration_secs', readonly=True)

    class Meta:
        model            = StudentAttempt
        fields           = (
            'id', 'session', 'session_key', 'session_title', 'test_title',
            'student_name', 'status', 'score',
            'started_at', 'finished_at', 'duration_secs',
        )
        export_order     = fields
        import_id_fields = ('id',)
        skip_unchanged   = True
        report_skipped   = True

    def dehydrate_session_key(self, obj: StudentAttempt) -> str:
        return obj.session.key if obj.session_id else ''

    def dehydrate_session_title(self, obj: StudentAttempt) -> str:
        return obj.session.title if obj.session_id else ''

    def dehydrate_test_title(self, obj: StudentAttempt) -> str:
        return obj.session.test.title if obj.session_id else ''

    def dehydrate_duration_secs(self, obj: StudentAttempt):
        d = obj.duration_seconds
        return round(d, 1) if d is not None else ''


# ── Answer ────────────────────────────────────────────────────────────────────

class AnswerResource(resources.ModelResource):
    attempt = fields.Field(
        attribute='attempt',
        column_name='attempt_id',
        widget=ForeignKeyWidget(StudentAttempt, field='id'),
    )
    question = fields.Field(
        attribute='question',
        column_name='question_id',
        widget=ForeignKeyWidget(Question, field='id'),
    )
    student_name  = fields.Field(attribute=None, column_name='student_name',  readonly=True)
    question_text = fields.Field(attribute=None, column_name='question_text', readonly=True)
    question_type = fields.Field(attribute=None, column_name='question_type', readonly=True)

    class Meta:
        model            = Answer
        fields           = (
            'id', 'attempt', 'student_name', 'question', 'question_text',
            'question_type', 'answer_text', 'selected_options',
            'is_correct', 'answered_at',
        )
        export_order     = fields
        import_id_fields = ('id',)
        skip_unchanged   = True
        report_skipped   = True

    def dehydrate_student_name(self, obj: Answer) -> str:
        return obj.attempt.student_name if obj.attempt_id else ''

    def dehydrate_question_text(self, obj: Answer) -> str:
        return obj.question.text[:120] if obj.question_id else ''

    def dehydrate_question_type(self, obj: Answer) -> str:
        return obj.question.question_type if obj.question_id else ''