"""In-memory knowledge graph using NetworkX."""

import networkx as nx
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class KnowledgeGraph:
    """Manages a per-session knowledge graph of papers and their relationships."""

    def __init__(self):
        self.graph = nx.DiGraph()

    def add_paper(self, paper: dict) -> str:
        """Add a paper as a node in the graph.

        Args:
            paper: Paper dict with at minimum 'title'.

        Returns:
            The node ID used.
        """
        node_id = paper.get("paper_id") or paper.get("arxiv_id") or paper.get("title", "")[:60]
        if not node_id:
            return ""

        self.graph.add_node(
            node_id,
            label=paper.get("title", "")[:60],
            title=paper.get("title", ""),
            year=paper.get("year"),
            domain=paper.get("domain", ""),
            authors=paper.get("authors", []),
            claims=paper.get("core_claims", []),
            source=paper.get("source", ""),
            citation_count=paper.get("citation_count", 0),
            methodology=paper.get("methodology", ""),
            keywords=paper.get("keywords", []),
        )
        return node_id

    def add_citation_edge(self, from_id: str, to_id: str):
        """Add a 'cites' edge from one paper to another."""
        if from_id and to_id and from_id != to_id:
            self.graph.add_edge(from_id, to_id, edge_type="cites", weight=1.0, reason="citation")

    def add_support_edge(self, paper_a_id: str, paper_b_id: str, reason: str = ""):
        """Add a bidirectional 'supports' edge between two papers."""
        if paper_a_id and paper_b_id and paper_a_id != paper_b_id:
            self.graph.add_edge(paper_a_id, paper_b_id, edge_type="supports", weight=1.0, reason=reason)

    def add_contradiction_edge(self, paper_a_id: str, paper_b_id: str, reason: str = ""):
        """Add a bidirectional 'contradicts' edge between two papers."""
        if paper_a_id and paper_b_id and paper_a_id != paper_b_id:
            self.graph.add_edge(paper_a_id, paper_b_id, edge_type="contradicts", weight=1.0, reason=reason)
            self.graph.add_edge(paper_b_id, paper_a_id, edge_type="contradicts", weight=1.0, reason=reason)

    def add_related_edge(self, paper_a_id: str, paper_b_id: str, similarity: float = 0.0):
        """Add a 'related' edge based on embedding similarity."""
        if paper_a_id and paper_b_id and paper_a_id != paper_b_id:
            self.graph.add_edge(
                paper_a_id, paper_b_id,
                edge_type="related", weight=similarity, reason=f"similarity={similarity:.2f}",
            )

    def get_node(self, node_id: str) -> Optional[dict]:
        """Get a node's data by ID."""
        if self.graph.has_node(node_id):
            return dict(self.graph.nodes[node_id])
        return None

    def get_neighbors(self, node_id: str) -> list[dict]:
        """Get all neighbors of a node with edge info."""
        if not self.graph.has_node(node_id):
            return []
        neighbors = []
        for neighbor in self.graph.neighbors(node_id):
            edge_data = self.graph.edges[node_id, neighbor]
            node_data = dict(self.graph.nodes[neighbor])
            neighbors.append({
                "node": node_data,
                "edge_type": edge_data.get("edge_type", "related"),
                "reason": edge_data.get("reason", ""),
            })
        return neighbors

    def get_contradictions(self) -> list[dict]:
        """Get all contradiction edges in the graph."""
        contradictions = []
        seen = set()
        for u, v, data in self.graph.edges(data=True):
            if data.get("edge_type") == "contradicts":
                pair = tuple(sorted([u, v]))
                if pair not in seen:
                    seen.add(pair)
                    u_data = self.graph.nodes.get(u, {})
                    v_data = self.graph.nodes.get(v, {})
                    contradictions.append({
                        "paper_a": u_data.get("title", u),
                        "paper_b": v_data.get("title", v),
                        "paper_a_id": u,
                        "paper_b_id": v,
                        "reason": data.get("reason", ""),
                        "year_a": u_data.get("year"),
                        "year_b": v_data.get("year"),
                    })
        return contradictions

    def get_stats(self) -> dict:
        """Get summary statistics of the graph."""
        edge_types = {}
        for _, _, data in self.graph.edges(data=True):
            etype = data.get("edge_type", "unknown")
            edge_types[etype] = edge_types.get(etype, 0) + 1

        return {
            "num_nodes": self.graph.number_of_nodes(),
            "num_edges": self.graph.number_of_edges(),
            "edge_types": edge_types,
            "density": nx.density(self.graph) if self.graph.number_of_nodes() > 1 else 0,
        }

    def export(self) -> dict:
        """Export the graph as nodes + edges for the frontend."""
        nodes = []
        for node_id, data in self.graph.nodes(data=True):
            nodes.append({
                "id": node_id,
                "label": data.get("label", node_id[:40]),
                "title": data.get("title", ""),
                "year": data.get("year"),
                "domain": data.get("domain", ""),
                "authors": data.get("authors", []),
                "claims": data.get("claims", []),
                "source": data.get("source", ""),
                "citation_count": data.get("citation_count", 0),
            })

        edges = []
        for u, v, data in self.graph.edges(data=True):
            edges.append({
                "source": u,
                "target": v,
                "edge_type": data.get("edge_type", "related"),
                "weight": data.get("weight", 1.0),
                "reason": data.get("reason", ""),
            })

        return {"nodes": nodes, "edges": edges}


# Global session store for knowledge graphs
_graphs: dict[str, KnowledgeGraph] = {}


def get_graph(session_id: str) -> KnowledgeGraph:
    """Get or create a knowledge graph for a session."""
    if session_id not in _graphs:
        _graphs[session_id] = KnowledgeGraph()
    return _graphs[session_id]


def delete_graph(session_id: str):
    """Delete a session's knowledge graph."""
    _graphs.pop(session_id, None)
