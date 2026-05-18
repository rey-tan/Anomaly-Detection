from datetime import datetime
from typing import Any, Dict, List, Optional

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


class AnalyzeResponse(BaseModel):
    metrics: Dict[str, Any]
    data: List[Dict[str, Any]]
    best_params: Optional[Dict[str, Any]]


class CacheCreate(BaseModel):
    config: AnalyzeConfig
    best_params: Dict[str, Any]
    metrics: Dict[str, Any]
    data: List[Dict[str, Any]]
