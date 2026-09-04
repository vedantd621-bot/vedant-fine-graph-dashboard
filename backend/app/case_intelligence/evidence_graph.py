"""
FinGraph Bounded Case Relationship Graph & Evidence Provenance Tracer.
Builds interactive D3 force subgraphs uniting Cases, Alerts, Accounts,
Transactions, Networks, and Forensic Evidence with explicit link provenance.
"""
from datetime import datetime, timezone
import logging
from typing import Dict, List, Optional, Set

from backend.app.case_intelligence.models import (
    CaseCorrelation,
    CaseRelationshipEdge,
    CaseRelationshipEdgeType,
    CaseRelationshipGraph,
    CaseRelationshipNode,
    CaseRelationshipNodeType,
    EvidenceProvenance,
    EvidenceRelationshipType,
)
from backend.app.models.cases import InvestigationCase
from analytics.src.models import RiskLevel

logger = logging.getLogger("FinGraph.CaseEvidenceGraph")


class CaseEvidenceGraphBuilder:
    """Constructs bounded interactive subgraphs and tracks evidence provenance."""

    def __init__(self, max_nodes: int = 60, max_edges: int = 100):
        self.max_nodes = max_nodes
        self.max_edges = max_edges

    def build_case_relationship_graph(
        self,
        focal_case: InvestigationCase,
        related_cases: List[InvestigationCase],
        correlations: List[CaseCorrelation],
    ) -> CaseRelationshipGraph:
        """Constructs bounded nodes and edges centered on focal_case."""
        nodes: List[CaseRelationshipNode] = []
        edges: List[CaseRelationshipEdge] = []
        node_ids: Set[str] = set()

        # 1. Add focal case node
        focal_node = CaseRelationshipNode(
            id=focal_case.case_id,
            label=focal_case.title,
            type=CaseRelationshipNodeType.CASE,
            risk_score=90.0 if focal_case.priority == "CRITICAL" else 75.0,
            risk_level=RiskLevel.CRITICAL if focal_case.priority == "CRITICAL" else RiskLevel.HIGH,
            status=focal_case.status.value,
            metadata={"priority": focal_case.priority.value, "is_focal": True},
        )
        nodes.append(focal_node)
        node_ids.add(focal_case.case_id)

        # 2. Add linked accounts
        for acc in focal_case.linked_accounts[:15]:
            if acc not in node_ids and len(nodes) < self.max_nodes:
                nodes.append(
                    CaseRelationshipNode(
                        id=acc,
                        label=f"Account {acc}",
                        type=CaseRelationshipNodeType.ACCOUNT,
                        metadata={"account_id": acc},
                    )
                )
                node_ids.add(acc)
            if len(edges) < self.max_edges:
                edges.append(
                    CaseRelationshipEdge(
                        source=focal_case.case_id,
                        target=acc,
                        type=CaseRelationshipEdgeType.LINKS_TO,
                        strength=0.9,
                        confidence=1.0,
                    )
                )

        # 3. Add linked alerts
        for alt in focal_case.linked_alerts[:10]:
            if alt not in node_ids and len(nodes) < self.max_nodes:
                nodes.append(
                    CaseRelationshipNode(
                        id=alt,
                        label=f"Alert {alt}",
                        type=CaseRelationshipNodeType.ALERT,
                        metadata={"alert_id": alt},
                    )
                )
                node_ids.add(alt)
            if len(edges) < self.max_edges:
                edges.append(
                    CaseRelationshipEdge(
                        source=focal_case.case_id,
                        target=alt,
                        type=CaseRelationshipEdgeType.TRIGGERS,
                        strength=0.85,
                        confidence=1.0,
                    )
                )

        # 4. Add evidence items
        for evd in focal_case.evidence[:8]:
            evd_id = evd.evidence_id
            if evd_id not in node_ids and len(nodes) < self.max_nodes:
                nodes.append(
                    CaseRelationshipNode(
                        id=evd_id,
                        label=evd.title,
                        type=CaseRelationshipNodeType.EVIDENCE,
                        metadata={"type": evd.type.value, "hash": evd.integrity_hash},
                    )
                )
                node_ids.add(evd_id)
            if len(edges) < self.max_edges:
                edges.append(
                    CaseRelationshipEdge(
                        source=evd_id,
                        target=focal_case.case_id,
                        type=CaseRelationshipEdgeType.SUPPORTS,
                        strength=1.0,
                        confidence=0.95,
                    )
                )

        # 5. Add related correlated cases
        for rel in related_cases[:10]:
            if rel.case_id not in node_ids and len(nodes) < self.max_nodes:
                nodes.append(
                    CaseRelationshipNode(
                        id=rel.case_id,
                        label=rel.title,
                        type=CaseRelationshipNodeType.CASE,
                        status=rel.status.value,
                        metadata={"priority": rel.priority.value, "is_focal": False},
                    )
                )
                node_ids.add(rel.case_id)

        # 6. Add correlation edges
        for corr in correlations:
            if corr.case_b in node_ids and len(edges) < self.max_edges:
                edges.append(
                    CaseRelationshipEdge(
                        source=corr.case_a,
                        target=corr.case_b,
                        type=CaseRelationshipEdgeType.CORRELATED_WITH,
                        strength=corr.signal_strength,
                        confidence=corr.confidence,
                        metadata={"signal": corr.signal_type.value, "explanation": corr.explanation},
                    )
                )

        truncated = len(nodes) >= self.max_nodes or len(edges) >= self.max_edges
        return CaseRelationshipGraph(
            focal_case_id=focal_case.case_id,
            nodes=nodes,
            edges=edges,
            total_nodes=len(nodes),
            total_edges=len(edges),
            truncated=truncated,
        )

    def generate_provenance_records(
        self,
        case: InvestigationCase,
    ) -> List[EvidenceProvenance]:
        """Extracts and formats provenance links from case evidence items."""
        provenance_list: List[EvidenceProvenance] = []
        for evd in case.evidence:
            rel_type = EvidenceRelationshipType.SUPPORTS
            if "contradict" in (evd.description or "").lower() or "benign" in (evd.description or "").lower():
                rel_type = EvidenceRelationshipType.CONTRADICTS
            elif evd.type.value in ("GRAPH_PATH", "RISK_FACTOR", "DETECTOR_RESULT"):
                rel_type = EvidenceRelationshipType.DERIVED_FROM

            provenance_list.append(
                EvidenceProvenance(
                    evidence_id=evd.evidence_id,
                    source_type=evd.type.value,
                    source_id=evd.source,
                    target_type="CASE",
                    target_id=case.case_id,
                    relationship_type=rel_type,
                    derived_factor=evd.title,
                    contribution=0.85 if rel_type != EvidenceRelationshipType.CONTRADICTS else -0.5,
                )
            )
        return provenance_list
