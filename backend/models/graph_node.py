"""Knowledge graph node and edge models."""

from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class EdgeType(str, Enum):
    CITES = "cites"
    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"
    RELATED = "related"


class GraphNode(BaseModel):
    """Represents a node in the knowledge graph (one paper)."""
    id: str
    label: str  # paper title (truncated)
    title: str  # full title
    year: Optional[int] = None
    domain: str = ""
    authors: list[str] = Field(default_factory=list)
    claims: list[str] = Field(default_factory=list)
    source: str = ""
    citation_count: int = 0


class GraphEdge(BaseModel):
    """Represents an edge between two papers in the knowledge graph."""
    source: str
    target: str
    edge_type: EdgeType
    weight: float = 1.0
    reason: str = ""


class GraphData(BaseModel):
    """Serializable knowledge graph for the frontend."""
    nodes: list[GraphNode] = Field(default_factory=list)
    edges: list[GraphEdge] = Field(default_factory=list)
