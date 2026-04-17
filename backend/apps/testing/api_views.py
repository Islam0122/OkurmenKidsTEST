from __future__ import annotations
import logging
from rest_framework import status, generics
from rest_framework.permissions import  AllowAny
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView
from django.core.exceptions import ValidationError
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import Test, TestSession, StudentAttempt
from .serializers import (
    TestListSerializer, TestDetailSerializer, TestWriteSerializer,
    TestSessionSerializer,
    SessionCreateSerializer, SessionCreateResponseSerializer,
    AttemptStartSerializer, AttemptStartResponseSerializer,
    AnswerSubmitSerializer, AnswerResultSerializer,
    AttemptFinishSerializer, FinishResultSerializer,
    StudentAttemptSerializer,
    SyncAnswerSerializer,
)
from .services import (
    SessionService, AttemptService, AnswerService, SyncService,
    create_session, get_valid_session,
    start_attempt, submit_answer, finish_attempt, get_attempt_result,
)

logger = logging.getLogger(__name__)


def _err(exc: ValidationError):
    msg = exc.message if hasattr(exc, 'message') else str(exc)
    return Response({'detail': msg}, status=status.HTTP_400_BAD_REQUEST)


# ─── Tests ────────────────────────────────────────────────────────────────────

class TestListCreateView(generics.ListCreateAPIView):
    filter_backends  = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['level', 'is_active']
    search_fields    = ['title', 'description']
    ordering_fields  = ['title', 'created_at']

    def get_serializer_class(self):
        return TestWriteSerializer if self.request.method == 'POST' else TestListSerializer

    def get_permissions(self):
        return [IsAdminUser()] if self.request.method == 'POST' else [AllowAny()]

    def get_queryset(self):
        qs = Test.objects.all()
        if not (self.request.user and self.request.user.is_staff):
            qs = qs.filter(is_active=True)
        return qs


class TestDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Test.objects.all()

    def get_serializer_class(self):
        return TestDetailSerializer if self.request.method == 'GET' else TestWriteSerializer

    def get_permissions(self):
        return [AllowAny()] if self.request.method == 'GET' else [IsAdminUser()]


# ─── Sessions ─────────────────────────────────────────────────────────────────

class SessionCreateView(APIView):

    def post(self, request):
        ser = SessionCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            result = SessionService.create_session(
                test_id=str(ser.validated_data['test_id']),
                title=ser.validated_data.get('title', ''),
            )
        except ValidationError as exc:
            return _err(exc)
        return Response(
            SessionCreateResponseSerializer(result).data,
            status=status.HTTP_201_CREATED,
        )


class SessionValidateView(APIView):
    """POST /api/v1/sessions/validate — student validates key."""
    permission_classes = [AllowAny]
    throttle_classes   = [AnonRateThrottle]

    def post(self, request):
        key = request.data.get('key', '').strip()
        if not key:
            return Response({'detail': 'key is required.'}, status=400)
        try:
            session = SessionService.validate_session(key)
        except ValidationError as exc:
            return _err(exc)
        return Response(TestSessionSerializer(session).data)


class SessionEnterView(SessionValidateView):
    """POST /api/v1/sessions/enter — same as validate, kept for compat."""
    pass


class SessionExpireView(APIView):
    """POST /api/v1/sessions/{id}/expire — admin force-expires a session."""

    def post(self, request, session_id):
        try:
            SessionService.expire_session(str(session_id))
        except ValidationError as exc:
            return _err(exc)
        return Response({'detail': 'Session expired.'})


class SessionListView(generics.ListAPIView):
    serializer_class   = TestSessionSerializer
    filter_backends    = [DjangoFilterBackend, OrderingFilter]
    filterset_fields   = ['test', 'is_active', 'status']

    def get_queryset(self):
        return TestSession.objects.select_related('test').prefetch_related('attempts')


# ─── Attempts ─────────────────────────────────────────────────────────────────

class AttemptStartView(APIView):
    permission_classes = [AllowAny]
    throttle_classes   = [AnonRateThrottle]

    def post(self, request):
        ser = AttemptStartSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            result = AttemptService.start_attempt(
                key=ser.validated_data['key'],
                student_name=ser.validated_data['student_name'],
            )
        except ValidationError as exc:
            return _err(exc)
        return Response(AttemptStartResponseSerializer(result).data, status=201)


class AttemptAnswerView(APIView):
    permission_classes = [AllowAny]
    throttle_classes   = [AnonRateThrottle]

    def post(self, request):
        ser = AnswerSubmitSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            result = AnswerService.submit_answer(
                attempt_id=str(ser.validated_data['attempt_id']),
                question_id=str(ser.validated_data['question_id']),
                answer_text=ser.validated_data.get('answer_text', ''),
                selected_options=[str(o) for o in ser.validated_data.get('selected_options', [])],
            )
        except ValidationError as exc:
            return _err(exc)
        return Response(AnswerResultSerializer(result).data)


