"""Research API routes — start research sessions and stream status via SSE."""

import asyncio
import json
import logging

from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import StreamingResponse

from models.paper import PaperSearchRequest
from agents.orchestrator import (
    create_session,
    get_session,
    get_status_queue,
    run_research_pipeline,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["research"])


@router.post("/research")
async def start_research(
    request: PaperSearchRequest,
    background_tasks: BackgroundTasks,
):
    """Start a new ARIA research session.

    Creates a session, kicks off the pipeline in the background,
    and returns the session ID immediately.
    """
    logger.info(f"New research request: '{request.question[:60]}', max_papers={request.max_papers}, depth={request.depth}")

    session_id = create_session(request.question)

    # Run the pipeline in the background
    background_tasks.add_task(
        run_research_pipeline,
        session_id=session_id,
        max_papers=request.max_papers,
        depth=request.depth,
    )

    return {"session_id": session_id}


@router.get("/status/{session_id}")
async def stream_status(session_id: str):
    """Stream real-time status updates via Server-Sent Events (SSE).

    The client should connect to this endpoint using EventSource.
    Events are streamed as they happen during the research pipeline.
    """
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    queue = get_status_queue(session_id)
    if not queue:
        raise HTTPException(status_code=404, detail="Status stream not available")

    async def event_generator():
        try:
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=300)
                except asyncio.TimeoutError:
                    # Send keepalive
                    yield f"data: {json.dumps({'event': 'keepalive', 'detail': '', 'progress': -1})}\n\n"
                    continue

                if event is None:
                    # Pipeline finished
                    yield f"data: {json.dumps({'event': 'done', 'detail': 'Stream closed', 'progress': 100})}\n\n"
                    break

                yield f"data: {json.dumps(event)}\n\n"
        except asyncio.CancelledError:
            logger.info(f"SSE stream cancelled for session {session_id}")
        except Exception as e:
            logger.error(f"SSE stream error: {e}")
            yield f"data: {json.dumps({'event': 'error', 'detail': str(e), 'progress': -1})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/results/{session_id}")
async def get_results(session_id: str):
    """Get the complete results of a research session.

    Returns summary, contradictions, gaps, and papers once the pipeline is done.
    """
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session["status"] == "running":
        return {
            "status": "running",
            "message": "Research is still in progress. Connect to /api/status/{session_id} for live updates.",
        }

    if session["status"] == "failed":
        raise HTTPException(
            status_code=500,
            detail=f"Research failed: {session.get('error', 'Unknown error')}",
        )

    # Parse gaps JSON if it's a string
    gaps = session.get("gaps", "")
    if isinstance(gaps, str):
        try:
            gaps = json.loads(gaps)
        except json.JSONDecodeError:
            gaps = {"gaps": []}

    return {
        "status": session["status"],
        "session_id": session_id,
        "question": session.get("question", ""),
        "summary": session.get("summary", ""),
        "contradictions": session.get("contradictions", ""),
        "gaps": gaps,
        "papers": session.get("papers", []),
    }
