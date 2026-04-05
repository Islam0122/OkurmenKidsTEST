"""
exam_state.py — Per-connection exam state machine.

States:
    WAITING      → client connected, waiting for "start" message
    STARTING     → validating session + creating attempt with Django
    IN_PROGRESS  → questions being answered
    FINISHING    → finish request sent to Django, awaiting result
    DONE         → attempt finished, result delivered
    ERROR        → terminal error state

The state machine is NOT thread-safe on its own; it is designed for a
single asyncio task per WebSocket connection (which FastAPI guarantees).
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any


class ExamState(Enum):
    WAITING     = auto()
    STARTING    = auto()
    IN_PROGRESS = auto()
    FINISHING   = auto()
    DONE        = auto()
    ERROR       = auto()


class QuestionType(str, Enum):
    SINGLE_CHOICE   = "single_choice"
    MULTIPLE_CHOICE = "multiple_choice"
    TEXT            = "text"
    CODE            = "code"


@dataclass
class Question:
    id:              str
    text:            str
    question_type:   str
    difficulty:      str
    order:           int
    is_auto_gradable: bool
    options:         list[dict]  = field(default_factory=list)
    language:        str         = ""
    metadata:        dict        = field(default_factory=dict)

    @classmethod
    def from_dict(cls, d: dict) -> "Question":
        return cls(
            id=d["id"],
            text=d["text"],
            question_type=d["type"],
            difficulty=d.get("difficulty", "medium"),
            order=d.get("order", 0),
            is_auto_gradable=d.get("is_auto_gradable", False),
            options=d.get("options", []),
            language=d.get("language", ""),
            metadata=d.get("metadata", {}),
        )

    def to_client_dict(self) -> dict:
        """Serialise for sending to the browser (no correct-answer leaks)."""
        d: dict[str, Any] = {
            "id":              self.id,
            "text":            self.text,
            "type":            self.question_type,
            "difficulty":      self.difficulty,
            "order":           self.order,
            "is_auto_gradable": self.is_auto_gradable,
        }
        if self.options:
            d["options"] = self.options  # already stripped of is_correct by Django
        if self.language:
            d["language"] = self.language
        if self.metadata:
            d["metadata"] = self.metadata
        return d


@dataclass
class AnswerRecord:
    question_id:    str
    answer_id:      str
    is_correct:     bool | None
    grading_status: str
    answered_at:    float = field(default_factory=time.time)


@dataclass
class ExamSession:
    """All runtime state for one student's exam session."""

    # ── Immutable after STARTING ──────────────────────────────────────────────
    session_key:   str = ""
    session_id:    str = ""
    student_name:  str = ""
    attempt_id:    str = ""
    test_title:    str = ""
    session_type:  str = "exam"  # "exam" | "training"
    expires_at:    str = ""

    # ── Questions ────────────────────────────────────────────────────────────
    questions:      list[Question]     = field(default_factory=list)
    current_index:  int                = 0      # pointer into questions list
    answers:        dict[str, AnswerRecord] = field(default_factory=dict)  # q_id → record

    # ── Timing ───────────────────────────────────────────────────────────────
    started_at:  float = field(default_factory=time.time)
    last_active: float = field(default_factory=time.time)

    # ── State ────────────────────────────────────────────────────────────────
    state: ExamState = ExamState.WAITING

    # ── Finish result cache ───────────────────────────────────────────────────
    finish_result: dict | None = None

    # ── Derived helpers ───────────────────────────────────────────────────────

    @property
    def total_questions(self) -> int:
        return len(self.questions)

    @property
    def answered_count(self) -> int:
        return len(self.answers)

    @property
    def correct_count(self) -> int:
        return sum(1 for a in self.answers.values() if a.is_correct is True)

    @property
    def score_so_far(self) -> float:
        """Running score based on auto-graded answers only."""
        graded = [a for a in self.answers.values() if a.is_correct is not None]
        if not graded:
            return 0.0
        correct = sum(1 for a in graded if a.is_correct)
        return round(correct / len(graded) * 100, 1)

    @property
    def current_question(self) -> Question | None:
        if 0 <= self.current_index < len(self.questions):
            return self.questions[self.current_index]
        return None

    @property
    def is_last_question(self) -> bool:
        return self.current_index >= len(self.questions) - 1

    @property
    def all_answered(self) -> bool:
        answered_ids = set(self.answers)
        return all(q.id in answered_ids for q in self.questions)

    def touch(self):
        self.last_active = time.time()

    def advance(self):
        """Move to next unanswered question. Returns True if advanced."""
        # Find next question not yet answered
        start = self.current_index + 1
        for i in range(start, len(self.questions)):
            if self.questions[i].id not in self.answers:
                self.current_index = i
                return True
        # Try finding any unanswered question from beginning
        for i in range(0, len(self.questions)):
            if self.questions[i].id not in self.answers:
                self.current_index = i
                return True
        return False  # all answered

    def record_answer(
        self,
        question_id:    str,
        answer_id:      str,
        is_correct:     bool | None,
        grading_status: str,
    ):
        self.answers[question_id] = AnswerRecord(
            question_id=question_id,
            answer_id=answer_id,
            is_correct=is_correct,
            grading_status=grading_status,
        )

    def progress_dict(self) -> dict:
        return {
            "answered":      self.answered_count,
            "total":         self.total_questions,
            "correct":       self.correct_count,
            "score_so_far":  self.score_so_far,
            "current_index": self.current_index,
        }