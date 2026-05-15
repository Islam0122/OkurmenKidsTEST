from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass, field

from django.core.cache import cache

from .aggregations import (
    get_multi_session_kpis,
    get_multi_session_ranking,
    get_multi_session_question_breakdown,
    get_score_buckets,
    get_score_by_session,
    get_attempts_by_day,
)

logger = logging.getLogger(__name__)

CACHE_TTL = 60 * 3

@dataclass
class MultiSessionFilters:
    session_ids  : list[str]        = field(default_factory=list)
    date_from    : str | None       = None
    date_to      : str | None       = None
    test_id      : str | None       = None
    session_type : str | None       = None
    status       : str | None       = None
    min_score    : float | None     = None
    max_score    : float | None     = None
    dedup_mode   : str              = "best"

    @property
    def cache_key(self) -> str:
        raw = (
            ",".join(sorted(self.session_ids))
            + f"|{self.date_from}|{self.date_to}"
            + f"|{self.test_id}|{self.session_type}"
            + f"|{self.status}|{self.min_score}|{self.max_score}"
            + f"|{self.dedup_mode}"
        )
        h = hashlib.md5(raw.encode(), usedforsecurity=False).hexdigest()[:12]
        return f"multi_analytics:{h}"

    @property
    def has_filters(self) -> bool:
        return any([
            self.date_from, self.date_to, self.test_id,
            self.session_type, self.status,
            self.min_score is not None,
            self.max_score is not None,
        ])


class MultiSessionService:
    @staticmethod
    def get_analytics(filters: MultiSessionFilters) -> dict:
        if not filters.session_ids:
            return _empty_data()

        cached = cache.get(filters.cache_key)
        if cached is not None:
            logger.debug("multi_analytics cache hit: %s", filters.cache_key)
            return cached

        logger.debug(
            "multi_analytics computing for %d sessions (dedup=%s)",
            len(filters.session_ids), filters.dedup_mode,
        )

        try:
            kpis      = get_multi_session_kpis(filters)
            ranking   = get_multi_session_ranking(filters)
            breakdown = get_multi_session_question_breakdown(filters)
            score_buckets    = get_score_buckets(filters)
            score_by_session = get_score_by_session(filters)
            attempts_by_day  = get_attempts_by_day(filters)
        except Exception as exc:
            logger.exception("multi_analytics error: %s", exc)
            return _empty_data()

        data = {
            "kpis":             kpis,
            "ranking":          ranking,
            "breakdown":        breakdown,
            "score_buckets":    score_buckets,
            "score_by_session": score_by_session,
            "attempts_by_day":  attempts_by_day,
        }

        cache.set(filters.cache_key, data, CACHE_TTL)
        return data

    @staticmethod
    def invalidate(session_ids: list[str]) -> None:
        try:
            cache.delete_pattern("multi_analytics:*")
        except AttributeError:
            pass


def _empty_data() -> dict:
    return {
        "kpis":             {},
        "ranking":          [],
        "breakdown":        [],
        "score_buckets":    [],
        "score_by_session": [],
        "attempts_by_day":  [],
    }