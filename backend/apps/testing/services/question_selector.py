"""
services/question_selector.py

Question selection algorithm for student attempts.

Distribution (Task 3):
  single_choice   = 8
  multiple_choice = 8
  text            = 2
  code            = 2
  ───────────────────
  TOTAL           = 20

Fallback algorithm:
  If any type has fewer questions than its target quota,
  the deficit is distributed proportionally to the remaining types
  (those that still have surplus capacity), preserving randomness.

No DB schema changes. No new models.
"""
from __future__ import annotations

import logging
import random
from typing import Optional

from django.core.exceptions import ValidationError
from django.db.models import Prefetch

logger = logging.getLogger(__name__)

# ── Target distribution ───────────────────────────────────────────────────────

TOTAL_QUESTIONS = 20

# Canonical order is preserved during selection and validation.
QUESTION_TYPES: list[str] = [
    "single_choice",
    "multiple_choice",
    "text",
    "code",
]

# Target quota per type (Task 3 requirement).
TARGET_DISTRIBUTION: dict[str, int] = {
    "single_choice":   8,
    "multiple_choice": 8,
    "text":            2,
    "code":            2,
}

assert sum(TARGET_DISTRIBUTION.values()) == TOTAL_QUESTIONS, (
    "TARGET_DISTRIBUTION must sum to TOTAL_QUESTIONS"
)


# ── Distribution engine ───────────────────────────────────────────────────────

def _compute_distribution(
    available: dict[str, int],
) -> dict[str, int]:
    """
    Compute the actual per-type quota given how many questions each type has.

    Algorithm (fallback):
      1. Start with TARGET_DISTRIBUTION for each present type.
      2. For types that have fewer questions than their target,
         cap them at their actual count and collect the deficit.
      3. Distribute the deficit proportionally across types that
         still have surplus capacity, iterating until stable.
      4. If total reachable < TOTAL_QUESTIONS, repeat each question
         as needed (handled later by _fill_to_n).

    Args:
        available: {question_type: count_in_db}

    Returns:
        {question_type: quota_to_select}  — sums to TOTAL_QUESTIONS
        (may exceed available[type] for types with very few questions;
        _fill_to_n handles repetition in that case).
    """
    # Only consider types that exist in the test
    present = {t: available[t] for t in QUESTION_TYPES if available.get(t, 0) > 0}

    if not present:
        raise ValidationError("Test has no questions.")

    # Initialise quotas from target (or actual if type has fewer)
    quotas: dict[str, int] = {}
    for t in present:
        quotas[t] = min(TARGET_DISTRIBUTION.get(t, 0), present[t])

    # Types completely absent get 0 deficit weight — only present types matter
    # for distributing remaining slots.
    allocated = sum(quotas.values())
    remaining = TOTAL_QUESTIONS - allocated

    if remaining == 0:
        return quotas

    # Distribute remaining slots to types that can absorb more
    # (i.e. present[t] > quotas[t]).  Use a simple greedy pass.
    # Repeat until remaining == 0 or no type can absorb more.
    types_ordered = sorted(present.keys(), key=lambda t: -(present[t] - quotas[t]))

    for _pass in range(TOTAL_QUESTIONS):  # at most TOTAL_QUESTIONS iterations
        if remaining <= 0:
            break
        made_progress = False
        for t in types_ordered:
            if remaining <= 0:
                break
            # How much more can this type absorb?
            can_absorb = present[t] - quotas[t]
            if can_absorb > 0:
                add = min(can_absorb, remaining)
                quotas[t] += add
                remaining -= add
                made_progress = True
        if not made_progress:
            break

    # If remaining > 0 after exhausting all capacity, allow repetition
    # by giving the extra slots to the type with the most questions.
    if remaining > 0:
        best = max(present, key=lambda t: present[t])
        quotas[best] += remaining

    return quotas


# ── Sampling ──────────────────────────────────────────────────────────────────

def _fill_to_n(pool: list, n: int, rng: random.Random) -> list:
    """
    Select exactly n questions from pool.

    - pool >= n : sample without replacement.
    - pool <  n : repeat-sample; avoids consecutive duplicates where possible.
    """
    if not pool:
        raise ValidationError("Cannot fill from an empty pool.")

    if len(pool) >= n:
        return rng.sample(pool, n)

    result: list = []
    last_id = None

    while len(result) < n:
        candidates = [q for q in pool if q.id != last_id] or pool
        chosen = rng.choice(candidates)
        result.append(chosen)
        last_id = chosen.id

    return result


# ── Serialisation ─────────────────────────────────────────────────────────────

def _serialize_question(q) -> dict:
    item: dict = {
        "id":               str(q.id),
        "text":             q.text,
        "question_type":    q.question_type,
        "difficulty":       q.difficulty,
        "order":            q.order,
        "is_auto_gradable": q.is_auto_gradable,
    }
    if q.language:
        item["language"] = q.language
    if q.metadata:
        item["metadata"] = q.metadata
    if q.question_type in ("single_choice", "multiple_choice"):
        item["options"] = [
            {"id": str(o.id), "text": o.text, "order": o.order}
            for o in sorted(q.options.all(), key=lambda o: o.order)
        ]
    return item


