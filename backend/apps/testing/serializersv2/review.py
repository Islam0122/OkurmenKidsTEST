from __future__ import annotations

from rest_framework import serializers


class ReviewOptionSerializer(serializers.Serializer):
    """A single question option (selected or correct)."""
    id   = serializers.UUIDField()
    text = serializers.CharField()


class MistakeSerializer(serializers.Serializer):
    """
    Represents one incorrect (or partially-correct) answer in the review.

    For single_choice / multiple_choice:
        selected_options + correct_options are populated.
    For text / code:
        student_answer + expected_answer + ai_score + ai_confidence are populated.
    Both types carry: ai_feedback, ai_suggestion, explanation.
    """
    question_id   = serializers.UUIDField()
    question_type = serializers.CharField()
    question      = serializers.CharField()
    difficulty    = serializers.CharField()
    is_correct    = serializers.BooleanField(allow_null=True)
    answered_at   = serializers.DateTimeField(allow_null=True)

    # Choice questions
    selected_options = ReviewOptionSerializer(many=True, required=False, default=list)
    correct_options  = ReviewOptionSerializer(many=True, required=False, default=list)

    # Text / code questions
    student_answer   = serializers.CharField(allow_blank=True, required=False, default="")
    expected_answer  = serializers.CharField(allow_blank=True, required=False, default="")
    ai_score         = serializers.FloatField(allow_null=True, required=False)
    ai_confidence    = serializers.FloatField(allow_null=True, required=False)

    # Shared
    explanation  = serializers.CharField(allow_blank=True, required=False, default="")
    ai_feedback  = serializers.CharField(allow_blank=True, required=False, default="")
    ai_suggestion = serializers.CharField(allow_blank=True, required=False, default="")


class AttemptStatisticsSerializer(serializers.Serializer):
    """Per-question-type accuracy breakdown."""
    single_choice_accuracy   = serializers.FloatField(allow_null=True)
    multiple_choice_accuracy = serializers.FloatField(allow_null=True)
    code_accuracy            = serializers.FloatField(allow_null=True)
    text_accuracy            = serializers.FloatField(allow_null=True)

    # Extra grouped analytics
    hardest_questions   = serializers.ListField(child=serializers.DictField(), required=False)
    most_failed         = serializers.ListField(child=serializers.DictField(), required=False)
    avg_ai_score        = serializers.FloatField(allow_null=True, required=False)
    mistake_by_type     = serializers.DictField(required=False)


class ReviewSummarySerializer(serializers.Serializer):
    """High-level review summary: strong/weak topics and recommendations."""
    strong_topics       = serializers.ListField(child=serializers.CharField())
    weak_topics         = serializers.ListField(child=serializers.CharField())
    recommended_focus   = serializers.ListField(child=serializers.CharField())


class AttemptReviewSerializer(serializers.Serializer):
    """
    Full attempt review response.

    Fields mirror the spec in the task description.
    """
    attempt_id       = serializers.UUIDField()
    student_name     = serializers.CharField()
    test             = serializers.CharField()
    score            = serializers.FloatField()
    correct_answers  = serializers.IntegerField()
    wrong_answers    = serializers.IntegerField()
    success_rate     = serializers.FloatField()
    duration_seconds = serializers.FloatField(allow_null=True)

    mistakes    = MistakeSerializer(many=True)
    statistics  = AttemptStatisticsSerializer()
    summary     = ReviewSummarySerializer()