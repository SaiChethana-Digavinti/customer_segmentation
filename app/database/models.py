from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    Text,
    ForeignKey,
    JSON,
    Boolean,
)

from sqlalchemy.orm import relationship

from app.database.connection import Base


# ============================================================
# CUSTOMER TABLE
# ============================================================

class Customer(Base):

    __tablename__ = "customers"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True
    )

    customer_id = Column(
        String(64),
        unique=True,
        nullable=False,
        index=True
    )

    recency = Column(
        Float,
        nullable=False,
        default=0
    )

    frequency = Column(
        Float,
        nullable=False,
        default=0
    )

    monetary = Column(
        Float,
        nullable=False,
        default=0
    )

    rfm_score = Column(
        Integer,
        nullable=True
    )

    segment = Column(
        String(64),
        nullable=True,
        index=True
    )

    priority = Column(
        String(32),
        nullable=True
    )

    campaign = Column(
        String(128),
        nullable=True
    )

    action = Column(
        Text,
        nullable=True
    )

    cluster = Column(
        Integer,
        nullable=True
    )

    clustering_method = Column(
        String(64),
        nullable=True
    )

    silhouette_score = Column(
        Float,
        nullable=True
    )

    pca1 = Column(
        Float,
        nullable=True
    )

    pca2 = Column(
        Float,
        nullable=True
    )

    # --------------------------------------------------------
    # Relationships
    # --------------------------------------------------------

    rfm = relationship(
        "RFMAnalysis",
        back_populates="customer",
        cascade="all, delete-orphan"
    )

    segmentation = relationship(
        "CustomerSegmentation",
        back_populates="customer",
        cascade="all, delete-orphan"
    )

    ai_recommendations = relationship(
        "AIRecommendation",
        back_populates="customer",
        cascade="all, delete-orphan"
    )


# ============================================================
# RFM ANALYSIS TABLE
# ============================================================

class RFMAnalysis(Base):

    __tablename__ = "rfm_analysis"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True
    )

    customer_id = Column(
        Integer,
        ForeignKey("customers.id"),
        nullable=False,
        index=True
    )

    recency = Column(
        Float,
        nullable=False,
        default=0
    )

    frequency = Column(
        Float,
        nullable=False,
        default=0
    )

    monetary = Column(
        Float,
        nullable=False,
        default=0
    )

    rfm_score = Column(
        String(20),
        nullable=True
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    # --------------------------------------------------------
    # Relationship
    # --------------------------------------------------------

    customer = relationship(
        "Customer",
        back_populates="rfm"
    )


# ============================================================
# CUSTOMER SEGMENTATION TABLE
# ============================================================

class CustomerSegmentation(Base):

    __tablename__ = "customer_segmentation"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True
    )

    customer_id = Column(
        Integer,
        ForeignKey("customers.id"),
        nullable=False,
        index=True
    )

    segment = Column(
        String(100),
        nullable=False,
        index=True
    )

    priority = Column(
        String(50),
        nullable=True
    )

    campaign = Column(
        String(150),
        nullable=True
    )

    marketing_strategy = Column(
        Text,
        nullable=True
    )

    recommended_action = Column(
        Text,
        nullable=True
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    # --------------------------------------------------------
    # Relationship
    # --------------------------------------------------------

    customer = relationship(
        "Customer",
        back_populates="segmentation"
    )


# ============================================================
# AI RECOMMENDATION TABLE
# ============================================================

class AIRecommendation(Base):

    __tablename__ = "ai_recommendations"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True
    )

    customer_id = Column(
        Integer,
        ForeignKey("customers.id"),
        nullable=False,
        index=True
    )

    message = Column(
        Text,
        nullable=True
    )

    marketing_strategy = Column(
        Text,
        nullable=True
    )

    recommended_action = Column(
        Text,
        nullable=True
    )

    model_name = Column(
        String(100),
        nullable=True
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    # --------------------------------------------------------
    # Relationship
    # --------------------------------------------------------

    customer = relationship(
        "Customer",
        back_populates="ai_recommendations"
    )


# ============================================================
# DATASET RUNS TABLE
# ============================================================

class DatasetRun(Base):

    __tablename__ = "dataset_runs"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True
    )

    filename = Column(
        String(255),
        nullable=False
    )

    row_count = Column(
        Integer,
        nullable=False
    )

    status = Column(
        String(32),
        nullable=False
    )

    best_method = Column(
        String(64),
        nullable=True
    )

    comparison = Column(
        JSON,
        nullable=True
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )


# ============================================================
# SEGMENT SNAPSHOTS TABLE
# ============================================================

class SegmentSnapshot(Base):

    __tablename__ = "segment_snapshots"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True
    )

    segment = Column(
        String(64),
        nullable=False,
        index=True
    )

    customer_count = Column(
        Integer,
        nullable=False
    )

    avg_recency = Column(
        Float,
        nullable=False
    )

    avg_frequency = Column(
        Float,
        nullable=False
    )

    avg_monetary = Column(
        Float,
        nullable=False
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )


# ============================================================
# USER TABLE (AUTHENTICATION & ROLES)
# ============================================================

class User(Base):

    __tablename__ = "users"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True
    )

    username = Column(
        String(64),
        unique=True,
        nullable=False,
        index=True
    )

    email = Column(
        String(128),
        unique=True,
        nullable=False,
        index=True
    )

    full_name = Column(
        String(128),
        nullable=False,
        default=""
    )

    hashed_password = Column(
        String(255),
        nullable=False
    )

    role = Column(
        String(32),
        nullable=False,
        default="analyst"  # "admin" or "analyst"
    )

    is_active = Column(
        Boolean,
        nullable=False,
        default=True
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    last_login = Column(
        DateTime,
        nullable=True
    )


# ============================================================
# AUDIT LOG TABLE (SYSTEM & SECURITY TRACKING)
# ============================================================

class AuditLog(Base):

    __tablename__ = "audit_logs"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True
    )

    user_id = Column(
        Integer,
        nullable=True,
        index=True
    )

    username = Column(
        String(64),
        nullable=False,
        index=True
    )

    action = Column(
        String(64),
        nullable=False,
        index=True
    )

    details = Column(
        Text,
        nullable=True
    )

    status = Column(
        String(32),
        nullable=False,
        default="SUCCESS"
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        index=True
    )


# ============================================================
# ANALYSIS HISTORY TABLE (CUSTOMER ANALYTICS & AI LOGS)
# ============================================================

class AnalysisHistory(Base):

    __tablename__ = "analysis_history"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    customer_id = Column(
        String(64),
        nullable=False,
        index=True
    )

    customer_name = Column(
        String(128),
        nullable=True,
        default=""
    )

    analysis_date = Column(
        DateTime,
        default=datetime.utcnow,
        index=True
    )

    customer_details = Column(
        JSON,
        nullable=True
    )

    segmentation_data = Column(
        JSON,
        nullable=True
    )

    predicted_segment = Column(
        String(64),
        nullable=True,
        index=True
    )

    segment_explanation = Column(
        Text,
        nullable=True
    )

    ai_recommendation = Column(
        Text,
        nullable=True
    )

    marketing_strategy = Column(
        Text,
        nullable=True
    )

    recommended_action = Column(
        Text,
        nullable=True
    )

    report_status = Column(
        String(32),
        nullable=False,
        default="COMPLETED"
    )

    report_data = Column(
        JSON,
        nullable=True
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    user = relationship(
        "User",
        backref="analysis_histories"
    )
