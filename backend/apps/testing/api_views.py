from __future__ import annotations
import logging
from rest_framework import status, generics
from rest_framework.permissions import IsAdminUser, AllowAny
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
    permission_classes = [IsAdminUser]

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
    permission_classes = [IsAdminUser]

    def post(self, request, session_id):
        try:
            SessionService.expire_session(str(session_id))
        except ValidationError as exc:
            return _err(exc)
        return Response({'detail': 'Session expired.'})


class SessionListView(generics.ListAPIView):
    serializer_class   = TestSessionSerializer
    permission_classes = [IsAdminUser]
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
    permission_classes = [IsAdminUser]
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