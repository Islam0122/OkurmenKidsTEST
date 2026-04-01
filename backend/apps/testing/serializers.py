from rest_framework import serializers
from .models import (
    Test, Question, QuestionOption,
    TestSession, StudentAttempt, Answer,
)


# ─── QuestionOption ───────────────────────────────────────────────────────────

class QuestionOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model  = QuestionOption
        fields = ['id', 'text', 'order']


class QuestionOptionAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model  = QuestionOption
        fields = ['id', 'text', 'is_correct', 'order']


# ─── Question ─────────────────────────────────────────────────────────────────

class QuestionSerializer(serializers.ModelSerializer):
    options = QuestionOptionSerializer(many=True, read_only=True)

    class Meta:
        model  = Question
        fields = [
            'id', 'text', 'question_type', 'language',
            'difficulty', 'order', 'options',
        ]


class QuestionWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Question
        fields = [
            'id', 'test', 'text', 'question_type',
            'language', 'difficulty', 'order', 'metadata',
        ]


# ─── Test ─────────────────────────────────────────────────────────────────────

class TestListSerializer(serializers.ModelSerializer):
    question_count = serializers.IntegerField(read_only=True)

    class Meta:
        model  = Test
        fields = [
            'id', 'title', 'description', 'level',
            'is_active', 'question_count', 'created_at',
        ]


class TestDetailSerializer(serializers.ModelSerializer):
    questions      = QuestionSerializer(many=True, read_only=True)
    question_count = serializers.IntegerField(read_only=True)

    class Meta:
        model  = Test
        fields = [
            'id', 'title', 'description', 'level', 'is_active',
            'question_count', 'questions', 'created_at', 'updated_at',
        ]


class TestWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Test
        fields = ['id', 'title', 'description', 'level', 'is_active']


# ─── Session ──────────────────────────────────────────────────────────────────

class SessionCreateSerializer(serializers.Serializer):
    test_id = serializers.UUIDField()


class SessionCreateResponseSerializer(serializers.Serializer):
    session_id = serializers.CharField()
    key        = serializers.CharField()
    test_title = serializers.CharField()
    expires_at = serializers.CharField()
    status     = serializers.CharField()


class TestSessionSerializer(serializers.ModelSerializer):
    test_title          = serializers.CharField(source='test.title', read_only=True)
    is_valid            = serializers.BooleanField(read_only=True)
    attempt_count       = serializers.SerializerMethodField()
    active_attempt_count = serializers.SerializerMethodField()

    class Meta:
        model  = TestSession
        fields = [
            'id', 'key', 'test_title', 'status', 'is_active', 'is_valid',
            'created_at', 'expires_at', 'attempt_count', 'active_attempt_count',
        ]

    def get_attempt_count(self, obj):
        return obj.attempts.count()

    def get_active_attempt_count(self, obj):
        return obj.active_attempt_count


# ─── Attempt ──────────────────────────────────────────────────────────────────

class AttemptStartSerializer(serializers.Serializer):
    key          = serializers.CharField(max_length=64)
    student_name = serializers.CharField(max_length=255)


class AttemptStartResponseSerializer(serializers.Serializer):
    attempt_id   = serializers.CharField()
    student_name = serializers.CharField()
    test_title   = serializers.CharField()
    questions    = serializers.ListField()


class AnswerSubmitSerializer(serializers.Serializer):
    attempt_id       = serializers.UUIDField()
    question_id      = serializers.UUIDField()
    answer_text      = serializers.CharField(allow_blank=True, default='')
    selected_options = serializers.ListField(
        child=serializers.UUIDField(), allow_empty=True, default=list
    )


class AnswerResultSerializer(serializers.Serializer):
    answer_id  = serializers.CharField()
    is_correct = serializers.BooleanField(allow_null=True)
    message    = serializers.CharField()


class AttemptFinishSerializer(serializers.Serializer):
    attempt_id = serializers.UUIDField()


class FinishResultSerializer(serializers.Serializer):
    attempt_id       = serializers.CharField()
    student_name     = serializers.CharField()
    score            = serializers.FloatField()
    total_questions  = serializers.IntegerField()
    answered         = serializers.IntegerField()
    correct          = serializers.IntegerField()
    duration_seconds = serializers.FloatField(allow_null=True)


class StudentAttemptSerializer(serializers.ModelSerializer):
    test_title       = serializers.CharField(source='session.test.title', read_only=True)
    session_key      = serializers.CharField(source='session.key', read_only=True)
    is_finished      = serializers.BooleanField(read_only=True)
    duration_seconds = serializers.FloatField(read_only=True)

    class Meta:
        model  = StudentAttempt
        fields = [
            'id', 'test_title', 'session_key', 'student_name', 'status',
            'started_at', 'finished_at', 'is_finished', 'score', 'duration_seconds',
        ]


# ─── Sync (FastAPI) ───────────────────────────────────────────────────────────

class SyncAnswerSerializer(serializers.Serializer):
    question_id      = serializers.UUIDField()
    answer_text      = serializers.CharField(allow_blank=True, default='')
    selected_options = serializers.ListField(
        child=serializers.UUIDField(), allow_empty=True, default=list
    )