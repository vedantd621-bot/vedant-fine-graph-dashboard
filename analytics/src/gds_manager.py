"""
FinGraph Neo4j Graph Data Science (GDS) Projection & Algorithm Manager.
Handles in-memory graph projections, execution of PageRank, Louvain, and WCC algorithms,
and feature extraction for risk scoring with graceful fallback support.
"""
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Ensure project root in sys.path
root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from neo4j.src.client import Neo4jClient
from analytics.src.config import RiskScoringConfig, get_risk_scoring_config
from analytics.src.models import GraphFeatures

logger = logging.getLogger("FinGraph.GDSManager")


class GDSManager:
    """Manages GDS in-memory graph projections, algorithms, and node metric extraction."""

    def __init__(self, client: Neo4jClient, config: Optional[RiskScoringConfig] = None):
        self.client = client
        self.config = config or get_risk_scoring_config()
        self.graph_name = self.config.gds_graph_name

    def is_gds_available(self) -> bool:
        """Checks if GDS plugin procedures are installed and accessible in Neo4j."""
        try:
            records = self.client.execute_query(
                "SHOW PROCEDURES YIELD name WHERE name STARTS WITH 'gds' RETURN count(*) AS count"
            )
            if records and records[0]["count"] > 0:
                return True
            return False
        except Exception as exc:
            logger.warning(f"GDS availability check failed: {exc}")
            return False

    def projection_exists(self, graph_name: Optional[str] = None) -> bool:
        """Returns True if the in-memory projection exists in GDS catalog."""
        name = graph_name or self.graph_name
        try:
            records = self.client.execute_query(
                "CALL gds.graph.exists($graph_name) YIELD exists RETURN exists",
                {"graph_name": name},
            )
            return bool(records and records[0]["exists"])
        except Exception as exc:
            logger.debug(f"Projection exists check error: {exc}")
            return False

    def create_projection(self, graph_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Creates an analytical in-memory graph projection of Accounts and TRANSFERRED_TO edges.
        Idempotently drops any pre-existing projection with the same name first.
        """
        name = graph_name or self.graph_name
        if self.projection_exists(name):
            self.drop_projection(name)

        cypher = """
        CALL gds.graph.project(
            $graph_name,
            'Account',
            {
                TRANSFERRED_TO: {
                    type: 'TRANSFERRED_TO',
                    orientation: 'NATURAL',
                    properties: ['amount']
                }
            }
        )
        YIELD graphName, nodeCount, relationshipCount, projectMillis
        RETURN graphName, nodeCount, relationshipCount, projectMillis
        """
        records = self.client.execute_query(cypher, {"graph_name": name})
        if records:
            res = records[0]
            g_name = res.get("graphName", name)
            n_count = res.get("nodeCount", 0)
            r_count = res.get("relationshipCount", 0)
            p_millis = res.get("projectMillis", 0)
            logger.info(
                f"GDS projection '{g_name}' created: "
                f"{n_count} nodes, {r_count} relationships in {p_millis}ms"
            )
            return res
        return {}

    def drop_projection(self, graph_name: Optional[str] = None) -> bool:
        """Drops an in-memory graph projection from GDS catalog."""
        name = graph_name or self.graph_name
        try:
            records = self.client.execute_query(
                "CALL gds.graph.drop($graph_name, false) YIELD graphName RETURN graphName",
                {"graph_name": name},
            )
            return bool(records)
        except Exception as exc:
            logger.debug(f"Drop projection note: {exc}")
            return False

    def refresh_projection(self, graph_name: Optional[str] = None) -> Dict[str, Any]:
        """Refreshes the analytical projection with the latest operational graph state."""
        return self.create_projection(graph_name)

    def run_pagerank(self, graph_name: Optional[str] = None, write_back: bool = True) -> Dict[str, Any]:
        """Computes PageRank centrality to identify structurally influential transit hubs."""
        name = graph_name or self.graph_name
        cypher_mutate = """
        CALL gds.pageRank.mutate($graph_name, {
            mutateProperty: 'pagerank_score',
            dampingFactor: 0.85,
            maxIterations: 20
        })
        YIELD nodePropertiesWritten, computeMillis
        RETURN nodePropertiesWritten, computeMillis
        """
        records = self.client.execute_query(cypher_mutate, {"graph_name": name})
        res = records[0] if records else {}

        if write_back:
            self.client.execute_query(
                "CALL gds.graph.nodeProperties.write($graph_name, ['pagerank_score']) YIELD propertiesWritten RETURN propertiesWritten",
                {"graph_name": name},
            )
        return res

    def run_wcc(self, graph_name: Optional[str] = None, write_back: bool = True) -> Dict[str, Any]:
        """Computes Weakly Connected Components (WCC) to partition the network into connected subgraphs."""
        name = graph_name or self.graph_name
        cypher_mutate = """
        CALL gds.wcc.mutate($graph_name, {
            mutateProperty: 'wcc_id'
        })
        YIELD componentCount, computeMillis
        RETURN componentCount, computeMillis
        """
        records = self.client.execute_query(cypher_mutate, {"graph_name": name})
        res = records[0] if records else {}

        if write_back:
            self.client.execute_query(
                "CALL gds.graph.nodeProperties.write($graph_name, ['wcc_id']) YIELD propertiesWritten RETURN propertiesWritten",
                {"graph_name": name},
            )
        return res

    def run_louvain(self, graph_name: Optional[str] = None, write_back: bool = True) -> Dict[str, Any]:
        """Computes Louvain community modularity to identify dense, tightly clustered syndicate rings."""
        name = graph_name or self.graph_name
        cypher_mutate = """
        CALL gds.louvain.mutate($graph_name, {
            mutateProperty: 'louvain_community_id',
            relationshipWeightProperty: 'amount'
        })
        YIELD communityCount, modularity, modularities
        RETURN communityCount, modularity
        """
        records = self.client.execute_query(cypher_mutate, {"graph_name": name})
        res = records[0] if records else {}

        if write_back:
            self.client.execute_query(
                "CALL gds.graph.nodeProperties.write($graph_name, ['louvain_community_id']) YIELD propertiesWritten RETURN propertiesWritten",
                {"graph_name": name},
            )
        return res

    def run_all_algorithms(self, graph_name: Optional[str] = None) -> Dict[str, Any]:
        """Executes PageRank, WCC, and Louvain community detection sequentially."""
        name = graph_name or self.graph_name
        logger.info(f"Running GDS algorithms on projection '{name}'...")
        pr_res = self.run_pagerank(name, write_back=True)
        wcc_res = self.run_wcc(name, write_back=True)
        louv_res = self.run_louvain(name, write_back=True)

        return {
            "pagerank": pr_res,
            "wcc": wcc_res,
            "louvain": louv_res,
        }

    def extract_graph_features(self, account_ids: Optional[List[str]] = None) -> Dict[str, GraphFeatures]:
        """
        Extracts topological and GDS graph metrics for all or specified accounts.
        Includes graceful fallbacks for degrees, volume, and community sizing.
        """
        cypher = """
        MATCH (a:Account)
        WHERE ($account_ids IS NULL OR a.account_id IN $account_ids)
        OPTIONAL MATCH (a)<-[in_r:TRANSFERRED_TO]-()
        OPTIONAL MATCH (a)-[out_r:TRANSFERRED_TO]->()
        WITH a,
             count(DISTINCT in_r) AS in_degree,
             count(DISTINCT out_r) AS out_degree,
             coalesce(sum(in_r.amount), 0.0) + coalesce(sum(out_r.amount), 0.0) AS total_volume
        WITH a, in_degree, out_degree, (in_degree + out_degree) AS total_degree, total_volume
        RETURN
            a.account_id AS account_id,
            coalesce(a.pagerank_score, a.pagerank, 0.0) AS pagerank,
            a.wcc_id AS wcc_id,
            coalesce(a.louvain_community_id, a.community_id) AS louvain_community_id,
            in_degree,
            out_degree,
            total_degree,
            total_volume
        ORDER BY total_degree DESC, total_volume DESC
        """
        params = {"account_ids": account_ids if account_ids else None}
        records = self.client.execute_query(cypher, params)

        # Calculate Louvain community sizes
        community_sizes: Dict[int, int] = {}
        for rec in records:
            comm = rec.get("louvain_community_id")
            if comm is not None:
                community_sizes[comm] = community_sizes.get(comm, 0) + 1

        features_map: Dict[str, GraphFeatures] = {}
        for rec in records:
            acc_id = rec["account_id"]
            comm_id = rec.get("louvain_community_id")
            size = community_sizes.get(comm_id, 1) if comm_id is not None else 1

            feat = GraphFeatures(
                account_id=acc_id,
                pagerank=float(rec.get("pagerank", 0.0)),
                wcc_id=rec.get("wcc_id"),
                louvain_community_id=comm_id,
                in_degree=int(rec.get("in_degree", 0)),
                out_degree=int(rec.get("out_degree", 0)),
                total_degree=int(rec.get("total_degree", 0)),
                community_size=size,
                total_volume=float(rec.get("total_volume", 0.0)),
            )
            features_map[acc_id] = feat

        return features_map
