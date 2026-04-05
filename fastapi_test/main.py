from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from ws_handler import ExamWebSocketHandler
from django_client import DjangoAPIClient
from config import settings


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("main")



@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting OkurmenKids WS Engine …")
    logger.info("Django API base: %s", settings.DJANGO_API_BASE)
    yield
    logger.info("Shutting down …")
    await DjangoAPIClient.close()



app = FastAPI(
    title="OkurmenKids WebSocket Engine",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



@app.get("/health")
async def health():
    return {"status": "ok", "engine": "OkurmenKids WS v1.0"}


@app.get("/api/django-health")
async def django_health():
    """Proxy-check that Django backend is reachable."""
    try:
        async with DjangoAPIClient.session() as client:
            data = await client.get_raw("/health/")
        return {"status": "ok", "django": data}
    except Exception as exc:
        return JSONResponse({"status": "error", "detail": str(exc)}, status_code=502)



@app.websocket("/ws/exam")
async def exam_websocket(websocket: WebSocket):
    """
    Main WebSocket endpoint.

    Protocol (JSON messages):

    Client → Server:
        { "type": "start",        "session_key": "...", "student_name": "..." }
        { "type": "answer",       "question_id": "...", "selected_options": [...] }
        { "type": "answer",       "question_id": "...", "answer_text": "..." }
        { "type": "finish"                                                         }
        { "type": "ping"                                                           }

    Server → Client:
        { "type": "session_info",  ... session metadata ... }
        { "type": "question",      ... question data ...    }
        { "type": "answer_result", "is_correct": bool|null, "grading_status": str, ... }
        { "type": "progress",      "answered": int, "total": int, "score_so_far": float }
        { "type": "finish_result", ... final scores ...     }
        { "type": "error",         "code": str, "message":str }
        { "type": "pong"                                       }
    """
    handler = ExamWebSocketHandler(websocket)
    await handler.run()


# ── Serve frontend ────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    try:
        with open("example_test.html", "r", encoding="utf-8") as f:
            return HTMLResponse(f.read())
    except FileNotFoundError:
        return HTMLResponse("<h1>example_test.html not found</h1>", status_code=404)


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info",
    )