import hashlib
import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from . import models
from .security import get_password_hash, verify_password


def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()


def get_user_by_id(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_users(db: Session) -> List[models.User]:
    return db.query(models.User).all()


def create_user(db: Session, username: str, password: str, role: str = "user", permissions: Optional[Dict[str, Any]] = None):
    hashed_password = get_password_hash(password)
    user = models.User(
        username=username,
        hashed_password=hashed_password,
        role=role,
        permissions=permissions,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, username: str, password: str):
    user = get_user_by_username(db, username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def update_user_role(db: Session, user: models.User, role: str):
    user.role = role
    db.commit()
    db.refresh(user)
    return user


def update_user_permissions(db: Session, user: models.User, permissions: Dict[str, Any]):
    user.permissions = permissions
    db.commit()
    db.refresh(user)
    return user


def log_user_activity(db: Session, user_id: int, action: str, resource: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
    entry = models.UserActivity(
        user_id=user_id,
        action=action,
        resource=resource,
        details=details,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def get_user_activity(db: Session, user_id: int, limit: Optional[int] = None):
    query = db.query(models.UserActivity).filter(models.UserActivity.user_id == user_id).order_by(models.UserActivity.created_at.desc())
    if limit is not None:
        query = query.limit(limit)
    return query.all()


def create_user_analysis(
    db: Session,
    user_id: int,
    config_hash: str,
    stock: str,
    mode: str,
    timeframe: str,
    start_date: str,
    end_date: str,
    features: List[Any],
    best_params: Optional[Dict[str, Any]],
    metrics: Optional[Dict[str, Any]],
    status: str = "success",
    duration_seconds: Optional[int] = None,
):
    entry = models.UserAnalysis(
        user_id=user_id,
        config_hash=config_hash,
        stock=stock,
        mode=mode,
        timeframe=timeframe,
        start_date=start_date,
        end_date=end_date,
        features=features,
        best_params=best_params,
        metrics=metrics,
        status=status,
        duration_seconds=duration_seconds,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def get_user_analyses(db: Session, user_id: int, limit: Optional[int] = None):
    query = db.query(models.UserAnalysis).filter(models.UserAnalysis.user_id == user_id).order_by(models.UserAnalysis.executed_at.desc())
    if limit is not None:
        query = query.limit(limit)
    return query.all()


def create_notification(
    db: Session,
    user_id: int,
    title: str,
    message: str,
    type: str = "info",
    is_read: bool = False,
):
    notification = models.Notification(
        user_id=user_id,
        title=title,
        message=message,
        type=type,
        is_read=is_read,
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification


def get_user_notifications(db: Session, user_id: int, unread_only: bool = False):
    query = db.query(models.Notification).filter(models.Notification.user_id == user_id)
    if unread_only:
        query = query.filter(models.Notification.is_read == False)
    return query.order_by(models.Notification.created_at.desc()).all()


def mark_notification_read(db: Session, notification_id: int):
    notification = db.query(models.Notification).filter(models.Notification.id == notification_id).first()
    if notification is None:
        return None
    notification.is_read = True
    notification.read_at = datetime.utcnow()
    db.commit()
    db.refresh(notification)
    return notification


def get_config_hash(config: dict) -> str:
    normalized = json.dumps(config, sort_keys=True)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def get_cache_entry(db: Session, config_hash: str):
    return db.query(models.PipelineCache).filter(models.PipelineCache.config_hash == config_hash).first()


def create_cache_entry(
    db: Session,
    config_hash: str,
    stock: str,
    mode: str,
    timeframe: str,
    start_date: str,
    end_date: str,
    features: list,
    best_params: dict,
    metrics: dict,
    data: list,
):
    entry = models.PipelineCache(
        config_hash=config_hash,
        stock=stock,
        mode=mode,
        timeframe=timeframe,
        start_date=start_date,
        end_date=end_date,
        features=features,
        best_params=best_params,
        metrics=metrics,
        data=data,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def create_or_update_cache_entry(
    db: Session,
    config_hash: str,
    stock: str,
    mode: str,
    timeframe: str,
    start_date: str,
    end_date: str,
    features: list,
    best_params: dict,
    metrics: dict,
    data: list,
):
    entry = get_cache_entry(db, config_hash)
    if entry:
        entry.best_params = best_params
        entry.metrics = metrics
        entry.data = data
        entry.stock = stock
        entry.mode = mode
        entry.timeframe = timeframe
        entry.start_date = start_date
        entry.end_date = end_date
        entry.features = features
    else:
        entry = models.PipelineCache(
            config_hash=config_hash,
            stock=stock,
            mode=mode,
            timeframe=timeframe,
            start_date=start_date,
            end_date=end_date,
            features=features,
            best_params=best_params,
            metrics=metrics,
            data=data,
        )
        db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry
