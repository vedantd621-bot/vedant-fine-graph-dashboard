"""
FinGraph Graph Visualization Business Service.
Extracts bounded local subgraph neighborhoods for interactive network forensics.
"""
from datetime import datetime
from typing import Dict, List, Optional, Set

from neo4j.src.client import Neo4jClient
from analytics.src.models import RiskLevel
from analytics.src.risk_engine import ExplainableRiskEngine
from backend.app.models.graph import GraphEdge, GraphNode, GraphPayload


class GraphService:
    """Service providing bounded graph visualization payloads."""

    def __init__(self, client: Neo4jClient, risk_engine: ExplainableRiskEngine):
        self.client = client
        self.risk_engine = risk_engine

    def get_account_subgraph(
        self,
        account_id: str,
        depth: int = 2,
        max_nodes: int = 100,
        max_edges: int = 250,
    ) -> GraphPayload:
        """
        Retrieves a bounded local neighborhood subgraph centered on the focal account.
        Includes counterparties, owners, and host banks.
        """
        # Clamp depth safely between 1 and 3
        safe_depth = max(1, min(3, depth))

        # Query Account transaction neighborhood
        cypher_transfers = f"""
        MATCH path = (root:Account {{account_id: $account_id}})-[r:TRANSFERRED_TO*1..{safe_depth}]-(neighbor:Account)
        UNWIND relationships(path) AS rel
        WITH startNode(rel) AS src, endNode(rel) AS dst, rel
        RETURN DISTINCT
            src.account_id AS source,
            dst.account_id AS target,
            rel.transaction_id AS tx_id,
            rel.amount AS amount,
            coalesce(rel.currency, 'USD') AS currency,
            rel.timestamp AS timestamp
        LIMIT $max_edges
        """
        transfer_records = self.client.execute_query(
            cypher_transfers,
            {"account_id": account_id, "max_edges": max_edges},
        )

        # Collect unique account IDs
        account_ids: Set[str] = {account_id}
        edges: List[GraphEdge] = []

        for r in transfer_records:
            src_node = r.get("source") or r.get("src_id")
            dst_node = r.get("target") or r.get("dst_id")
            if not src_node or not dst_node:
                continue

            account_ids.add(src_node)
            account_ids.add(dst_node)

            ts = r.get("timestamp")
            if isinstance(ts, str):
                ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            elif hasattr(ts, "to_native"):
                ts = ts.to_native()

            edges.append(
                GraphEdge(
                    id=f"tx_{r.get('tx_id', r.get('transaction_id', 'unknown'))}",
                    source=src_node,
                    target=dst_node,
                    type="TRANSFERRED_TO",
                    amount=float(r["amount"]),
                    currency=r.get("currency", "USD"),
                    timestamp=ts,
                    metadata={"transaction_id": r.get("tx_id", r.get("transaction_id"))},
                )
            )

        # Query metadata for involved accounts (owners and banks)
        cypher_meta = """
        MATCH (a:Account)
        WHERE a.account_id IN $account_ids
        OPTIONAL MATCH (p:Person)-[owns_r:OWNS]->(a)
        OPTIONAL MATCH (a)-[host_r:HOSTED_BY]->(b:Bank)
        RETURN
            a.account_id AS account_id,
            a.account_type AS account_type,
            a.risk_score AS risk_score,
            a.risk_level AS risk_level,
            p.person_id AS owner_id,
            p.name AS owner_name,
            b.bank_id AS bank_id,
            b.name AS bank_name
        """
        meta_records = self.client.execute_query(cypher_meta, {"account_ids": list(account_ids)})

        nodes_map: Dict[str, GraphNode] = {}

        for m in meta_records:
            acc_id = m["account_id"]
            if acc_id not in nodes_map and len(nodes_map) < max_nodes:
                score = float(m.get("risk_score") or 0.0)
                lvl_str = m.get("risk_level", "LOW")
                try:
                    lvl = RiskLevel(lvl_str)
                except ValueError:
                    lvl = RiskLevel.LOW

                nodes_map[acc_id] = GraphNode(
                    id=acc_id,
                    label=f"Account {acc_id}",
                    type="Account",
                    risk_score=score,
                    risk_level=lvl,
                    metadata={
                        "account_type": m.get("account_type", "checking"),
                        "bank_name": m.get("bank_name"),
                        "owner_name": m.get("owner_name"),
                    },
                )

            # Add Owner Person node if present
            owner_id = m.get("owner_id")
            if owner_id and owner_id not in nodes_map and len(nodes_map) < max_nodes:
                nodes_map[owner_id] = GraphNode(
                    id=owner_id,
                    label=m.get("owner_name", owner_id),
                    type="Person",
                    metadata={"person_id": owner_id},
                )
                edges.append(
                    GraphEdge(
                        id=f"owns_{owner_id}_{acc_id}",
                        source=owner_id,
                        target=acc_id,
                        type="OWNS",
                    )
                )

            # Add Bank node if present
            bank_id = m.get("bank_id")
            if bank_id and bank_id not in nodes_map and len(nodes_map) < max_nodes:
                nodes_map[bank_id] = GraphNode(
                    id=bank_id,
                    label=m.get("bank_name", bank_id),
                    type="Bank",
                    metadata={"bank_id": bank_id},
                )
                edges.append(
                    GraphEdge(
                        id=f"hosted_{acc_id}_{bank_id}",
                        source=acc_id,
                        target=bank_id,
                        type="HOSTED_BY",
                    )
                )

        # Fallback if root account has no transactions
        if account_id not in nodes_map:
            nodes_map[account_id] = GraphNode(
                id=account_id,
                label=f"Account {account_id}",
                type="Account",
                risk_score=0.0,
                risk_level=RiskLevel.LOW,
            )

        nodes = list(nodes_map.values())
        is_truncated = len(transfer_records) >= max_edges or len(nodes) >= max_nodes

        return GraphPayload(
            focal_account_id=account_id,
            nodes=nodes,
            edges=edges,
            is_truncated=is_truncated,
            total_nodes=len(nodes),
            total_edges=len(edges),
        )
