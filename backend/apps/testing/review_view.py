

from __future__ import annotations

import logging

from django.core.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status as http_status

from .services.attempt_review import AttemptReviewService
from .serializersv2.review import AttemptReviewSerializer

logger = logging.getLogger(__name__)


class AttemptReviewView(APIView):
    """
    GET /api/testing/attempts/<attempt_id>/review/

    Returns a full post-test review for a finished attempt:
      - attempt meta (score, duration, correct/wrong counts)
      - mistakes list (selected vs correct options, AI feedback, explanation)
      - per-type accuracy statistics
      - topic summary (strong / weak / recommended focus)

    Access control:
      AllowAny — the attempt_id itself acts as an access token
      (students don't have Django auth; they only know their own attempt UUID).
      Add IsAdminUser or a custom permission if stricter access is needed.
    """

    permission_classes = [AllowAny]

    def get(self, request: Request, attempt_id: str) -> Response:
        logger.info(
            "[AttemptReviewView] request attempt_id=%s", attempt_id
        )

        try:
            data = AttemptReviewService.build_review(str(attempt_id))
        except ValidationError as exc:
            msg = exc.message if hasattr(exc, "message") else str(exc)
            logger.warning(
                "[AttemptReviewView] validation error attempt_id=%s: %s",
                attempt_id, msg,
            )
            return Response({"detail": msg}, status=http_status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            logger.exception(
                "[AttemptReviewView] unexpected error attempt_id=%s: %s",
                attempt_id, exc,
            )
            return Response(
                {"detail": "An unexpected error occurred."},
                status=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        serializer = AttemptReviewSerializer(data)
        return Response(serializer.data, status=http_status.HTTP_200_OK)

