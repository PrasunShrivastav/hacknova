"""Conversational agent — session memory + ChromaDB retrieval for follow-up Q&A."""

import logging

from vector.chroma_store import query_papers
from llm_client import call_gemini

logger = logging.getLogger(__name__)

# In-memory session conversation history
_sessions: dict[str, list[dict]] = {}


def chat(session_id: str, question: str, total_papers: int = 0) -> str:
    """Answer a follow-up question using retrieved papers and conversation history.

    Args:
        session_id: Research session ID.
        question: User's follow-up question.
        total_papers: Total papers in the session (for context).

    Returns:
        ARIA's response string.
    """
    history = _sessions.get(session_id, [])

    # Retrieve most relevant papers from ChromaDB
    relevant = query_papers(session_id, question, top_k=5)
    context = "\n\n".join([
        f"📄 [{p.get('title', 'Untitled')} ({p.get('year', '?')})]:\n{p.get('abstract', '')[:500]}"
        for p in relevant
    ])

    if not context:
        context = "No papers found in the database for this session."

    # Build conversation history (last 6 messages)
    history_text = "\n".join([
        f"{m['role'].upper()}: {m['content']}"
        for m in history[-6:]
    ])

    prompt = f"""You are ARIA, an AI research assistant. You have analyzed {total_papers} academic papers on behalf of the user.

Answer the user's question by reasoning across the papers you've read. Always cite specific papers when making claims.
Be thorough but concise. If you're unsure, say so.

RELEVANT PAPERS (from vector search):
{context}

CONVERSATION HISTORY:
{history_text}

USER: {question}

ARIA:"""

    try:
        answer = call_gemini(prompt)
        logger.info(f"Chat response generated for session {session_id}: {len(answer)} chars")
    except Exception as e:
        logger.error(f"Chat error: {e}")
        answer = "I apologize, but I encountered an error processing your question. Please try again in a moment."

    # Update history
    history.append({"role": "user", "content": question})
    history.append({"role": "assistant", "content": answer})
    _sessions[session_id] = history

    return answer


def get_history(session_id: str) -> list[dict]:
    """Get the conversation history for a session."""
    return _sessions.get(session_id, [])


def clear_session(session_id: str):
    """Clear the conversation history for a session."""
    _sessions.pop(session_id, None)
