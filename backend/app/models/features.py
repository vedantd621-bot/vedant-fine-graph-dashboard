"""
FinGraph ML-Ready Feature Store Models (Pydantic V2).
Provides normalized feature vectors, metadata definitions, and batch export structures.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class FeatureDefinition(BaseModel):
    """Metadata specification for a single ML feature."""
    name: str
    data_type: str  # "float", "int", "bool"
    description: str
    feature_version: str = "v1"
    source_module: str


class EntityFeatureVector(BaseModel):
    """Complete normalized feature vector for an entity."""
    entity_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    feature_version: str = "v1"
    features: Dict[str, float] = Field(default_factory=dict)

    def to_flat_dict(self) -> Dict[str, Any]:
        """Flattens feature vector for CSV export."""
        flat = {
            "entity_id": self.entity_id,
            "timestamp": self.timestamp.isoformat(),
            "feature_version": self.feature_version,
        }
        flat.update(self.features)
        return flat


class FeatureStoreExportRequest(BaseModel):
    """Request options for exporting ML features."""
    format: str = "json"  # "json" or "csv"
    entity_ids: Optional[List[str]] = None
    min_risk_score: Optional[float] = None
    feature_version: str = "v1"


class FeatureStoreExportResponse(BaseModel):
    """Response containing exported feature set metadata."""
    feature_version: str
    record_count: int
    feature_names: List[str]
    exported_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    data: Optional[List[Dict[str, Any]]] = None
    csv_content: Optional[str] = None
