from django.urls import path
from . import views
from .api_views import (
    TestListCreateView, TestDetailView,
    SessionCreateView, SessionEnterView, SessionValidateView,
    SessionExpireView, SessionListView,
    AttemptStartView, AttemptAnswerView, AttemptFinishView,
    AttemptResultView, AttemptListView,
    SyncSessionDataView, SyncPushAnswerView,
    SyncAttemptStateView, SyncFinalizeView,
)

app_name = 'testing'

urlpatterns = [
    # ── HTML admin views ──────────────────────────────────────────────────────
    path('testing1/import/',         views.import_questions,  name='import-questions'),
    path('testing1/import/confirm/', views.confirm_import,    name='confirm-import'),
    path('testing1/export/',         views.export_questions,  name='export-questions'),
    path('testing1/template/',       views.download_template, name='download-template'),

    # ── Tests ─────────────────────────────────────────────────────────────────
    path('api/v1/tests/',           TestListCreateView.as_view(), name='api-tests-list'),
    path('api/v1/tests/<uuid:pk>/', TestDetailView.as_view(),     name='api-tests-detail'),

    # ── Sessions ──────────────────────────────────────────────────────────────
    path('api/v1/sessions/',                        SessionListView.as_view(),    name='api-sessions-list'),
    path('api/v1/sessions/create',                  SessionCreateView.as_view(),  name='api-sessions-create'),
    path('api/v1/sessions/enter',                   SessionEnterView.as_view(),   name='api-sessions-enter'),
    path('api/v1/sessions/validate',                SessionValidateView.as_view(), name='api-sessions-validate'),
    path('api/v1/sessions/<uuid:session_id>/expire', SessionExpireView.as_view(), name='api-sessions-expire'),

    # ── Attempts & Answers ────────────────────────────────────────────────────
    path('api/v1/attempt/start',                    AttemptStartView.as_view(),  name='api-attempt-start'),
    path('api/v1/attempt/answer',                   AttemptAnswerView.as_view(), name='api-attempt-answer'),
    path('api/v1/attempt/finish',                   AttemptFinishView.as_view(), name='api-attempt-finish'),
    path('api/v1/attempt/<uuid:attempt_id>/result', AttemptResultView.as_view(), name='api-attempt-result'),
    path('api/v1/attempts/',                        AttemptListView.as_view(),   name='api-attempts-list'),

    # ── Sync API (FastAPI integration) ────────────────────────────────────────
    path('api/v1/sync/session/<str:key>',                        SyncSessionDataView.as_view(),  name='api-sync-session'),
    path('api/v1/sync/attempt/<uuid:attempt_id>/answer',         SyncPushAnswerView.as_view(),   name='api-sync-answer'),
    path('api/v1/sync/attempt/<uuid:attempt_id>/state',          SyncAttemptStateView.as_view(), name='api-sync-state'),
    path('api/v1/sync/attempt/<uuid:attempt_id>/finalize',       SyncFinalizeView.as_view(),     name='api-sync-finalize'),
]