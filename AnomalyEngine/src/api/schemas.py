from datetime import datetime
from typing import Any, Dict, List, Optional, Literal

from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None


class UserCreate(BaseModel):
    username: str
    password: str
    role: Optional[str] = "analyst"
    permissions: Optional[Dict[str, Any]] = None


class UserRead(BaseModel):
    id: int
    username: str
    role: str
    permissions: Optional[Dict[str, Any]] = None
    is_active: bool
    created_at: Optional[datetime]

    class Config:
        from_attributes = True


class UserRoleUpdate(BaseModel):
    role: str


class UserPermissionsUpdate(BaseModel):
    permissions: Dict[str, Any]


class UserActivityRead(BaseModel):
    id: int
    user_id: int
    username: Optional[str] = None
    action: str
    resource: Optional[str]
    details: Optional[Dict[str, Any]]
    created_at: Optional[datetime]

    class Config:
        from_attributes = True


class UserAnalysisRead(BaseModel):
    id: int
    config_hash: str
    stock: str
    mode: str
    timeframe: str
    start_date: str
    end_date: str
    features: List[Any]
    best_params: Optional[Dict[str, Any]]
    metrics: Optional[Dict[str, Any]]
    is_favorite: Optional[bool] = False
    data_path: Optional[str] = None
    status: str
    duration_seconds: Optional[int]
    executed_at: Optional[datetime]

    class Config:
        from_attributes = True


class NotificationRead(BaseModel):
    id: int
    title: str
    message: str
    type: str
    is_read: bool
    created_at: Optional[datetime]
    read_at: Optional[datetime]

    class Config:
        from_attributes = True


class NotificationCreate(BaseModel):
    user_id: int
    title: str
    message: str
    type: Optional[str] = "info"


class AnalyzeConfig(BaseModel):
    stock: str
    start_date: str
    end_date: str
    timeframe: str
    features: List[str]
    mode: str


class ModelResult(BaseModel):
    metrics: Dict[str, Any]
    params: Dict[str, Any]


class AnalyzeResponse(BaseModel):
    data: List[Dict[str, Any]]
    models: Dict[str, ModelResult]


class AnomalyExplanationRequest(BaseModel):
    stock: Optional[str] = None
    mode: Optional[str] = None
    timeframe: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    metrics: Optional[Dict[str, Any]] = None
    best_params: Optional[Dict[str, Any]] = None
    data: List[Dict[str, Any]]


class AnomalyExplanationEntry(BaseModel):
    row_number: int
    date: Optional[str] = None
    bullets: List[str]
    summary: Optional[str] = None


class AnomalyExplanationResponse(BaseModel):
    raw_summary: Optional[str] = None
    summary: str
    highlights: List[str]
    entries: Optional[List[AnomalyExplanationEntry]] = None
    anomaly_count: int
    source: str


class ExplanationRead(BaseModel):
    id: int
    analysis_id: Optional[int] = None
    user_id: int
    model: Optional[str] = None
    model_version: Optional[str] = None
    artifact_path: Optional[str] = None
    artifact_hash: Optional[str] = None
    summary: Optional[str] = None
    highlights: Optional[List[str]] = None
    entries: Optional[List[Dict[str, Any]]] = None
    anomaly_count: Optional[int] = 0
    meta: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime]

    class Config:
        from_attributes = True


class CacheCreate(BaseModel):
    config: AnalyzeConfig
    best_params: Dict[str, Any]
    metrics: Dict[str, Any]
    data: List[Dict[str, Any]]


class AdminDataAssetRead(BaseModel):
    name: str
    source: str
    path: str
    rows: int
    columns: List[str]
    size_bytes: int
    modified_at: Optional[datetime]
    first_date: Optional[str] = None
    last_date: Optional[str] = None
    preview: Optional[List[Dict[str, Any]]] = None

    class Config:
        from_attributes = True


class AdminDataSymbolRead(BaseModel):
    name:str
    first_date: Optional[str] = None
    last_date: Optional[str] = None


class AdminScrapeRequest(BaseModel):
    source: Literal["sharesansar"] = "sharesansar"
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    max_pages: Optional[int] = None
    output_format: Literal["csv"] = "csv"


class AdminScrapeRunRead(BaseModel):
    date: str
    success: bool
    records_count: Optional[int] = None
    files: Optional[Dict[str, Any]] = None
    statistics: Optional[Dict[str, Any]] = None
    created_count: Optional[int] = None
    updated_count: Optional[int] = None
    created_symbols: Optional[List[str]] = None
    updated_symbols: Optional[List[str]] = None
    error: Optional[str] = None


class AdminScrapeResponse(BaseModel):
    source: str
    start_date: str
    end_date: str
    total_records: int
    runs: List[AdminScrapeRunRead]
