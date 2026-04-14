from __future__ import annotations
import django_filters
from django.db.models import QuerySet
from apps.testing.models import StudentAttempt, AttemptStatus


class AttemptResultsFilter(django_filters.FilterSet):
    status = django_filters.ChoiceFilter(choices=AttemptStatus.choices)
    min_score = django_filters.NumberFilter(field_name="score", lookup_expr="gte")
    max_score = django_filters.NumberFilter(field_name="score", lookup_expr="lte")
    search = django_filters.CharFilter(field_name="student_name", lookup_expr="icontains")
    started_after  = django_filters.IsoDateTimeFilter(field_name="started_at",  lookup_expr="gte")
    started_before = django_filters.IsoDateTimeFilter(field_name="started_at",  lookup_expr="lte")
    session = django_filters.UUIDFilter(field_name="session__id")
    test    = django_filters.UUIDFilter(field_name="session__test__id")

    class Meta:
        model  = StudentAttempt
        fields = [
            "status",
            "min_score", "max_score",
            "search",
            "started_after", "started_before",
            "session",
            "test",
        ]