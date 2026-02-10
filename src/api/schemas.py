"""
Pydantic Schemas - Request and response models for API endpoints.

All data validation and serialization happens through these schemas.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any

from pydantic import BaseModel, EmailStr, Field, field_validator


# ============================================
# Authentication
# ============================================
class LoginRequest(BaseModel):
    """Login request with username and password."""
    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=6)


class TokenResponse(BaseModel):
    """JWT token response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(..., description="Access token expiry in seconds")


class RefreshTokenRequest(BaseModel):
    """Refresh token request."""
    refresh_token: str


# ============================================
# Users
# ============================================
class UserCreate(BaseModel):
    """Create new user request."""
    username: str = Field(..., min_length=3, max_length=100)
    email: Optional[EmailStr] = None
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=1, max_length=255)
    role: str = Field(default="officer", pattern="^(officer|supervisor|admin)$")
    rank: Optional[str] = None
    badge_number: Optional[str] = None
    police_station: Optional[str] = None
    district: Optional[str] = None
    phone: Optional[str] = None


class UserResponse(BaseModel):
    """User response (safe, no password)."""
    id: str
    username: str
    email: Optional[str]
    full_name: str
    role: str
    rank: Optional[str]
    badge_number: Optional[str]
    police_station: Optional[str]
    district: Optional[str]
    phone: Optional[str]
    is_active: bool
    last_login: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================
# SOP Assistant
# ============================================
class SOPRequest(BaseModel):
    """Request for SOP investigation guidance."""
    fir_details: str = Field(..., min_length=10, description="FIR details or case description")
    case_category: Optional[str] = Field(None, description="e.g., 'theft', 'murder', 'assault'")
    district: Optional[str] = None
    sections_cited: Optional[List[str]] = None
    top_k: int = Field(default=5, ge=1, le=20, description="Number of similar cases to retrieve")


class Citation(BaseModel):
    """Source citation."""
    source: str = Field(..., description="Document title or case name")
    doc_type: Optional[str] = None
    court: Optional[str] = None
    score: float = Field(..., ge=0.0, le=1.0, description="Relevance score")


class InvestigationStep(BaseModel):
    """Single investigation step."""
    priority: str = Field(..., pattern="^(critical|important|recommended)$")
    step_number: int
    action: str
    rationale: Optional[str] = None
    source: Optional[str] = None


class SOPResponse(BaseModel):
    """SOP investigation guidance response."""
    query: str
    response: str = Field(..., description="Full AI-generated guidance")
    citations: List[Citation]
    num_results: int
    processing_time_ms: Optional[int] = None


# ============================================
# Chargesheet Review
# ============================================
class ChargesheetReviewRequest(BaseModel):
    """Request to review chargesheet for completeness."""
    chargesheet_text: Optional[str] = Field(None, min_length=50)
    chargesheet_url: Optional[str] = None
    case_number: Optional[str] = None
    sections_charged: Optional[List[str]] = None
    top_k: int = Field(default=5, ge=1, le=20)


class ChargesheetIssue(BaseModel):
    """Issue found in chargesheet."""
    severity: str = Field(..., pattern="^(critical|moderate|minor)$")
    category: str
    description: str
    recommendation: Optional[str] = None


class ChargesheetReviewResponse(BaseModel):
    """Chargesheet review result."""
    query: str
    completeness_score: float = Field(..., ge=0.0, le=100.0, description="Score out of 100")
    response: str
    missing_elements: List[str] = Field(default_factory=list)
    weak_points: List[str] = Field(default_factory=list)
    strengths: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    citations: List[Citation]
    processing_time_ms: Optional[int] = None


# ============================================
# Search
# ============================================
class SearchRequest(BaseModel):
    """Natural language search request."""
    query: str = Field(..., min_length=3, description="Search query")
    filters: Optional[Dict[str, Any]] = Field(default_factory=dict)
    collection: str = Field(default="all_documents", pattern="^(all_documents|court_rulings|bare_acts)$")
    top_k: int = Field(default=10, ge=1, le=50)


