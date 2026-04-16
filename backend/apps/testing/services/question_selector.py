from __future__ import annotations

import random
from collections import defaultdict
from typing import Optional

from django.core.exceptions import ValidationError
from django.db.models import Prefetch


TOTAL_QUESTIONS = 20
QUESTION_TYPES  = ["single_choice", "multiple_choice", "text", "code"]


# ── Distribution ──────────────────────────────────────────────────────────────

def _compute_distribution(available_types: list[str]) -> dict[str, int]:
    """
    Distribute TOTAL_QUESTIONS as evenly as possible across available types.

    Examples (TOTAL_QUESTIONS = 20):
      4 types → {each: 5}          → [5, 5, 5, 5]
      3 types → {two: 7, one: 6}   → [7, 7, 6]
      2 types → {each: 10}         → [10, 10]
      1 type  → {one: 20}          → [20]

    Remainder is distributed left-to-right (first types get the extra question).
    """
    n = len(available_types)
    if n == 0:
        return {}

    base, remainder = divmod(TOTAL_QUESTIONS, n)

    return {
        qtype: base + (1 if i < remainder else 0)
        for i, qtype in enumerate(available_types)
    }


# ── Helpers ───────────────────────────────────────────────────────────────────

def _fill_to_n(pool: list, n: int, rng: random.Random) -> list:
    """
    Select exactly n questions from pool.

    - pool >= n : random sample without duplicates.
    - pool <  n : repeat-sample until n reached,
                  avoiding consecutive duplicates where possible.
    """
    if not pool:
        raise ValidationError("Cannot fill from an empty pool.")

    if len(pool) >= n:
        return rng.sample(pool, n)

    result: list = []
    last_id = None

    while len(result) < n:
        available = [q for q in pool if q.id != last_id]
        if not available:
            available = pool  # single-item pool — must repeat
        chosen = rng.choice(available)
        result.append(chosen)
        last_id = chosen.id

    return result


def _serialize_question(q) -> dict:
    item = {
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
    Select exactly TOTAL_QUESTIONS (20) questions for an attempt
    with adaptive distribution across available question types.

    Distribution rules:
      - 4 types present → 5 each
      - 3 types present → 7, 7, 6
      - 2 types present → 10, 10
      - 1 type  present → 20

    If a type has fewer questions than its quota, questions are
    repeated randomly (no consecutive duplicates where possible).

    Single DB query + prefetch_related (zero N+1).
    Reproducible when seed or attempt_id is provided.

    Raises ValidationError if the test has no questions at all.
    """
    from ..models import Question

    # ── Resolve seed ──────────────────────────────────────────────────────────
    resolved_seed: Optional[int] = seed
    if resolved_seed is None and attempt_id is not None:
        resolved_seed = _seed_from_attempt_id(attempt_id)

    rng = random.Random(resolved_seed)

    # ── 1. Single query: fetch all questions + options ────────────────────────
    all_questions = list(
        Question.objects
        .filter(test_id=test_id)
        .prefetch_related(Prefetch("options"))
        .order_by()  # strip default ordering; we shuffle ourselves
    )

    if not all_questions:
        raise ValidationError(f"Test {test_id} has no questions.")

    # ── 2. Group by type (Python-side, no extra queries) ─────────────────────
    grouped: dict[str, list] = defaultdict(list)
    for q in all_questions:
        grouped[q.question_type].append(q)

    # Preserve canonical type order; include only types that exist in this test
    available_types = [t for t in QUESTION_TYPES if grouped.get(t)]

    # ── 3. Compute adaptive distribution ─────────────────────────────────────
    distribution = _compute_distribution(available_types)

    # ── 4. Select per type ───────────────────────────────────────────────────
    selected: list = []
    for qtype in available_types:
        quota = distribution[qtype]
        pool  = grouped[qtype]
        chosen = _fill_to_n(pool, quota, rng)
        selected.extend(chosen)

    # ── 5. Shuffle so types are not clustered ─────────────────────────────────
    rng.shuffle(selected)

    # ── 6. Serialize (options already prefetched — zero extra queries) ────────
    return [_serialize_question(q) for q in selected]


# ── Validation ────────────────────────────────────────────────────────────────

def validate_attempt_structure(answers: list[dict]) -> None:
    """
    Validate that a submitted answer list matches the adaptive distribution
    that would have been generated for the same set of question types.

    Rules enforced:
      - Exactly TOTAL_QUESTIONS (20) answers.
      - Only known question types.
      - Type distribution matches _compute_distribution() for the
        types actually present in the answers.

    Raises ValidationError with a descriptive message on any violation.
    """
    if not isinstance(answers, list):
        raise ValidationError("answers must be a list.")

    if len(answers) != TOTAL_QUESTIONS:
        raise ValidationError(
            f"Expected exactly {TOTAL_QUESTIONS} answers, got {len(answers)}."
        )

    # ── Count types present in answers ────────────────────────────────────────
    type_counts: dict[str, int] = defaultdict(int)
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
        type_counts[qtype] += 1

    # ── Reconstruct expected distribution ─────────────────────────────────────
    present_types = [t for t in QUESTION_TYPES if type_counts.get(t, 0) > 0]
    expected_dist = _compute_distribution(present_types)

    violations = [
        f"  '{qtype}': expected {expected_dist.get(qtype, 0)}, got {type_counts.get(qtype, 0)}"
        for qtype in present_types
        if type_counts.get(qtype, 0) != expected_dist.get(qtype, 0)
    ]
    if violations:
        raise ValidationError(
            f"Attempt structure invalid — distribution mismatch "
            f"({len(present_types)} type(s) detected, "
            f"expected {expected_dist}):\n" + "\n".join(violations)
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