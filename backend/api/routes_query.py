"""Query API routes — conversational Q&A over research results."""

import logging

from fastapi import APIRouter, HTTPException

from models.paper import QueryRequest
from agents.conversational_agent import chat, get_history
from agents.orchestrator import get_session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["query"])


@router.post("/query")
async def query_papers(request: QueryRequest):
    """Ask a follow-up question about the research results.

    Uses ChromaDB retrieval + conversation history + Gemini to answer.
    """
    session = get_session(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session["status"] not in ("completed", "running"):
        raise HTTPException(
            status_code=400,
            detail=f"Session is not ready for queries (status: {session['status']})",
        )

    logger.info(f"Query for session {request.session_id}: '{request.question[:60]}'")

    total_papers = len(session.get("papers", []))
    answer = chat(
        session_id=request.session_id,
        question=request.question,
        total_papers=total_papers,
    )

    return {"answer": answer, "session_id": request.session_id}


@router.get("/history/{session_id}")
async def get_chat_history(session_id: str):
    """Get the conversation history for a session."""
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    history = get_history(session_id)
    return {"session_id": session_id, "history": history}
