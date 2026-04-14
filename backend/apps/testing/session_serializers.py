from __future__ import annotations

from rest_framework import serializers


class LeaderboardEntrySerializer(serializers.Serializer):
    rank             = serializers.IntegerField()
    attempt_id       = serializers.UUIDField()
    student_name     = serializers.CharField()
    score            = serializers.FloatField()
    duration_seconds = serializers.FloatField(allow_null=True)


class LeaderboardResponseSerializer(serializers.Serializer):
    session_id = serializers.UUIDField()
    count      = serializers.IntegerField()
    results    = LeaderboardEntrySerializer(many=True)



class AttemptResultRowSerializer(serializers.Serializer):
    attempt_id       = serializers.UUIDField(source="id")
    student_name     = serializers.CharField()
    score            = serializers.FloatField()
    status           = serializers.CharField()
    correct          = serializers.IntegerField()   # annotated: correct_count
    wrong            = serializers.IntegerField()   # annotated: wrong_count
    total            = serializers.IntegerField()   # annotated: total_questions (from session test)
    answered         = serializers.IntegerField()   # annotated: answered_count
    duration_seconds = serializers.FloatField(allow_null=True)
    started_at       = serializers.DateTimeField()
    finished_at      = serializers.DateTimeField(allow_null=True)