from pydantic import BaseModel, Field
from typing import List


# =========================================================
# HEALTH RESPONSE
# =========================================================

class HealthResponse(BaseModel):
    status: str
    service: str


# =========================================================
# CUSTOMER RESPONSE
# =========================================================

class CustomerResponse(BaseModel):
    customer_id: int

    segment: str

    recency: int = Field(ge=0)
    frequency: int = Field(ge=0)
    monetary: float = Field(ge=0)

    rfm_score: str
    rfm_total: int

    marketing_strategy: str
    recommended_action: str
    campaign: str
    priority: str


# =========================================================
# AI RECOMMENDATION RESPONSE
# =========================================================

class AIRecommendationResponse(BaseModel):
    customer_id: int

    segment: str
    campaign: str
    priority: str

    marketing_strategy: str
    recommended_action: str

    ai_message: str


# =========================================================
# SEGMENT SUMMARY
# =========================================================

class SegmentSummary(BaseModel):
    segment: str

    customer_count: int

    avg_recency: float
    avg_frequency: float
    avg_monetary: float

    total_revenue: float


# =========================================================
# CUSTOMER STATISTICS RESPONSE
# =========================================================

class CustomerStatisticsResponse(BaseModel):
    total_customers: int

    total_revenue: float

    average_monetary: float

    total_segments: int


# =========================================================
# CAMPAIGN SUMMARY RESPONSE
# =========================================================

class CampaignSummaryResponse(BaseModel):
    campaign: str

    customer_count: int

    total_revenue: float


# =========================================================
# PRIORITY SUMMARY RESPONSE
# =========================================================

class PrioritySummaryResponse(BaseModel):
    priority: str

    customer_count: int

    total_revenue: float


# =========================================================
# DASHBOARD OVERVIEW RESPONSE
# =========================================================

class DashboardOverviewResponse(BaseModel):

    # -----------------------------------------------------
    # KPI CARDS
    # -----------------------------------------------------

    total_customers: int

    total_revenue: float

    average_customer_value: float

    total_segments: int

    total_campaigns: int

    high_priority_customers: int

    # -----------------------------------------------------
    # SEGMENT ANALYTICS
    # -----------------------------------------------------

    segments: List[SegmentSummary] = []

    # -----------------------------------------------------
    # BACKWARD COMPATIBILITY
    # -----------------------------------------------------
    # Some frontend code may use segment_data instead
    # of segments.
    # -----------------------------------------------------

    segment_data: List[SegmentSummary] = []


# =========================================================
# AUTHENTICATION & USER SCHEMAS
# =========================================================

from typing import Optional, Any, Dict
from datetime import datetime


class UserRegister(BaseModel):
    username: str
    email: str
    full_name: str
    password: str
    role: Optional[str] = "analyst"


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class UserUpdateRole(BaseModel):
    role: str


class UserUpdateStatus(BaseModel):
    is_active: bool


class AdminUserCreate(BaseModel):
    username: str
    email: str
    full_name: str
    password: str
    role: str = "analyst"
    is_active: bool = True


# =========================================================
# AUDIT LOG & ADMIN SCHEMAS
# =========================================================

class AuditLogResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    username: str
    action: str
    details: Optional[str] = None
    status: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DatasetRunResponse(BaseModel):
    id: int
    filename: str
    row_count: int
    status: str
    best_method: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AdminStatsResponse(BaseModel):
    total_users: int
    active_users: int
    admin_users: int
    analyst_users: int
    total_customers: int
    total_dataset_runs: int
    db_status: str
    system_status: str


# =========================================================
# ANALYSIS HISTORY SCHEMAS
# =========================================================

class AnalysisHistoryItemResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    username: Optional[str] = None
    customer_id: str
    customer_name: Optional[str] = ""
    analysis_date: Optional[datetime] = None
    predicted_segment: Optional[str] = None
    ai_recommendation_snippet: Optional[str] = None
    marketing_strategy: Optional[str] = None
    recommended_action: Optional[str] = None
    report_status: str = "COMPLETED"

    class Config:
        from_attributes = True


class AnalysisHistoryDetailResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    username: Optional[str] = None
    customer_id: str
    customer_name: Optional[str] = ""
    analysis_date: Optional[datetime] = None
    customer_details: Optional[Dict[str, Any]] = None
    segmentation_data: Optional[Dict[str, Any]] = None
    predicted_segment: Optional[str] = None
    segment_explanation: Optional[str] = None
    ai_recommendation: Optional[str] = None
    marketing_strategy: Optional[str] = None
    recommended_action: Optional[str] = None
    report_status: str = "COMPLETED"
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AnalysisHistoryPaginationResponse(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int
    records: List[AnalysisHistoryItemResponse]
