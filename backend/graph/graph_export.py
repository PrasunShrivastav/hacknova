"""Graph export utilities — formats for visualization and analysis."""

import json
import logging
from graph.knowledge_graph import KnowledgeGraph

logger = logging.getLogger(__name__)


def export_to_json(kg: KnowledgeGraph) -> str:
    """Export the knowledge graph to a JSON string.

    Args:
        kg: KnowledgeGraph instance.

    Returns:
        JSON string with nodes and edges arrays.
    """
    data = kg.export()
    return json.dumps(data, indent=2, default=str)


def export_to_gexf(kg: KnowledgeGraph, filepath: str):
    """Export the knowledge graph to GEXF format for Gephi.

    Args:
        kg: KnowledgeGraph instance.
        filepath: Output file path.
    """
    import networkx as nx
    try:
        nx.write_gexf(kg.graph, filepath)
        logger.info(f"Graph exported to GEXF: {filepath}")
    except Exception as e:
        logger.error(f"GEXF export failed: {e}")


def generate_summary_stats(kg: KnowledgeGraph) -> dict:
    """Generate detailed statistics about the knowledge graph.

    Returns:
        Dict with node/edge counts, most connected papers, domain distribution.
    """
    stats = kg.get_stats()

    # Find most connected papers (highest degree)
    if kg.graph.number_of_nodes() > 0:
        degree_sorted = sorted(
            kg.graph.degree(), key=lambda x: x[1], reverse=True
        )[:5]
        stats["most_connected"] = [
            {
                "id": node_id,
                "title": kg.graph.nodes[node_id].get("title", "")[:60],
                "connections": degree,
            }
            for node_id, degree in degree_sorted
        ]

        # Domain distribution
        domains: dict[str, int] = {}
        for _, data in kg.graph.nodes(data=True):
            domain = data.get("domain", "unknown") or "unknown"
            domains[domain] = domains.get(domain, 0) + 1
        stats["domain_distribution"] = domains
    else:
        stats["most_connected"] = []
        stats["domain_distribution"] = {}

    return stats
