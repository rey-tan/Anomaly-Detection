from sqlalchemy import Boolean, Column, DateTime, Integer, JSON, String
from sqlalchemy.sql import func

from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
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