class AttemptFinishView(APIView):
    permission_classes = [AllowAny]
    throttle_classes   = [AnonRateThrottle]

    def post(self, request):
        ser = AttemptFinishSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            result = AttemptService.finish_attempt(str(ser.validated_data['attempt_id']))
        except ValidationError as exc:
            return _err(exc)
        return Response(FinishResultSerializer(result).data)


class AttemptResultView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, attempt_id):
        try:
            data = AttemptService.get_attempt_result(str(attempt_id))
        except ValidationError as exc:
            return _err(exc)
        return Response(data)


class AttemptListView(generics.ListAPIView):
    serializer_class   = StudentAttemptSerializer
    filter_backends    = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields   = ['session', 'session__test', 'status']
    search_fields      = ['student_name']
    ordering_fields    = ['-started_at', 'score']

    def get_queryset(self):
        return StudentAttempt.objects.select_related('session__test').all()


# ─── Sync API (FastAPI integration) ───────────────────────────────────────────

class SyncSessionDataView(APIView):
    """GET /api/v1/sync/session/{key} — FastAPI fetches full session payload."""
    permission_classes = [AllowAny]

    def get(self, request, key):
        try:
            data = SyncService.prepare_data_for_fastapi(key)
        except ValidationError as exc:
            return _err(exc)
        return Response(data)


class SyncPushAnswerView(APIView):
    """POST /api/v1/sync/attempt/{attempt_id}/answer — FastAPI pushes answer."""
    permission_classes = [AllowAny]

    def post(self, request, attempt_id):
        ser = SyncAnswerSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            result = SyncService.push_attempt_update(
                attempt_id=str(attempt_id),
                payload={
                    'question_id':      str(ser.validated_data['question_id']),
                    'answer_text':      ser.validated_data.get('answer_text', ''),
                    'selected_options': [str(o) for o in ser.validated_data.get('selected_options', [])],
                },
            )
        except ValidationError as exc:
            return _err(exc)
        return Response(result)


class SyncAttemptStateView(APIView):
    """GET /api/v1/sync/attempt/{attempt_id}/state — FastAPI reads current state."""
    permission_classes = [AllowAny]

    def get(self, request, attempt_id):
        try:
            data = SyncService.sync_attempt_results(str(attempt_id))
        except ValidationError as exc:
            return _err(exc)
        return Response(data)


class SyncFinalizeView(APIView):
    """POST /api/v1/sync/attempt/{attempt_id}/finalize — FastAPI finalizes attempt."""
    permission_classes = [AllowAny]

    def post(self, request, attempt_id):
        try:
            data = SyncService.finalize_results(str(attempt_id))
        except ValidationError as exc:
            return _err(exc)
        return Response(data)


from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from django.core.exceptions import ValidationError


class AnswerGradeStatusView(APIView):
    """
    GET /api/v1/answer/<uuid:answer_id>/grade-status

    Lightweight polling endpoint — no auth required (answer_id acts as token).
    Returns current AI grading status + result once available.
    """
    permission_classes = [AllowAny]

    def get(self, request, answer_id):
        from apps.testing.models import Answer

        try:
            answer = Answer.objects.select_related('question').get(pk=answer_id)
        except Answer.DoesNotExist:
            return Response({'detail': 'Answer not found.'}, status=404)

        data = {
            # ── Existing fields (always present) ─────────────────────────────
            'answer_id': str(answer.id),
            'grading_status': answer.grading_status,
            'is_correct': answer.is_correct,

            # ── New AI fields (null until graded) ─────────────────────────────
            'ai_score': answer.ai_score,
            'ai_confidence': answer.ai_confidence,
            'ai_feedback': answer.ai_feedback or '',
            'ai_suggestion': answer.ai_suggestion if hasattr(answer, 'ai_suggestion') else '',
        }
        return Response(data)

from rest_framework import generics
from django.db.models import F, ExpressionWrapper, DurationField
from django.utils import timezone

from .models import StudentAttempt, AttemptStatus
from .serializers import LeaderboardSerializer


class LeaderboardView(generics.ListAPIView):
    """
    GET /api/v1/leaderboard?session=<uuid>
    """
    serializer_class = LeaderboardSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        session_id = self.request.query_params.get("session")

        qs = StudentAttempt.objects.filter(
            status=AttemptStatus.FINISHED,
        ).select_related("session")

        if session_id:
            qs = qs.filter(session_id=session_id)

        # tie-break: faster finish = higher rank
        qs = qs.annotate(
            duration=ExpressionWrapper(
                F("finished_at") - F("started_at"),
                output_field=DurationField()
            )
        ).order_by("-score", "duration")

        return qs

from django.db.models import (
    BooleanField,
    Case,
    Count,
    ExpressionWrapper,
    F,
    FloatField,
    IntegerField,
    OuterRef,
    Q,
    Subquery,
    Value,
    When,
    DurationField,
)
from django.db.models.functions import Coalesce, Extract
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView

from apps.testing.models import AttemptStatus, StudentAttempt, TestSession

