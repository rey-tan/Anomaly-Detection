from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class UserCreate(BaseModel):
    username: str
    password: str


class UserRead(BaseModel):
    id: int
    username: str
    is_active: bool

    class Config:
        orm_mode = True


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
