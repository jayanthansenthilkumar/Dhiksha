"""
Database models and schemas for the Learning Recommendation System.
Uses SQLAlchemy ORM with PostgreSQL.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4

from sqlalchemy import (
    ARRAY,
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()


class User(Base):
    """User table - stores learner profiles."""

    __tablename__ = "users"

    user_id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    cohort_tag = Column(Text, nullable=True)  # e.g., "premium", "free", "student"
    last_active_at = Column(DateTime(timezone=True), nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)  # Soft delete for GDPR

    # Relationships
    events = relationship("Event", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(user_id={self.user_id}, cohort={self.cohort_tag})>"


class Content(Base):
    """Content table - stores learning items (videos, articles, quizzes)."""

    __tablename__ = "contents"

    content_id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    title = Column(Text, nullable=False)
    type = Column(
        Enum("video", "article", "quiz", name="content_type_enum"),
        nullable=False,
    )
    tags = Column(ARRAY(Text), nullable=True)  # e.g., ["python", "machine-learning"]
    difficulty = Column(
        Integer,
        nullable=False,
        default=3,
    )
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Constraints
    __table_args__ = (
        CheckConstraint("difficulty BETWEEN 1 AND 5", name="difficulty_range"),
    )

    # Relationships
    events = relationship("Event", back_populates="content", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Content(content_id={self.content_id}, title='{self.title[:30]}...', type={self.type})>"


class Event(Base):
    """Event table - stores user-content interactions.
    
    Partitioned by timestamp (monthly) in production.
    """

    __tablename__ = "events"

    event_id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    content_id = Column(PG_UUID(as_uuid=True), ForeignKey("contents.content_id"), nullable=False)
    event_type = Column(
        Enum("view", "complete", "like", "quiz_score", name="event_type_enum"),
        nullable=False,
    )
    value = Column(Float, nullable=True)  # e.g., quiz score (0-100), watch time (seconds)
    ts = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    deleted = Column(Boolean, nullable=False, default=False)  # Soft delete for user opt-out

    # Indexes for query performance
    __table_args__ = (
        Index("idx_events_user_ts", "user_id", "ts"),
        Index("idx_events_content_ts", "content_id", "ts"),
        Index("idx_events_type_ts", "event_type", "ts"),
    )

    # Relationships
    user = relationship("User", back_populates="events")
    content = relationship("Content", back_populates="events")

    def __repr__(self):
        return f"<Event(event_id={self.event_id}, type={self.event_type}, user={self.user_id}, content={self.content_id})>"


# Additional tables for production features

class ModelVersion(Base):
    """Track deployed model versions for debugging."""

    __tablename__ = "model_versions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    model_name = Column(String(100), nullable=False)  # e.g., "retrieval_model"
    version = Column(String(50), nullable=False)  # e.g., "v1.2.0"
    mlflow_run_id = Column(String(100), nullable=True)
    deployed_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    deployed_by = Column(String(100), nullable=False)  # e.g., "github-actions", "alice@co.com"
    is_active = Column(Boolean, nullable=False, default=True)

    __table_args__ = (
        Index("idx_model_versions_name", "model_name", "is_active"),
    )

    def __repr__(self):
        return f"<ModelVersion(model={self.model_name}, version={self.version}, active={self.is_active})>"


class RecommendationLog(Base):
    """Log recommendations served to users (for offline evaluation and debugging)."""

    __tablename__ = "recommendation_logs"

    log_id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(PG_UUID(as_uuid=True), nullable=False)
    recommended_content_ids = Column(ARRAY(PG_UUID(as_uuid=True)), nullable=False)
    scores = Column(ARRAY(Float), nullable=True)  # Model scores for each recommendation
    model_version = Column(String(50), nullable=False)
    ts = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    latency_ms = Column(Integer, nullable=True)  # Serving latency

    __table_args__ = (
        Index("idx_recommendation_logs_user_ts", "user_id", "ts"),
        Index("idx_recommendation_logs_ts", "ts"),
    )

    def __repr__(self):
        return f"<RecommendationLog(user={self.user_id}, n_recs={len(self.recommended_content_ids)})>"


# Pydantic schemas for API validation (FastAPI)

from pydantic import BaseModel, Field, validator


class UserSchema(BaseModel):
    """Pydantic schema for User."""

    user_id: UUID
    created_at: datetime
    cohort_tag: Optional[str] = None
    last_active_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ContentSchema(BaseModel):
    """Pydantic schema for Content."""

    content_id: UUID
    title: str
    type: str  # "video", "article", "quiz"
    tags: Optional[List[str]] = None
    difficulty: int = Field(..., ge=1, le=5)
    created_at: datetime

    class Config:
        from_attributes = True


class EventCreate(BaseModel):
    """Schema for creating a new event (API POST /events)."""

    user_id: UUID
    content_id: UUID
    event_type: str  # "view", "complete", "like", "quiz_score"
    value: Optional[float] = None
    ts: Optional[datetime] = None  # If not provided, use server time

    @validator("event_type")
    def validate_event_type(cls, v):
        allowed = ["view", "complete", "like", "quiz_score"]
        if v not in allowed:
            raise ValueError(f"event_type must be one of {allowed}")
        return v


class EventSchema(BaseModel):
    """Pydantic schema for Event."""

    event_id: UUID
    user_id: UUID
    content_id: UUID
    event_type: str
    value: Optional[float] = None
    ts: datetime

    class Config:
        from_attributes = True


class RecommendationRequest(BaseModel):
    """Schema for recommendation request."""

    user_id: UUID
    k: int = Field(default=10, ge=1, le=100)  # Number of recommendations


class RecommendationItem(BaseModel):
    """Single recommendation item."""

    content_id: UUID
    score: float
    reason_tags: Optional[List[str]] = None  # e.g., ["similar_to_recent", "popular"]


class RecommendationResponse(BaseModel):
    """Schema for recommendation response."""

    user_id: UUID
    recommendations: List[RecommendationItem]
    model_version: str
    latency_ms: int
