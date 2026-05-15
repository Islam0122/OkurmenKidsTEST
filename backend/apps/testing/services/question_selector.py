from __future__ import annotations

import random
from collections import defaultdict
from typing import Optional, List, Dict, Any, Tuple

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.models import Prefetch

# Constants
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

# Load distribution from Django settings with fallback
QUESTION_DISTRIBUTION: Dict[str, int] = getattr(
    settings,
    "TEST_QUESTION_DISTRIBUTION",
    DEFAULT_DISTRIBUTION,
)


# ──────────────────────────────────────────────────────────────────────────────
# Distribution Logic
# ──────────────────────────────────────────────────────────────────────────────

def _validate_distribution_configuration() -> None:
    """
    Validate that distribution configuration is correct.

    Raises:
        ValidationError: If distribution total doesn't match TOTAL_QUESTIONS
    """
    configured_total = sum(QUESTION_DISTRIBUTION.values())
    if configured_total != TOTAL_QUESTIONS:
        raise ValidationError(
            f"TEST_QUESTION_DISTRIBUTION total must equal {TOTAL_QUESTIONS}, "
            f"got {configured_total}."
        )


def _compute_distribution(available_types: List[str]) -> Dict[str, int]:
    """
    Compute final distribution for available question types.

    Uses fixed configuration loaded from Django settings and redistributes
    quotas for missing types evenly across available types.

    Args:
        available_types: List of question types present in the test

    Returns:
        Dictionary mapping question types to their quotas

    Raises:
        ValidationError: If distribution is invalid or unknown types provided

    Examples:
        Base distribution (all types present):
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
    """
    # Edge case: No available types
    if not available_types:
        return {}

    # Validate available types
    invalid_types = set(available_types) - set(QUESTION_TYPES)
    if invalid_types:
        raise ValidationError(
            f"Unknown question types: {sorted(invalid_types)}"
        )

    # Validate distribution configuration
    _validate_distribution_configuration()

    # Calculate base distribution and missing quota
    distribution: Dict[str, int] = {}
    missing_quota = 0

    for qtype in QUESTION_TYPES:
        configured = QUESTION_DISTRIBUTION.get(qtype, 0)

        if qtype in available_types:
            distribution[qtype] = configured
        else:
            missing_quota += configured

    # If no missing types, return distribution as-is
    if missing_quota == 0:
        return distribution

    # Redistribute missing quota evenly across available types
    available_types_in_order = [
        qtype for qtype in QUESTION_TYPES
        if qtype in distribution
    ]

    base_extra, remainder = divmod(
        missing_quota,
        len(available_types_in_order),
    )

    for index, qtype in enumerate(available_types_in_order):
        distribution[qtype] += base_extra
        if index < remainder:
            distribution[qtype] += 1

    # Validate final distribution
    _validate_distribution_total(distribution)

    return distribution


def _validate_distribution_total(distribution: Dict[str, int]) -> None:
    """
    Validate that distribution totals to TOTAL_QUESTIONS.

    Args:
        distribution: Distribution to validate

    Raises:
        ValidationError: If total doesn't match TOTAL_QUESTIONS
    """
    total = sum(distribution.values())
    if total != TOTAL_QUESTIONS:
        raise ValidationError(
            f"Distribution total must be {TOTAL_QUESTIONS}, got {total}. "
            f"Distribution: {distribution}"
        )


# ──────────────────────────────────────────────────────────────────────────────
# Selection Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _fill_to_n(pool: List[Any], n: int, rng: random.Random) -> List[Any]:
    """
    Select exactly n items from pool with deterministic behavior.

    Rules:
        - If pool >= n: Random sample without duplicates
        - If pool < n: Repeat sample until n reached, avoiding consecutive duplicates

    Args:
        pool: List of items to select from
        n: Number of items to select
        rng: Random number generator for deterministic selection

    Returns:
        List of selected items

    Raises:
        ValidationError: If pool is empty
    """
    if not pool:
        raise ValidationError("Cannot sample from empty question pool.")

    if len(pool) >= n:
        return rng.sample(pool, n)

    # Repeat sampling for small pools
    result: List[Any] = []
    last_id = None

    while len(result) < n:
        # Avoid consecutive duplicates if possible
        available = [
            item for item in pool
            if getattr(item, 'id', None) != last_id
        ]

        if not available:
            available = pool

        chosen = rng.choice(available)
        result.append(chosen)
        last_id = getattr(chosen, 'id', None)

    return result


def _serialize_question(question: Any) -> Dict[str, Any]:
    """
    Serialize question model to dictionary format.

    Args:
        question: Question model instance

    Returns:
        Serialized question dictionary
    """
    item = {
        "id": str(question.id),
        "text": question.text,
        "question_type": question.question_type,
        "difficulty": question.difficulty,
        "order": question.order,
        "is_auto_gradable": question.is_auto_gradable,
    }

    # Add optional fields
    if hasattr(question, 'language') and question.language:
        item["language"] = question.language

    if hasattr(question, 'metadata') and question.metadata:
        item["metadata"] = question.metadata

    # Add options for choice questions
    if question.question_type in ("single_choice", "multiple_choice"):
        if hasattr(question, 'options'):
            item["options"] = [
                {
                    "id": str(option.id),
                    "text": option.text,
                    "order": option.order,
                }
                for option in sorted(
                    question.options.all(),
                    key=lambda opt: opt.order,
                )
            ]

    return item


def _seed_from_attempt_id(attempt_id: str) -> int:
    """
    Generate deterministic seed from attempt ID.

    Args:
        attempt_id: UUID string

    Returns:
        Integer seed for random number generator
    """
    # Convert hex string to integer and mod to fit within 32-bit range
    return int(attempt_id.replace("-", ""), 16) % (2 ** 31)


# ──────────────────────────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────────────────────────

def get_questions_for_attempt(
        test_id: str,
        seed: Optional[int] = None,
        attempt_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Build deterministic question set for test attempt.

    Features:
        - Fixed production-ready distribution from Django settings
        - Automatic redistribution for missing question types
        - Deterministic selection with optional seed
        - Optimized query performance (zero N+1)
        - Repeat sampling for small question pools
        - Shuffled output for unbiased ordering

    Args:
        test_id: ID of the test
        seed: Optional random seed for reproducibility
        attempt_id: Optional attempt ID to generate seed from

    Returns:
        List of serialized question objects

    Raises:
        ValidationError: If test has no questions or distribution is invalid
    """
    from ..models import Question

    # Resolve seed with priority: explicit seed > attempt_id > None
    resolved_seed: Optional[int] = seed
    if resolved_seed is None and attempt_id is not None:
        resolved_seed = _seed_from_attempt_id(attempt_id)

    rng = random.Random(resolved_seed)

    # Optimized single query with prefetch
    all_questions = list(
        Question.objects
        .filter(test_id=test_id)
        .prefetch_related(
            Prefetch("options", to_attr="cached_options")
        )
        .order_by("id")  # Deterministic ordering before random selection
    )

    if not all_questions:
        raise ValidationError(f"Test {test_id} has no questions.")

    # Group questions by type
    grouped: Dict[str, List[Any]] = defaultdict(list)
    for question in all_questions:
        grouped[question.question_type].append(question)

    # Determine available types
    available_types = [
        qtype for qtype in QUESTION_TYPES
        if grouped.get(qtype)
    ]

    # Compute distribution based on available types
    distribution = _compute_distribution(available_types)

    # Select questions according to distribution
    selected: List[Any] = []

    for qtype in available_types:
        quota = distribution[qtype]
        pool = grouped[qtype]

        chosen = _fill_to_n(pool=pool, n=quota, rng=rng)
        selected.extend(chosen)

    # Final deterministic shuffle to remove ordering bias
    rng.shuffle(selected)

    # Serialize and return
    return [_serialize_question(question) for question in selected]


# ──────────────────────────────────────────────────────────────────────────────
# Validation
# ──────────────────────────────────────────────────────────────────────────────

def validate_attempt_structure(answers: List[Dict[str, Any]]) -> None:
    """
    Validate submitted attempt structure against distribution rules.

    Validates:
        - Correct total number of answers
        - Valid question types
        - Distribution matches expected computed distribution

    Args:
        answers: List of answer dictionaries

    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(answers, list):
        raise ValidationError("answers must be a list.")

    if len(answers) != TOTAL_QUESTIONS:
        raise ValidationError(
            f"Expected exactly {TOTAL_QUESTIONS} answers, "
            f"got {len(answers)}."
        )

    # Count question types in answers
    type_counts: Dict[str, int] = defaultdict(int)

    for index, answer in enumerate(answers):
        # Extract question_type from different possible structures
        qtype = (
                answer.get("question_type")
                or (answer.get("question") or {}).get("question_type")
        )

        if not qtype:
            raise ValidationError(
                f"Answer at index {index} is missing question_type."
            )

        if qtype not in QUESTION_TYPES:
            raise ValidationError(
                f"Unknown question_type='{qtype}' at index {index}."
            )

        type_counts[qtype] += 1

    # Determine present types
    present_types = [
        qtype for qtype in QUESTION_TYPES
        if type_counts.get(qtype, 0) > 0
    ]

    # Compute expected distribution for present types
    expected_distribution = _compute_distribution(present_types)

    # Validate each type's count
    violations: List[str] = []

    for qtype in present_types:
        expected = expected_distribution.get(qtype, 0)
        actual = type_counts.get(qtype, 0)

        if expected != actual:
            violations.append(
                f"'{qtype}': expected {expected}, got {actual}"
            )

    if violations:
        raise ValidationError(
            "Attempt structure invalid:\n" + "\n".join(violations)
        )


# ──────────────────────────────────────────────────────────────────────────────
# Integration Helpers
# ──────────────────────────────────────────────────────────────────────────────

def build_attempt_questions(test_id: str, attempt_id: str) -> List[Dict[str, Any]]:
    """
    Build deterministic question set for attempt (convenience wrapper).

    Args:
        test_id: ID of the test
        attempt_id: ID of the attempt (used for seeding)

    Returns:
        List of serialized question objects
    """
    return get_questions_for_attempt(
        test_id=test_id,
        attempt_id=attempt_id,
    )