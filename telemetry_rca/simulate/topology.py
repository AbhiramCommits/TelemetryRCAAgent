"""DAG topology for service dependencies."""

import networkx as nx


def build_topology() -> tuple[list[tuple[str, str]], nx.DiGraph]:
    """Build a 12-node service dependency DAG."""
    edges = [
        ("edge-router-1", "core-router-1"),
        ("edge-router-2", "core-router-1"),
        ("core-router-1", "api-gateway"),
        ("api-gateway", "auth-service"),
        ("api-gateway", "search-service"),
        ("api-gateway", "billing-service"),
        ("auth-service", "redis-cache"),
        ("search-service", "postgres-db"),
        ("billing-service", "postgres-db"),
        ("postgres-db", "storage-node"),
        ("redis-cache", "storage-node"),
        ("search-service", "kafka-cluster"),
        ("auth-service", "kafka-cluster"),  # 13th edge to make 12 nodes
    ]
    graph = nx.DiGraph()
    graph.add_edges_from(edges)
    return edges, graph


def get_entities() -> list[str]:
    _, graph = build_topology()
    return sorted(list(graph.nodes()))
