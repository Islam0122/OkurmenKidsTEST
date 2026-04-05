"""
ws_handler.py — WebSocket connection handler.

One ExamWebSocketHandler instance is created per connected client.
It owns the full lifecycle: accept → start → answer loop → finish → close.

Design notes:
  • A single asyncio task handles the entire connection (no threading).
  • Heartbeat runs as a background task to keep idle connections alive.
  • All Django API calls are awaited; errors are caught and sent as
    structured error messages before the connection is closed.
  • The state machine (ExamSession) is the single source of truth.
"""
from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect

from config import settings
from django_client import (
    DjangoAPIClient,
    DjangoAPIError,
    SessionExpiredError,
    AttemptError,
)
from exam_state import ExamSession, ExamState, Question

logger = logging.getLogger("ws_handler")


# ── Error codes (align with client-side handling) ─────────────────────────────

class ErrCode:
    INVALID_SESSION  = "INVALID_SESSION"
    SESSION_EXPIRED  = "SESSION_EXPIRED"
    ATTEMPT_ERROR    = "ATTEMPT_ERROR"
    ANSWER_ERROR     = "ANSWER_ERROR"
    INVALID_PAYLOAD  = "INVALID_PAYLOAD"
    DJANGO_ERROR     = "DJANGO_ERROR"
    IDLE_TIMEOUT     = "IDLE_TIMEOUT"
    PROTOCOL_ERROR   = "PROTOCOL_ERROR"
    INTERNAL         = "INTERNAL_ERROR"


# ── Handler ───────────────────────────────────────────────────────────────────

class ExamWebSocketHandler:
    """
    Manages one WebSocket connection through the full exam lifecycle.

    Message flow:
        client sends  { type: "start", session_key, student_name }
        server sends  { type: "session_info", ... }
        server sends  { type: "question", ... first question ... }

        loop:
          client sends  { type: "answer", question_id, selected_options|answer_text }
          server sends  { type: "answer_result", ... }
          server sends  { type: "question", ... next question ... }  OR
          server sends  { type: "all_answered", message }

        client sends  { type: "finish" }  (or server auto-finishes if all answered)
        server sends  { type: "finish_result", ... }
    """

    def __init__(self, websocket: WebSocket):
        self.ws      = websocket
        self.session = ExamSession()
        self._heartbeat_task: asyncio.Task | None = None
        self._peer: str = ""

    # ── Entry point ───────────────────────────────────────────────────────────

    async def run(self):
        await self.ws.accept()
        self._peer = str(self.ws.client)
        logger.info("WS connected: %s", self._peer)

        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

        try:
            await self._message_loop()
        except WebSocketDisconnect as exc:
            logger.info("WS disconnected: %s  code=%s", self._peer, exc.code)
        except Exception as exc:
            logger.exception("Unhandled error in WS handler for %s", self._peer)
            await self._send_error(ErrCode.INTERNAL, f"Internal server error: {exc}")
        finally:
            if self._heartbeat_task:
                self._heartbeat_task.cancel()
            logger.info("WS handler teardown: %s", self._peer)

    # ── Message loop ──────────────────────────────────────────────────────────

    async def _message_loop(self):
        while True:
            # Enforce idle timeout
            idle = time.time() - self.session.last_active
            if idle > settings.WS_IDLE_TIMEOUT and self.session.state not in (
                ExamState.DONE, ExamState.ERROR
            ):
                await self._send_error(ErrCode.IDLE_TIMEOUT, "Session timed out due to inactivity.")
                await self.ws.close(code=1000)
                return

            try:
                raw = await asyncio.wait_for(
                    self.ws.receive_text(),
                    timeout=settings.WS_IDLE_TIMEOUT,
                )
            except asyncio.TimeoutError:
                await self._send_error(ErrCode.IDLE_TIMEOUT, "Idle timeout exceeded.")
                await self.ws.close(code=1000)
                return

            self.session.touch()

            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                await self._send_error(ErrCode.INVALID_PAYLOAD, "Message must be valid JSON.")
                continue

            msg_type = msg.get("type", "")
            logger.debug("← [%s] type=%s state=%s", self._peer[:20], msg_type, self.session.state.name)

            await self._dispatch(msg_type, msg)

            if self.session.state in (ExamState.DONE, ExamState.ERROR):
                # Give client a moment to receive the final message
                await asyncio.sleep(0.5)
                await self.ws.close(code=1000)
                return

    # ── Dispatcher ────────────────────────────────────────────────────────────

    async def _dispatch(self, msg_type: str, msg: dict):
        state = self.session.state

        if msg_type == "ping":
            await self._send({"type": "pong"})
            return

        match (state, msg_type):
            case (ExamState.WAITING, "start"):
                await self._handle_start(msg)

            case (ExamState.IN_PROGRESS, "answer"):
                await self._handle_answer(msg)

            case (ExamState.IN_PROGRESS, "finish"):
                await self._handle_finish()

            case (ExamState.IN_PROGRESS, "get_question"):
                # Client can request current question again (e.g. after reconnect)
                await self._send_current_question()

            case (ExamState.DONE, _):
                await self._send_error(ErrCode.PROTOCOL_ERROR, "Attempt already finished.")

            case _:
                await self._send_error(
                    ErrCode.PROTOCOL_ERROR,
                    f"Unexpected message type '{msg_type}' in state {state.name}.",
                )

    # ── Start ─────────────────────────────────────────────────────────────────

    async def _handle_start(self, msg: dict):
        session_key  = (msg.get("session_key") or "").strip()
        student_name = (msg.get("student_name") or "").strip()

        if not session_key:
            await self._send_error(ErrCode.INVALID_PAYLOAD, "session_key is required.")
            return
        if not student_name:
            await self._send_error(ErrCode.INVALID_PAYLOAD, "student_name is required.")
            return

        self.session.state       = ExamState.STARTING
        self.session.session_key = session_key
        self.session.student_name = student_name

        # Send "connecting" feedback immediately
        await self._send({"type": "connecting", "message": "Connecting to test server…"})

        try:
            # 1. Validate session
            session_data = await DjangoAPIClient.validate_session(session_key)

            # 2. Start attempt (creates DB record, returns questions)
            attempt_data = await DjangoAPIClient.start_attempt(session_key, student_name)

        except SessionExpiredError as exc:
            self.session.state = ExamState.ERROR
            await self._send_error(ErrCode.SESSION_EXPIRED, str(exc))
            return
        except AttemptError as exc:
            self.session.state = ExamState.ERROR
            await self._send_error(ErrCode.ATTEMPT_ERROR, str(exc))
            return
        except DjangoAPIError as exc:
            self.session.state = ExamState.ERROR
            await self._send_error(ErrCode.DJANGO_ERROR, str(exc))
            return

        # Populate state
        self.session.attempt_id   = attempt_data["attempt_id"]
        self.session.test_title   = attempt_data["test_title"]
        self.session.session_type = attempt_data.get("session_type", "exam")
        self.session.session_id   = session_data.get("id", "")
        self.session.expires_at   = session_data.get("expires_at", "")
        self.session.questions    = [
            Question.from_dict(q) for q in attempt_data.get("questions", [])
        ]
        self.session.current_index = 0
        self.session.state = ExamState.IN_PROGRESS

        logger.info(
            "Attempt started: student=%s attempt=%s questions=%d session_type=%s",
            student_name, self.session.attempt_id[:8],
            self.session.total_questions, self.session.session_type,
        )

        # 3. Send session info to client
        await self._send({
            "type":         "session_info",
            "attempt_id":   self.session.attempt_id,
            "test_title":   self.session.test_title,
            "session_type": self.session.session_type,
            "total":        self.session.total_questions,
            "expires_at":   self.session.expires_at,
            "student_name": student_name,
        })

        # 4. Send first question
        await self._send_current_question()

    # ── Answer ────────────────────────────────────────────────────────────────

    async def _handle_answer(self, msg: dict):
        question_id      = (msg.get("question_id") or "").strip()
        answer_text      = (msg.get("answer_text") or "").strip()
        selected_options: list[str] = [
            str(o) for o in msg.get("selected_options", [])
        ]

        if not question_id:
            await self._send_error(ErrCode.INVALID_PAYLOAD, "question_id is required.")
            return

        # Validate question belongs to this test
        q_ids = {q.id for q in self.session.questions}
        if question_id not in q_ids:
            await self._send_error(ErrCode.ANSWER_ERROR, "question_id not found in this test.")
            return

        # Already answered?  Django will upsert, but we warn client.
        already_answered = question_id in self.session.answers

        try:
            result = await DjangoAPIClient.submit_answer(
                attempt_id=self.session.attempt_id,
                question_id=question_id,
                answer_text=answer_text,
                selected_options=selected_options,
            )
        except DjangoAPIError as exc:
            await self._send_error(ErrCode.ANSWER_ERROR, str(exc))
            return

        # Record locally
        self.session.record_answer(
            question_id=question_id,
            answer_id=result["answer_id"],
            is_correct=result.get("is_correct"),
            grading_status=result.get("grading_status", "pending"),
        )

        # Find the question object for extra context
        question = next((q for q in self.session.questions if q.id == question_id), None)

        # Send answer result
        await self._send({
            "type":            "answer_result",
            "question_id":     question_id,
            "answer_id":       result["answer_id"],
            "is_correct":      result.get("is_correct"),
            "grading_status":  result.get("grading_status", "pending"),
            "message":         result.get("message", ""),
            "re_answer":       already_answered,
            "question_type":   question.question_type if question else "",
        })

        # Send updated progress
        await self._send({"type": "progress", **self.session.progress_dict()})

        # Auto-advance to next question
        if self.session.all_answered:
            await self._send({
                "type":    "all_answered",
                "message": "All questions answered. You may finish the test.",
                **self.session.progress_dict(),
            })
            # Auto-finish
            await self._handle_finish()
        else:
            # Move index past current if it was the current question
            if self.session.current_question and self.session.current_question.id == question_id:
                self.session.advance()
            await self._send_current_question()

    # ── Finish ────────────────────────────────────────────────────────────────

    async def _handle_finish(self):
        if self.session.state == ExamState.DONE:
            return  # idempotent

        self.session.state = ExamState.FINISHING
        await self._send({"type": "finishing", "message": "Calculating your results…"})

        try:
            finish_data = await DjangoAPIClient.finish_attempt(self.session.attempt_id)
        except AttemptError as exc:
            # Already finished is OK; fetch result instead
            if "already finished" in str(exc).lower():
                finish_data = await DjangoAPIClient.get_attempt_result(self.session.attempt_id)
            else:
                self.session.state = ExamState.ERROR
                await self._send_error(ErrCode.ATTEMPT_ERROR, str(exc))
                return
        except DjangoAPIError as exc:
            self.session.state = ExamState.ERROR
            await self._send_error(ErrCode.DJANGO_ERROR, str(exc))
            return

        self.session.state = ExamState.DONE
        self.session.finish_result = finish_data

        elapsed = time.time() - self.session.started_at

        await self._send({
            "type":              "finish_result",
            "attempt_id":        finish_data.get("attempt_id", self.session.attempt_id),
            "student_name":      self.session.student_name,
            "test_title":        self.session.test_title,
            "score":             finish_data.get("score", 0),
            "total_questions":   finish_data.get("total_questions", self.session.total_questions),
            "answered":          finish_data.get("answered", self.session.answered_count),
            "correct":           finish_data.get("correct", self.session.correct_count),
            "pending_grading":   finish_data.get("pending_grading", 0),
            "duration_seconds":  finish_data.get("duration_seconds") or elapsed,
            "session_type":      self.session.session_type,
        })

        logger.info(
            "Attempt finished: student=%s score=%.1f elapsed=%.0fs",
            self.session.student_name,
            finish_data.get("score", 0),
            elapsed,
        )

    # ── Helpers ───────────────────────────────────────────────────────────────

    async def _send_current_question(self):
        q = self.session.current_question
        if q is None:
            return
        payload = {
            "type":           "question",
            "question_number": self.session.current_index + 1,
            "total":           self.session.total_questions,
            **q.to_client_dict(),
            "already_answered": q.id in self.session.answers,
        }
        if q.id in self.session.answers:
            payload["previous_answer"] = {
                "is_correct":     self.session.answers[q.id].is_correct,
                "grading_status": self.session.answers[q.id].grading_status,
            }
        await self._send(payload)

    async def _send(self, data: dict):
        try:
            await self.ws.send_json(data)
            logger.debug("→ [%s] type=%s", self._peer[:20], data.get("type"))
        except Exception as exc:
            logger.warning("Failed to send to %s: %s", self._peer, exc)
            raise

    async def _send_error(self, code: str, message: str):
        logger.warning("Error to %s: [%s] %s", self._peer, code, message)
        try:
            await self.ws.send_json({
                "type":    "error",
                "code":    code,
                "message": message,
            })
        except Exception:
            pass  # connection may already be closed

    # ── Heartbeat ─────────────────────────────────────────────────────────────

    async def _heartbeat_loop(self):
        """Send periodic pings so proxies / load-balancers don't close idle WS."""
        try:
            while True:
                await asyncio.sleep(settings.WS_PING_INTERVAL)
                if self.session.state in (ExamState.DONE, ExamState.ERROR):
                    break
                try:
                    await self.ws.send_json({"type": "ping_server"})
                except Exception:
                    break
        except asyncio.CancelledError:
            pass