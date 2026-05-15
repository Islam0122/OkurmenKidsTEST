from __future__ import annotations

import random
from collections import defaultdict
from typing import Optional

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.models import Prefetch


TOTAL_QUESTIONS = 20

QUESTION_TYPES = [
    "single_choice",
    "multiple_choice",
    "text",
    "code",
]


DEFAULT_DISTRIBUTION = {
    "single_choice": 8,
    "multiple_choice": 8,
    "text": 2,
    "code": 2,
}


QUESTION_DISTRIBUTION: dict[str, int] = getattr(
    settings,
    "TEST_QUESTION_DISTRIBUTION",
    DEFAULT_DISTRIBUTION,
)


# ──────────────────────────────────────────────────────────────────────────────
# Distribution
# ──────────────────────────────────────────────────────────────────────────────

def _compute_distribution(
    available_types: list[str],
) -> dict[str, int]:
    """
    Compute final production distribution.

    Base distribution is loaded from Django settings.

    Missing question types automatically redistribute their quota
    across available types as evenly as possible.

    Examples:
        Base:
            {
                "single_choice": 8,
                "multiple_choice": 8,
                "text": 2,
                "code": 2,
            }

        Missing "code":
            {
                "single_choice": 9,
                "multiple_choice": 9,
                "text": 2,
            }

        Only choice types:
            {
                "single_choice": 10,
                "multiple_choice": 10,
            }

    Redistribution is deterministic and stable.
    """
    if not available_types:
        return {}

    invalid_types = set(available_types) - set(QUESTION_TYPES)
    if invalid_types:
        raise ValidationError(
            f"Unknown question types: {sorted(invalid_types)}"
        )

    configured_total = sum(QUESTION_DISTRIBUTION.values())

    if configured_total != TOTAL_QUESTIONS:
        raise ValidationError(
            "TEST_QUESTION_DISTRIBUTION total must equal "
            f"{TOTAL_QUESTIONS}, got {configured_total}."
        )

    distribution: dict[str, int] = {}
    missing_quota = 0

    # ── Keep configured quotas for existing types ───────────────────────────
    for qtype in QUESTION_TYPES:
        configured = QUESTION_DISTRIBUTION.get(qtype, 0)

        if qtype in available_types:
            distribution[qtype] = configured
        else:
            missing_quota += configured

    if missing_quota == 0:
        return distribution

    # ── Redistribute missing quota deterministically ────────────────────────
    available_in_order = [
        qtype
        for qtype in QUESTION_TYPES
        if qtype in distribution
    ]

    base_extra, remainder = divmod(
        missing_quota,
        len(available_in_order),
    )

    for index, qtype in enumerate(available_in_order):
        distribution[qtype] += base_extra

        if index < remainder:
            distribution[qtype] += 1

    return distribution


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _fill_to_n(
    pool: list,
    n: int,
    rng: random.Random,
) -> list:
    """
    Select exactly n questions from pool.

    Rules:
        - pool >= n:
            random sample without duplicates

        - pool < n:
            repeat-sample until n reached,
            avoiding consecutive duplicates where possible
    """
    if not pool:
        raise ValidationError(
            "Cannot sample from empty question pool."
        )

    if len(pool) >= n:
        return rng.sample(pool, n)

    result: list = []
    last_id = None

    while len(result) < n:
        available = [
            q for q in pool
            if q.id != last_id
        ]

        if not available:
            available = pool

        chosen = rng.choice(available)

        result.append(chosen)
        last_id = chosen.id

    return result


def _serialize_question(q) -> dict:
    item = {
        "id": str(q.id),
        "text": q.text,
        "question_type": q.question_type,
        "difficulty": q.difficulty,
        "order": q.order,
        "is_auto_gradable": q.is_auto_gradable,
    }

    if q.language:
        item["language"] = q.language

    if q.metadata:
        item["metadata"] = q.metadata

    if q.question_type in (
        "single_choice",
        "multiple_choice",
    ):
        item["options"] = [
            {
                "id": str(o.id),
                "text": o.text,
                "order": o.order,
            }
            for o in sorted(
                q.options.all(),
                key=lambda o: o.order,
            )
        ]

    return item


