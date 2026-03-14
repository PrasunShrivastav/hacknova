"""Output models for ARIA research results."""

from pydantic import BaseModel, Field
from typing import Optional


class ResearchGap(BaseModel):
    rank: int
    gap: str
    evidence: str
    importance: str = "medium"


class ResearchGapsOutput(BaseModel):
    gaps: list[ResearchGap] = Field(default_factory=list)


class ResearchResults(BaseModel):
    """Complete results of a research session."""
    session_id: str
    question: str
    summary: str = ""
    contradictions: str = ""
    gaps: Optional[ResearchGapsOutput] = None
    papers: list[dict] = Field(default_factory=list)
    status: str = "pending"  # pending, running, completed, failed
    error: Optional[str] = None


class StatusEvent(BaseModel):
    """Single status event for SSE streaming."""
    event: str
    detail: str
    progress: int = 0  # 0-100
