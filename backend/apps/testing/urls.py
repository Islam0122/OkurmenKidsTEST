from django.urls import path
from . import views
from .api_views import (
    TestListCreateView, TestDetailView,
    SessionCreateView, SessionEnterView, SessionListView,
    AttemptStartView, AttemptAnswerView, AttemptFinishView,
    AttemptResultView, AttemptListView,
)

app_name = 'testing'

urlpatterns = [
    # ── HTML admin views ─────────────────────────────────────────────────────
    path('testing1/import/',         views.import_questions,  name='import-questions'),
    path('testing1/import/confirm/', views.confirm_import,    name='confirm-import'),
    path('testing1/export/',         views.export_questions,  name='export-questions'),
    path('testing1/template/',       views.download_template, name='download-template'),

    # ── REST API v1 — Tests ───────────────────────────────────────────────────
    path('api/v1/tests/',           TestListCreateView.as_view(), name='api-tests-list'),
    path('api/v1/tests/<uuid:pk>/', TestDetailView.as_view(),     name='api-tests-detail'),

    # ── REST API v1 — Sessions ────────────────────────────────────────────────
    path('api/v1/sessions/',        SessionListView.as_view(),   name='api-sessions-list'),
    path('api/v1/sessions/create',  SessionCreateView.as_view(), name='api-sessions-create'),
    path('api/v1/sessions/enter',   SessionEnterView.as_view(),  name='api-sessions-enter'),

    # ── REST API v1 — Attempts & Answers ──────────────────────────────────────
    path('api/v1/attempt/start',                    AttemptStartView.as_view(),  name='api-attempt-start'),
    path('api/v1/attempt/answer',                   AttemptAnswerView.as_view(), name='api-attempt-answer'),
    path('api/v1/attempt/finish',                   AttemptFinishView.as_view(), name='api-attempt-finish'),
    path('api/v1/attempt/<uuid:attempt_id>/result', AttemptResultView.as_view(), name='api-attempt-result'),
    path('api/v1/attempts/',                        AttemptListView.as_view(),   name='api-attempts-list'),
]

