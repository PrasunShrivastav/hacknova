"""Paper data models for ARIA."""

from pydantic import BaseModel, Field
from typing import Optional


class Paper(BaseModel):
    """Represents a single academic paper."""
    paper_id: str = ""
    title: str = ""
    abstract: str = ""
    authors: list[str] = Field(default_factory=list)
    year: Optional[int] = None
    url: str = ""
    pdf_url: str = ""
    source: str = ""  # "arxiv", "semantic_scholar", "pubmed"
    arxiv_id: str = ""
    citation_count: int = 0
    core_claims: list[str] = Field(default_factory=list)
    methodology: str = ""
    key_results: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    domain: str = ""
    embedding: list[float] = Field(default_factory=list, exclude=True)

    def unique_id(self) -> str:
        """Generate a unique identifier for deduplication."""
        if self.arxiv_id:
            return f"arxiv:{self.arxiv_id}"
        if self.paper_id:
            return f"ss:{self.paper_id}"
        return f"title:{self.title[:80].lower().strip()}"


class PaperSearchRequest(BaseModel):
    """Request body for starting a research session."""
    question: str
    max_papers: int = Field(default=30, ge=5, le=100)
    depth: int = Field(default=2, ge=0, le=3)


class QueryRequest(BaseModel):
    """Request body for conversational Q&A."""
    session_id: str
    question: str
