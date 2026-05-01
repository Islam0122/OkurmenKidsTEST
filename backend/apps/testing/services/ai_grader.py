
from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)



@dataclass
class GradeResult:
    is_correct:  Optional[bool]   # True / False / None (partial / uncertian)
    score:       float             # 0.0 – 10.0
    confidence:  float             # 0.0 – 1.0
    feedback:    str               # human-readable explanation
    suggestion:  str               # hint for the student
    raw_response: str = ""         # full GigaChat output (for debugging)

    def to_dict(self) -> dict:
        return {
            "is_correct": self.is_correct,
            "score":      round(self.score, 2),
            "confidence": round(self.confidence, 2),
            "feedback":   self.feedback,
            "suggestion": self.suggestion,
        }

_TEXT_PROMPT_TEMPLATE = """
You are a strict but fair academic grader working with beginner-level students (early-stage learners, ~1 month of study).

IMPORTANT CONTEXT:
- The student is a beginner.
- Be slightly lenient and supportive in grading.
- Reward partial understanding.
- Focus on the core idea rather than perfect completeness.

QUESTION:
{question}

STUDENT ANSWER:
{answer}

GRADING INSTRUCTIONS:
1. Assess factual correctness and completeness (0–10, integers only).
2. A score ≥ 6 means the answer is considered correct.
3. Give credit for partially correct answers.
4. Do not penalize heavily for small mistakes or missing details.
5. If the student shows basic understanding, score at least 6.
6. Be concise and avoid repetition.
7. Do not restate the question.
8. Do not include extra text or formatting.

RESPOND ONLY IN THIS EXACT FORMAT:
SCORE: <number>/10
CONFIDENCE: <decimal between 0 and 1>
FEEDBACK: <1–3 short sentences>
SUGGESTION: <1–2 short sentences>
""".strip()

_CODE_PROMPT_TEMPLATE = """
You are a senior {language} engineer and code reviewer working with beginner-level students (~1 month of experience).

IMPORTANT CONTEXT:
- The student is a beginner.
- Be slightly lenient and supportive.
- Reward partially correct logic even if not perfect.

TASK:
{question}

STUDENT CODE:
```{language}
{answer}
```

GRADING INSTRUCTIONS:
1. Check correctness: does the code solve the task? (most important)
2. Check code quality: naming, style, edge cases.
3. Score 0–10 (≥ 6 = correct solution).
4. Give concise code review feedback (1–3 sentences).
5. Suggest one concrete improvement (1–2 sentences).
6. Estimate your confidence (0.0–1.0).

RESPOND ONLY IN THIS EXACT FORMAT (no extra text):
SCORE: <number>/10
CONFIDENCE: <decimal between 0 and 1>
FEEDBACK: <your feedback>
SUGGESTION: <your suggestion>
""".strip()


def build_prompt(question_text: str, answer_text: str, question_type: str, language: str = "") -> str:
    if question_type == "code":
        lang = language or "code"
        return _CODE_PROMPT_TEMPLATE.format(
            language=lang,
            question=question_text.strip(),
            answer=answer_text.strip(),
        )
    return _TEXT_PROMPT_TEMPLATE.format(
        question=question_text.strip(),
        answer=answer_text.strip(),
    )



def _extract_float(pattern: str, text: str, default: float) -> float:
    m = re.search(pattern, text, re.IGNORECASE)
    if m:
        try:
            return float(m.group(1))
        except ValueError:
            pass
    return default


def _extract_text(pattern: str, text: str, default: str = "") -> str:
    m = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
    if m:
        return m.group(1).strip()
    return default


def parse_response(raw: str) -> GradeResult:
    """
    Parse GigaChat's structured reply into a GradeResult.
    Gracefully falls back on any parse error.
    """
    if not raw:
        return GradeResult(
            is_correct=None, score=0.0, confidence=0.0,
            feedback="AI did not return a response.",
            suggestion="Please try again or request manual review.",
            raw_response=raw,
        )

    # SCORE: X/10  or  SCORE: X
    score_raw  = _extract_float(r"SCORE\s*:\s*(\d+(?:\.\d+)?)\s*(?:/\s*10)?", raw, default=-1.0)
    confidence = _extract_float(r"CONFIDENCE\s*:\s*([01](?:\.\d+)?)", raw, default=0.5)
    feedback   = _extract_text(r"FEEDBACK\s*:\s*(.+?)(?=\nSUGGESTION\s*:|$)", raw, "No feedback provided.")
    suggestion = _extract_text(r"SUGGESTION\s*:\s*(.+?)$", raw, "No suggestion provided.")

    # Clamp values
    score      = min(max(score_raw, 0.0), 10.0) if score_raw >= 0 else 0.0
    confidence = min(max(confidence, 0.0), 1.0)
    is_correct: Optional[bool] = None if score_raw < 0 else (score >= 6.0)

    return GradeResult(
        is_correct=is_correct,
        score=score,
        confidence=confidence,
        feedback=feedback,
        suggestion=suggestion,
        raw_response=raw,
    )


# ── Main entry point ────────────────────────────────────────────────────────────

def grade_answer(answer_id: str) -> Optional[GradeResult]:
    """
    Load the Answer from DB, call GigaChat, return a GradeResult.
    Returns None if the answer cannot be graded (wrong type, missing data, API failure).

    DB persistence is intentionally NOT done here — the Celery task owns that.
    """
    from ..models import Answer, QuestionType

    try:
        answer = (
            Answer.objects
            .select_related("question", "attempt__session__test")
            .get(pk=answer_id)
        )
    except Answer.DoesNotExist:
        logger.error("grade_answer: Answer %s not found.", answer_id)
        return None

    question = answer.question

    if question.question_type not in (QuestionType.TEXT, QuestionType.CODE):
        logger.debug(
            "grade_answer: Answer %s is type=%s — skipped (auto-gradable).",
            answer_id, question.question_type,
        )
        return None

    answer_text = (answer.answer_text or "").strip()
    if not answer_text:
        logger.warning("grade_answer: Answer %s has empty answer_text.", answer_id)
        return GradeResult(
            is_correct=False, score=0.0, confidence=1.0,
            feedback="No answer was provided.",
            suggestion="Please submit your answer before the session expires.",
        )

    prompt = build_prompt(
        question_text=question.text,
        answer_text=answer_text,
        question_type=question.question_type,
        language=question.language or "",
    )

    from .gigachat import send_prompt, get_access_token
    token = get_access_token()
    if not token:
        logger.error("grade_answer: Could not obtain GigaChat token for answer %s.", answer_id)
        return None

    raw = send_prompt(prompt, token)
    if not raw:
        logger.error("grade_answer: GigaChat returned empty response for answer %s.", answer_id)
        return None

    result = parse_response(raw)
    logger.info(
        "grade_answer: answer=%s score=%.1f confidence=%.2f is_correct=%s",
        answer_id, result.score, result.confidence, result.is_correct,
    )
    return result