def _seed_from_attempt_id(attempt_id: str) -> int:
    return int(attempt_id.replace("-", ""), 16) % (2 ** 31)


# ── Public API ────────────────────────────────────────────────────────────────

def get_questions_for_attempt(
    test_id: str,
    seed: Optional[int] = None,
    attempt_id: Optional[str] = None,
) -> list[dict]:
    """
    Select exactly TOTAL_QUESTIONS (20) questions for an attempt.

    Target distribution (Task 3):
      single_choice   = 8
      multiple_choice = 8
      text            = 2
      code            = 2

    Fallback: if a type has fewer questions than its target, the deficit
    is redistributed to types with surplus.  If a type has 0 questions
    it is excluded entirely.

    Single DB query + prefetch_related (zero N+1).
    Reproducible when seed or attempt_id is provided.

    Args:
        test_id:    UUID string of the Test.
        seed:       Optional RNG seed for reproducibility.
        attempt_id: Optional attempt UUID; used to derive seed if seed is None.

    Returns:
        list of serialised question dicts, shuffled.

    Raises:
        ValidationError: if the test has no questions at all.
    """
    from apps.testing.models import Question

    # ── Resolve seed ──────────────────────────────────────────────────────────
    resolved_seed: Optional[int] = seed
    if resolved_seed is None and attempt_id is not None:
        resolved_seed = _seed_from_attempt_id(attempt_id)

    rng = random.Random(resolved_seed)

    # ── 1. Single query: all questions + prefetched options ───────────────────
    all_questions = list(
        Question.objects
        .filter(test_id=test_id)
        .prefetch_related(Prefetch("options"))
        .order_by()  # remove default ordering; we shuffle ourselves
    )

    if not all_questions:
        raise ValidationError(f"Test {test_id} has no questions.")

    # ── 2. Group by type (Python-side — no extra queries) ─────────────────────
    grouped: dict[str, list] = {t: [] for t in QUESTION_TYPES}
    for q in all_questions:
        if q.question_type in grouped:
            grouped[q.question_type].append(q)

    available_counts: dict[str, int] = {t: len(v) for t, v in grouped.items()}

    logger.debug(
        "get_questions_for_attempt: test=%s available=%s",
        test_id, available_counts,
    )

    # ── 3. Compute adaptive distribution ──────────────────────────────────────
    distribution = _compute_distribution(available_counts)

    logger.debug(
        "get_questions_for_attempt: distribution=%s", distribution,
    )

    # ── 4. Select per type ────────────────────────────────────────────────────
    selected: list = []
    for qtype in QUESTION_TYPES:
        quota = distribution.get(qtype, 0)
        if quota == 0:
            continue
        pool = grouped[qtype]
        chosen = _fill_to_n(pool, quota, rng)
        selected.extend(chosen)

    # ── 5. Shuffle so types are not clustered ─────────────────────────────────
    rng.shuffle(selected)

    # ── 6. Serialise (options already prefetched — zero extra queries) ─────────
    return [_serialize_question(q) for q in selected]


# ── Validation ────────────────────────────────────────────────────────────────

def validate_attempt_structure(answers: list[dict]) -> None:
    """
    Validate that submitted answers match the expected total.

    Rules:
      - Exactly TOTAL_QUESTIONS (20) answers required.
      - Only known question types accepted.

    Note: strict per-type distribution validation is intentionally relaxed
    because the fallback algorithm may produce distributions that differ from
    TARGET_DISTRIBUTION when the test has fewer questions in certain types.

    Raises:
        ValidationError: with a descriptive message.
    """
    if not isinstance(answers, list):
        raise ValidationError("answers must be a list.")

    if len(answers) != TOTAL_QUESTIONS:
        raise ValidationError(
            f"Expected exactly {TOTAL_QUESTIONS} answers, got {len(answers)}."
        )

    for i, answer in enumerate(answers):
        qtype = (
            answer.get("question_type")
            or (answer.get("question") or {}).get("question_type")
        )
        if not qtype:
            raise ValidationError(
                f"Answer at index {i} is missing 'question_type'."
            )
        if qtype not in QUESTION_TYPES:
            raise ValidationError(
                f"Answer at index {i} has unknown question_type='{qtype}'. "
                f"Allowed: {QUESTION_TYPES}."
            )


# ── Integration helper ────────────────────────────────────────────────────────

def build_attempt_questions(test_id: str, attempt_id: str) -> list[dict]:
    """
    Convenience wrapper for AttemptService.start_attempt().

    Seed is derived from attempt_id so the same attempt always
    produces the same question set (idempotent on retry).
    """
    return get_questions_for_attempt(
        test_id=test_id,
        attempt_id=attempt_id,
    )