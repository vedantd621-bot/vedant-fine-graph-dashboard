"""
Unit tests for CaseEvidenceGraphBuilder.
"""
import pytest
from backend.app.case_intelligence.correlation import CaseCorrelationEngine
from backend.app.case_intelligence.evidence_graph import CaseEvidenceGraphBuilder
from backend.app.case_intelligence.models import (
    CaseRelationshipEdgeType,
    CaseRelationshipNodeType,
    EvidenceRelationshipType,
)
from backend.app.models.cases import (
    CasePriority,
    CaseStatus,
    EvidenceItem,
    EvidenceType,
    InvestigationCase,
)


def test_case_relationship_graph_construction():
    builder = CaseEvidenceGraphBuilder(max_nodes=30, max_edges=50)

    focal_case = InvestigationCase(
        case_id="CASE-100",
        title="Focal Syndicate Investigation",
        description="Core multi-entity case",
        priority=CasePriority.CRITICAL,
        status=CaseStatus.IN_PROGRESS,
        linked_accounts=["ACC-1", "ACC-2"],
        linked_alerts=["ALT-1"],
        evidence=[
            EvidenceItem(
                evidence_id="EVD-101",
                case_id="CASE-100",
                type=EvidenceType.GRAPH_PATH,
                source="Cypher Engine",
                related_entity="ACC-1",
                title="Circular Graph Path",
                description="4-hop circular loop",
                created_by="investigator",
            )
        ],
        created_by="admin",
    )

    related_case = InvestigationCase(
        case_id="CASE-200",
        title="Connected Mule Ring",
        description="Secondary case",
        priority=CasePriority.HIGH,
        status=CaseStatus.OPEN,
        linked_accounts=["ACC-2", "ACC-3"],
        created_by="investigator",
    )

    corr_engine = CaseCorrelationEngine()
    correlations = corr_engine.correlate_cases(focal_case, [focal_case, related_case])

    graph = builder.build_case_relationship_graph(focal_case, [related_case], correlations)

    assert graph.focal_case_id == "CASE-100"
    assert graph.total_nodes >= 4  # focal case, 2 accounts, alert, evidence, related case
    assert graph.total_edges >= 3

    # Check node types
    node_types = {n.type for n in graph.nodes}
    assert CaseRelationshipNodeType.CASE in node_types
    assert CaseRelationshipNodeType.ACCOUNT in node_types
    assert CaseRelationshipNodeType.ALERT in node_types
    assert CaseRelationshipNodeType.EVIDENCE in node_types

    # Check provenance extraction
    provenance = builder.generate_provenance_records(focal_case)
    assert len(provenance) == 1
    assert provenance[0].evidence_id == "EVD-101"
    assert provenance[0].relationship_type in (
        EvidenceRelationshipType.DERIVED_FROM,
        EvidenceRelationshipType.SUPPORTS,
    )
