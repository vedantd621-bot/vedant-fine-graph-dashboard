"""
FinGraph Interactive Graph Visualization Models.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from analytics.src.models import RiskLevel


class GraphNode(BaseModel):
    """Visual node representation in Neo4j subgraphs."""
    id: str = Field(..., description="Unique node ID (e.g. A005, P001, B01)")
    label: str = Field(..., description="Human-readable node label or name")
    type: str = Field(..., description="Node label/category: Account, Person, Bank")
    risk_score: Optional[float] = None
    risk_level: Optional[RiskLevel] = None
    is_frozen: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)


class GraphEdge(BaseModel):
    """Visual directed relationship edge connecting nodes."""
    id: str = Field(..., description="Unique edge/transaction identifier")
    source: str = Field(..., description="Origin node ID")
    target: str = Field(..., description="Target node ID")
    type: str = Field(..., description="Relationship type: TRANSFERRED_TO, OWNS, HOSTED_BY")
    amount: Optional[float] = None
    currency: Optional[str] = "USD"
    timestamp: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class GraphPayload(BaseModel):
    """Complete graph structure consumed by D3 / React Flow graph renderers."""
    focal_account_id: Optional[str] = None
    nodes: List[GraphNode] = Field(default_factory=list)
    edges: List[GraphEdge] = Field(default_factory=list)
    links: Optional[List[GraphEdge]] = None
    is_truncated: bool = False
    total_nodes: int = 0
    total_edges: int = 0

    def model_post_init(self, __context: Any) -> None:
        if self.links is None:
            self.links = self.edges