def _seed_from_attempt_id(
    attempt_id: str,
) -> int:
    return int(
        attempt_id.replace("-", ""),
        16,
    ) % (2**31)


# ──────────────────────────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────────────────────────

def get_questions_for_attempt(
    test_id: str,
    seed: Optional[int] = None,
    attempt_id: Optional[str] = None,
) -> list[dict]:
    """
    Build deterministic question set for attempt.

    Features:
        - fixed production-ready distribution
        - automatic redistribution for missing types
        - repeat sampling
        - reproducible randomness
        - shuffled output
        - zero N+1 queries
    """
    from ..models import Question

    # ── Resolve seed ────────────────────────────────────────────────────────
    resolved_seed: Optional[int] = seed

    if resolved_seed is None and attempt_id is not None:
        resolved_seed = _seed_from_attempt_id(
            attempt_id,
        )

    rng = random.Random(resolved_seed)

    # ── Single query + prefetch ─────────────────────────────────────────────
    all_questions = list(
        Question.objects
        .filter(test_id=test_id)
        .prefetch_related(
            Prefetch("options")
        )
        .order_by()
    )

    if not all_questions:
        raise ValidationError(
            f"Test {test_id} has no questions."
        )

    # ── Group by type ───────────────────────────────────────────────────────
    grouped: dict[str, list] = defaultdict(list)

    for question in all_questions:
        grouped[question.question_type].append(
            question
        )

    available_types = [
        qtype
        for qtype in QUESTION_TYPES
        if grouped.get(qtype)
    ]

    distribution = _compute_distribution(
        available_types,
    )

    # ── Select questions ────────────────────────────────────────────────────
    selected: list = []

    for qtype in available_types:
        quota = distribution[qtype]
        pool = grouped[qtype]

        chosen = _fill_to_n(
            pool=pool,
            n=quota,
            rng=rng,
        )

        selected.extend(chosen)

    # ── Final deterministic shuffle ────────────────────────────────────────
    rng.shuffle(selected)

    # ── Serialize ───────────────────────────────────────────────────────────
    return [
        _serialize_question(q)
        for q in selected
    ]


# ──────────────────────────────────────────────────────────────────────────────
# Validation
# ──────────────────────────────────────────────────────────────────────────────

def validate_attempt_structure(
    answers: list[dict],
) -> None:
    """
    Validate submitted attempt structure.

    Rules:
        - exactly TOTAL_QUESTIONS answers
        - valid question types only
        - distribution must match computed distribution
    """
    if not isinstance(answers, list):
        raise ValidationError(
            "answers must be a list."
        )

    if len(answers) != TOTAL_QUESTIONS:
        raise ValidationError(
            f"Expected exactly "
            f"{TOTAL_QUESTIONS} answers, "
            f"got {len(answers)}."
        )

    type_counts: dict[str, int] = defaultdict(int)

    for index, answer in enumerate(answers):
        qtype = (
            answer.get("question_type")
            or (
                answer.get("question") or {}
            ).get("question_type")
        )

        if not qtype:
            raise ValidationError(
                f"Answer at index {index} "
                f"is missing question_type."
            )

        if qtype not in QUESTION_TYPES:
            raise ValidationError(
                f"Unknown question_type='{qtype}'."
            )

        type_counts[qtype] += 1

    present_types = [
        qtype
        for qtype in QUESTION_TYPES
        if type_counts.get(qtype, 0) > 0
    ]

    expected_distribution = _compute_distribution(
        present_types,
    )

    violations = []

    for qtype in present_types:
        expected = expected_distribution.get(
            qtype,
            0,
        )

        actual = type_counts.get(qtype, 0)

        if expected != actual:
            violations.append(
                f"'{qtype}': "
                f"expected {expected}, "
                f"got {actual}"
            )

    if violations:
        raise ValidationError(
            "Attempt structure invalid:\n"
            + "\n".join(violations)
        )


# ──────────────────────────────────────────────────────────────────────────────
# Integration helper
# ──────────────────────────────────────────────────────────────────────────────

def build_attempt_questions(
    test_id: str,
    attempt_id: str,
) -> list[dict]:
    """
    Deterministic wrapper for attempt generation.
    """
    return get_questions_for_attempt(
        test_id=test_id,
        attempt_id=attempt_id,
    )