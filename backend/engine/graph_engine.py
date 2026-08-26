"""
Forensic Transaction Network Graph Engine
"""
from typing import List, Dict, Any, Tuple, Optional
import networkx as nx
from backend.models.transaction import Transaction, GraphNode, GraphEdge, GraphData

class GraphEngine:
    def __init__(self):
        pass

    def build_graph(
        self,
        transactions: List[Transaction],
        flagged_tx_ids: Optional[set] = None,
        sanctioned_entities: Optional[set] = None,
        pep_entities: Optional[set] = None
    ) -> Tuple[nx.DiGraph, GraphData]:
        """
        Construct a NetworkX directed graph and generate Vis.js-compatible GraphData.
        """
        if flagged_tx_ids is None:
            flagged_tx_ids = set()
        if sanctioned_entities is None:
            sanctioned_entities = set()
        if pep_entities is None:
            pep_entities = set()

        G = nx.DiGraph()

        # Track node statistics
        node_stats: Dict[str, Dict[str, Any]] = {}
        edge_map: Dict[Tuple[str, str], Dict[str, Any]] = {}

        for tx in transactions:
            src = tx.source_entity
            tgt = tx.target_entity

            # Initialize node stats
            for entity, country in [(src, tx.source_country), (tgt, tx.target_country)]:
                if entity not in node_stats:
                    node_stats[entity] = {
                        "id": entity,
                        "label": entity,
                        "type": "entity",
                        "country": country,
                        "total_inflow": 0.0,
                        "total_outflow": 0.0,
                        "sanctioned": entity in sanctioned_entities,
                        "pep": entity in pep_entities,
                        "risk_level": "low"
                    }

            node_stats[src]["total_outflow"] += tx.amount
            node_stats[tgt]["total_inflow"] += tx.amount

            # Aggregate edges between same pair
            edge_key = (src, tgt)
            is_tx_flagged = tx.id in flagged_tx_ids or len(tx.risk_flags) > 0
            if edge_key not in edge_map:
                edge_map[edge_key] = {
                    "source": src,
                    "target": tgt,
                    "amount": 0.0,
                    "count": 0,
                    "transaction_ids": [],
                    "is_flagged": False
                }
            edge_map[edge_key]["amount"] += tx.amount
            edge_map[edge_key]["count"] += 1
            edge_map[edge_key]["transaction_ids"].append(tx.id)
            if is_tx_flagged:
                edge_map[edge_key]["is_flagged"] = True

            # Add to networkx
            G.add_edge(src, tgt, weight=tx.amount, tx_id=tx.id)

        # Determine node risk levels based on sanctions, flow, and degree
        for entity, stats in node_stats.items():
            if stats["sanctioned"]:
                stats["risk_level"] = "critical"
            elif stats["pep"]:
                stats["risk_level"] = "high"
            elif stats["total_inflow"] > 100000 or stats["total_outflow"] > 100000:
                stats["risk_level"] = "medium"

        # Check centrality in NetworkX
        if len(G) > 1:
            try:
                centrality = nx.betweenness_centrality(G)
                for node, score in centrality.items():
                    if score > 0.3 and node_stats[node]["risk_level"] == "low":
                        node_stats[node]["risk_level"] = "medium"
            except Exception:
                pass

        # Build GraphData models
        nodes = [GraphNode(**data) for data in node_stats.values()]
        edges = []
        for i, (key, data) in enumerate(edge_map.items()):
            label = f"${data['amount']:,.0f}" if data['count'] == 1 else f"{data['count']}x (${data['amount']:,.0f})"
            edges.append(
                GraphEdge(
                    id=f"e_{i}_{key[0]}_{key[1]}",
                    source=data["source"],
                    target=data["target"],
                    label=label,
                    amount=data["amount"],
                    currency="USD",
                    count=data["count"],
                    transaction_ids=data["transaction_ids"],
                    is_flagged=data["is_flagged"]
                )
            )

        return G, GraphData(nodes=nodes, edges=edges)

    def find_shortest_flow_path(self, G: nx.DiGraph, source: str, target: str) -> List[str]:
        """Find the shortest financial trail connecting two suspicious entities."""
        try:
            return nx.shortest_path(G, source=source, target=target)
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return []

    def get_cluster_subgraph(self, G: nx.DiGraph, entity: str, depth: int = 2) -> List[str]:
        """Extract ego subgraph around an entity of interest."""
        if entity not in G:
            return []
        nodes = {entity}
        current_layer = {entity}
        for _ in range(depth):
            next_layer = set()
            for node in current_layer:
                next_layer.update(G.successors(node))
                next_layer.update(G.predecessors(node))
            nodes.update(next_layer)
            current_layer = next_layer
        return list(nodes)
