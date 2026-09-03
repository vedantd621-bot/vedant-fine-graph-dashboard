"""
FinGraph Common API Response Envelopes & Error Models.
Ensures uniform JSON response envelopes across all REST endpoints.
"""
from typing import Any, Generic, List, Optional, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginationMeta(BaseModel):
    """Metadata describing paginated result sets."""
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    total_items: int = Field(default=0, ge=0)
    total_pages: int = Field(default=1, ge=1)
    has_next: bool = Field(default=False)
    has_prev: bool = Field(default=False)


class ApiResponse(BaseModel, Generic[T]):
    """Standard single-resource envelope."""
    data: T
    meta: Optional[dict] = None


class PaginatedResponse(BaseModel, Generic[T]):
    """Standard multi-resource paginated envelope."""
    data: List[T]
    pagination: PaginationMeta


class ApiErrorDetail(BaseModel):
    """Detailed error diagnostics."""
    code: str
    message: str
    details: Optional[Any] = None


class ApiErrorResponse(BaseModel):
    """Standard error envelope."""
    error: ApiErrorDetail