class SearchResultItem(BaseModel):
    """Single search result."""
    id: str
    title: str
    snippet: str = Field(..., max_length=500)
    document_type: str
    source: str
    court: Optional[str]
    date_published: Optional[str]
    sections_cited: List[str] = Field(default_factory=list)
    score: float = Field(..., ge=0.0, le=1.0)
    url: Optional[str] = None


class SearchResponse(BaseModel):
    """Search results."""
    query: str
    results: List[SearchResultItem]
    total_results: int
    processing_time_ms: Optional[int] = None
    filters_applied: Dict[str, Any] = Field(default_factory=dict)


class SimilarCasesRequest(BaseModel):
    """Find similar cases by document ID."""
    document_id: str
    top_k: int = Field(default=10, ge=1, le=50)


# ============================================
# Documents
# ============================================
class DocumentUploadRequest(BaseModel):
    """Document upload metadata."""
    document_type: str = Field(..., pattern="^(fir|chargesheet|court_ruling|panchnama|investigation_report|other)$")
    title: str = Field(..., min_length=1, max_length=500)
    case_number: Optional[str] = None
    police_station: Optional[str] = None
    district: Optional[str] = None
    date_published: Optional[str] = None  # ISO date string
    language: str = Field(default="en", pattern="^(en|hi|gu)$")


class DocumentUploadResponse(BaseModel):
    """Document upload result."""
    id: str
    document_type: str
    title: str
    status: str = Field(..., description="processing status")
    message: str
    processing_job_id: Optional[str] = None


class DocumentResponse(BaseModel):
    """Document details."""
    id: str
    document_type: str
    source: str
    title: str
    language: str
    case_number: Optional[str]
    court: Optional[str]
    district: Optional[str]
    date_published: Optional[str]
    processing_status: str
    ocr_confidence: Optional[float]
    sections_cited: List[str] = Field(default_factory=list)
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    """Paginated document list."""
    documents: List[DocumentResponse]
    total: int
    page: int
    page_size: int
    pages: int


# ============================================
# Section Conversion
# ============================================
class SectionConvertRequest(BaseModel):
    """Convert section between IPC/BNS or CrPC/BNSS."""
    section: str = Field(..., description="Section number (e.g., '302', '376')")
    from_code: str = Field(..., pattern="^(IPC|BNS|CrPC|BNSS|IEA|BSA)$")
    to_code: str = Field(..., pattern="^(IPC|BNS|CrPC|BNSS|IEA|BSA)$")


class SectionMapping(BaseModel):
    """Section mapping result."""
    old_code: str
    old_section: str
    old_title: Optional[str]
    new_code: str
    new_section: Optional[str]
    new_title: Optional[str]
    description: Optional[str]
    is_decriminalized: bool = False


class SectionConvertResponse(BaseModel):
    """Section conversion response."""
    query: str
    mapping: Optional[SectionMapping]
    message: str


# ============================================
# Admin
# ============================================
class SystemHealthResponse(BaseModel):
    """System health check."""
    status: str = Field(..., pattern="^(healthy|degraded|unhealthy)$")
    timestamp: datetime
    services: Dict[str, Dict[str, Any]]
    version: str


class AuditLogEntry(BaseModel):
    """Audit log entry."""
    id: int
    timestamp: datetime
    username: Optional[str]
    action: str
    resource_type: Optional[str]
    resource_id: Optional[str]
    details: Dict[str, Any] = Field(default_factory=dict)
    ip_address: Optional[str]
    response_status: Optional[int]


class AuditLogResponse(BaseModel):
    """Audit log query response."""
    entries: List[AuditLogEntry]
    total: int
    page: int
    page_size: int


class FiltersResponse(BaseModel):
    """Available search filters."""
    document_types: List[str]
    sources: List[str]
    courts: List[str]
    districts: List[str]
    years: List[int]


# ============================================
# Generic Responses
# ============================================
class MessageResponse(BaseModel):
    """Generic message response."""
    message: str
    detail: Optional[str] = None


class ErrorResponse(BaseModel):
    """Error response."""
    error: str
    detail: Optional[str] = None
    status_code: int
