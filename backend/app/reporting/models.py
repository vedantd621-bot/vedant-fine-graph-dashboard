"""
FinGraph Enterprise Reporting Models & Snapshot Schemas.
"""
from enum import Enum
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, Field


class ReportType(str, Enum):
    EXECUTIVE_FRAUD_REPORT = "EXECUTIVE_FRAUD_REPORT"
    FRAUD_NETWORK_REPORT = "FRAUD_NETWORK_REPORT"
    CAMPAIGN_REPORT = "CAMPAIGN_REPORT"
    INVESTIGATION_REPORT = "INVESTIGATION_REPORT"
    DETECTOR_PERFORMANCE_REPORT = "DETECTOR_PERFORMANCE_REPORT"
    OPERATIONS_REPORT = "OPERATIONS_REPORT"
    RISK_REPORT = "RISK_REPORT"
    TENANT_POSTURE_REPORT = "TENANT_POSTURE_REPORT"


class ReportFormat(str, Enum):
    JSON = "JSON"
    CSV = "CSV"


class ReportStatus(str, Enum):
    PENDING = "PENDING"
    GENERATING = "GENERATING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class ScheduleFrequency(str, Enum):
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"


class ReportFilter(BaseModel):
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    severity: Optional[str] = None
    risk_band: Optional[str] = None
    network_id: Optional[str] = None
    campaign_id: Optional[str] = None
    detector_id: Optional[str] = None
    investigator_id: Optional[str] = None


class CreateReportRequest(BaseModel):
    report_type: ReportType
    format: ReportFormat = ReportFormat.JSON
    title: Optional[str] = None
    filters: Optional[ReportFilter] = None


class ReportSnapshot(BaseModel):
    report_id: str = Field(default_factory=lambda: f"rpt_{uuid.uuid4().hex[:12]}")
    report_type: ReportType
    tenant_id: str
    title: str
    format: ReportFormat
    status: ReportStatus = ReportStatus.COMPLETED
    created_by: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    parameters: Dict[str, Any] = Field(default_factory=dict)
    data_version: str = "1.0"
    analytics_version: str = "master-enterprise"
    policy_version: Optional[str] = "v1.0"
    content_hash: Optional[str] = None  # SHA-256
    row_count: int = 0
    content: Optional[Any] = None


class CreateScheduleRequest(BaseModel):
    report_type: ReportType
    frequency: ScheduleFrequency
    title: Optional[str] = None
    filters: Optional[ReportFilter] = None
    format: ReportFormat = ReportFormat.JSON


class ReportSchedule(BaseModel):
    schedule_id: str = Field(default_factory=lambda: f"sch_{uuid.uuid4().hex[:12]}")
    report_type: ReportType
    tenant_id: str
    frequency: ScheduleFrequency
    title: str
    format: ReportFormat
    is_active: bool = True
    created_by: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_run_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None
    failure_count: int = 0
    filters: Optional[ReportFilter] = None