from .filters import AttemptResultsFilter
from .session_serializers import AttemptResultRowSerializer, LeaderboardEntrySerializer



def _duration_seconds_expr():
    """
    Returns an annotated expression for duration in seconds.
    Works on PostgreSQL via EXTRACT(EPOCH FROM ...) equivalent.
    Falls back gracefully on SQLite (returns timedelta float).
    """
    return ExpressionWrapper(
        F("finished_at") - F("started_at"),
        output_field=DurationField(),
    )


def _annotate_attempt_qs(qs):
    """
    Single-pass annotation:
      - correct_count   (answers where is_correct=True)
      - wrong_count     (answers where is_correct=False)
      - answered_count  (all submitted answers)
      - duration        (timedelta, nullable)
    """
    return qs.annotate(
        correct_count=Count("answers", filter=Q(answers__is_correct=True)),
        wrong_count=Count("answers", filter=Q(answers__is_correct=False)),
        answered_count=Count("answers"),
        duration=ExpressionWrapper(
            F("finished_at") - F("started_at"),
            output_field=DurationField(),
        ),
    )


def _to_seconds(td) -> float | None:
    """Convert timedelta → float seconds (None-safe)."""
    if td is None:
        return None
    return td.total_seconds()


class StandardPagination(PageNumberPagination):
    page_size            = 20
    page_size_query_param = "page_size"
    max_page_size        = 200



class SessionLeaderboardView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, session_id):
        session = get_object_or_404(
            TestSession.objects.select_related("test"),
            pk=session_id,
        )

        qs = (
            StudentAttempt.objects
            .filter(session=session, status=AttemptStatus.FINISHED)
            .annotate(
                duration=ExpressionWrapper(
                    F("finished_at") - F("started_at"),
                    output_field=DurationField(),
                )
            )
            .order_by("-score", "duration")
            .values("id", "student_name", "score", "duration")
        )

        results = []
        for rank, row in enumerate(qs, start=1):
            results.append({
                "rank":             rank,
                "attempt_id":       row["id"],
                "student_name":     row["student_name"],
                "score":            row["score"],
                "duration_seconds": _to_seconds(row["duration"]),
            })

        return Response({
            "session_id": str(session_id),
            "count":      len(results),
            "results":    results,
        })


class SessionResultsTableView(ListAPIView):


    permission_classes  = [IsAdminUser]
    pagination_class    = StandardPagination
    filter_backends     = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class     = AttemptResultsFilter
    search_fields       = ["student_name"]
    ordering_fields     = ["score", "started_at", "duration", "answered_count"]
    ordering            = ["-started_at"]

    # We override get_queryset to scope by session_id from the URL.
    # The filterset still works — it just starts with a pre-filtered qs.

    def get_session(self):
        if not hasattr(self, "_session"):
            self._session = get_object_or_404(
                TestSession.objects.select_related("test"),
                pk=self.kwargs["session_id"],
            )
        return self._session

    def get_queryset(self):
        session = self.get_session()

        # Subquery: total question count for this session's test
        # We use a static value here because the test is fixed per session,
        # but using Subquery keeps it SQL-level and avoids an extra Python round-trip
        # if this view is ever reused outside the session context.
        from apps.testing.models import Question
        total_subquery = Subquery(
            Question.objects
            .filter(test=session.test)
            .values("test")
            .annotate(cnt=Count("id"))
            .values("cnt")[:1],
            output_field=IntegerField(),
        )

        qs = (
            StudentAttempt.objects
            .filter(session=session)
            .select_related("session__test")
            .annotate(
                correct_count=Count("answers", filter=Q(answers__is_correct=True)),
                wrong_count=Count("answers",   filter=Q(answers__is_correct=False)),
                answered_count=Count("answers"),
                total_questions=total_subquery,
                duration=ExpressionWrapper(
                    F("finished_at") - F("started_at"),
                    output_field=DurationField(),
                ),
            )
        )
        return qs

    def get_serializer_class(self):
        return AttemptResultRowSerializer

    def list(self, request, *args, **kwargs):
        qs         = self.filter_queryset(self.get_queryset())
        page       = self.paginate_queryset(qs)
        session    = self.get_session()
        rows       = page if page is not None else qs

        data = []
        for attempt in rows:
            data.append({
                "id":              attempt.id,
                "student_name":    attempt.student_name,
                "score":           attempt.score,
                "status":          attempt.status,
                "correct":         attempt.correct_count,
                "wrong":           attempt.wrong_count,
                "total":           attempt.total_questions or 0,
                "answered":        attempt.answered_count,
                "duration_seconds": _to_seconds(attempt.duration),
                "started_at":      attempt.started_at,
                "finished_at":     attempt.finished_at,
            })

        serializer = AttemptResultRowSerializer(data, many=True)

        if page is not None:
            return self.get_paginated_response(serializer.data)

        return Response({
            "session_id": str(session.id),
            "count":      len(data),
            "results":    serializer.data,
        })