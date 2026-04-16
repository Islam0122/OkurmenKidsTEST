from __future__ import annotations

import random
from collections import defaultdict
from typing import Optional

from django.core.exceptions import ValidationError
from django.db.models import Prefetch


QUESTIONS_PER_TYPE = 5
QUESTION_TYPES = ["single_choice", "multiple_choice", "text", "code"]
TOTAL_QUESTIONS = len(QUESTION_TYPES) * QUESTIONS_PER_TYPE  # 20


# ── Helpers ───────────────────────────────────────────────────────────────────

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


def _fill_to_n(pool: list, n: int, rng: random.Random) -> list:
    """
    If pool has fewer than n items, repeat-sample until we reach n.
    Avoids consecutive duplicates when possible.
    """
    if len(pool) >= n:
        return rng.sample(pool, n)

    result: list = []
    last_id = None

    while len(result) < n:
        available = [q for q in pool if q.id != last_id]
        if not available:
            available = pool  # only one question — must repeat
        chosen = rng.choice(available)
        result.append(chosen)
        last_id = chosen.id

    return result


def _seed_from_attempt_id(attempt_id: str) -> int:
    """Derive a deterministic int seed from a UUID string."""
    return int(attempt_id.replace("-", ""), 16) % (2 ** 31)


# ── Public API ────────────────────────────────────────────────────────────────

def get_questions_for_attempt(
    test_id: str,
    seed: Optional[int] = None,
    attempt_id: Optional[str] = None,
) -> list[dict]:
    """
    Select exactly 20 questions (5 per type) for a test attempt.

    Priority for seed:
      1. explicit `seed` param
      2. derived from `attempt_id` if provided
      3. fully random (no seed)

    Single DB query + prefetch_related (no N+1).
    Fills with repeated questions if a type has < 5 in the test.
    Shuffles the final 20 so types are interleaved.

    Raises ValidationError if any question type is completely absent.
    """
    from ..models import Question

    # ── Resolve seed ──────────────────────────────────────────────────────────
    resolved_seed: Optional[int] = seed
    if resolved_seed is None and attempt_id is not None:
        resolved_seed = _seed_from_attempt_id(attempt_id)

    rng = random.Random(resolved_seed)

    # ── 1. Single query: all questions for this test + options ────────────────
    all_questions = list(
        Question.objects
        .filter(test_id=test_id)
        .prefetch_related(Prefetch("options"))
        .order_by()  # strip default ordering for pure random sampling
    )

    if not all_questions:
        raise ValidationError(f"Test {test_id} has no questions.")

    # ── 2. Group by type in Python (zero extra queries) ───────────────────────
    grouped: dict[str, list] = defaultdict(list)
    for q in all_questions:
        grouped[q.question_type].append(q)

    # ── 3. Validate all types are present ─────────────────────────────────────
    missing = [t for t in QUESTION_TYPES if not grouped.get(t)]
    if missing:
        raise ValidationError(
            f"Test {test_id} is missing question types: {missing}. "
            "All four types (single_choice, multiple_choice, text, code) are required."
        )

    # ── 4. Select exactly 5 per type ─────────────────────────────────────────
    selected: list = []
    for qtype in QUESTION_TYPES:
        pool = grouped[qtype]
        chosen = _fill_to_n(pool, QUESTIONS_PER_TYPE, rng)
        selected.extend(chosen)

    # ── 5. Shuffle so types are interleaved ───────────────────────────────────
    rng.shuffle(selected)

    # ── 6. Serialize (no extra queries — options already prefetched) ──────────
    return [_serialize_question(q) for q in selected]


# ── Validation ────────────────────────────────────────────────────────────────

def validate_attempt_structure(answers: list[dict]) -> None:
    """
    Validate that a submitted answer list matches the expected structure:
      - Exactly 20 answers total
      - Exactly 5 answers per question type

    Each answer dict must contain one of:
      - { "question_type": "..." }
      - { "question": { "question_type": "..." } }

    Raises ValidationError with a descriptive message on any violation.
    """
    if not isinstance(answers, list):
        raise ValidationError("answers must be a list.")

    if len(answers) != TOTAL_QUESTIONS:
        raise ValidationError(
            f"Expected exactly {TOTAL_QUESTIONS} answers, got {len(answers)}."
        )

    type_counts: dict[str, int] = defaultdict(int)

    for i, answer in enumerate(answers):
        # Support both flat { question_type } and nested { question: { question_type } }
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

    violations = [
        f"  '{qtype}': expected {QUESTIONS_PER_TYPE}, got {type_counts.get(qtype, 0)}"
        for qtype in QUESTION_TYPES
        if type_counts.get(qtype, 0) != QUESTIONS_PER_TYPE
    ]
    if violations:
        raise ValidationError(
            "Attempt structure invalid — type distribution mismatch:\n"
            + "\n".join(violations)
        )


def build_attempt_questions(test_id: str, attempt_id: str) -> list[dict]:
    return get_questions_for_attempt(
        test_id=test_id,
        attempt_id=attempt_id,
    )