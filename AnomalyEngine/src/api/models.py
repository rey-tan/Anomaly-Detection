from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, JSON, String
from sqlalchemy.sql import func

from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=True)
    hashed_password = Column(String, nullable=False)
    email_verified = Column(Boolean, default=False)
    otp_code = Column(String, nullable=True)
    otp_expires_at = Column(DateTime(timezone=True), nullable=True)
    role = Column(String, nullable=False, default="user")
    permissions = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class PipelineCache(Base):
    __tablename__ = "pipeline_cache"

    id = Column(Integer, primary_key=True, index=True)
    config_hash = Column(String, unique=True, index=True, nullable=False)
    stock = Column(String, nullable=False)
    mode = Column(String, nullable=False)
    timeframe = Column(String, nullable=False)
    start_date = Column(String, nullable=False)
    end_date = Column(String, nullable=False)
    features = Column(JSON, nullable=False)
    best_params = Column(JSON, nullable=True)
    metrics = Column(JSON, nullable=True)
    data = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class UserActivity(Base):
    __tablename__ = "user_activity"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(String, nullable=False)
    resource = Column(String, nullable=True)
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class UserAnalysis(Base):
    __tablename__ = "user_analysis"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    config_hash = Column(String, nullable=False)
    stock = Column(String, nullable=False)
    mode = Column(String, nullable=False)
    timeframe = Column(String, nullable=False)
    start_date = Column(String, nullable=False)
    end_date = Column(String, nullable=False)
    features = Column(JSON, nullable=False)
    best_params = Column(JSON, nullable=True)
    metrics = Column(JSON, nullable=True)
    data_path = Column(String, nullable=True)
    is_favorite = Column(Boolean, default=False)
    status = Column(String, nullable=False, default="success")
    executed_at = Column(DateTime(timezone=True), server_default=func.now())
    duration_seconds = Column(Integer, nullable=True)


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    analysis_id = Column(Integer, ForeignKey("user_analysis.id"), nullable=True)
    title = Column(String, nullable=False)
    message = Column(String, nullable=False)
    type = Column(String, nullable=False, default="info")
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    read_at = Column(DateTime(timezone=True), nullable=True)


class Explanation(Base):
    __tablename__ = "explanations"

    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey("user_analysis.id"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    model = Column(String, nullable=True)
    model_version = Column(String, nullable=True)
    artifact_path = Column(String, nullable=True)
    artifact_hash = Column(String, nullable=True, index=True)
    summary = Column(String, nullable=True)
    highlights = Column(JSON, nullable=True)
    entries = Column(JSON, nullable=True)
    anomaly_count = Column(Integer, nullable=True)
    meta = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
