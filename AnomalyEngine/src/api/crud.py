import hashlib
import json
from datetime import datetime, timezone
from sqlalchemy.sql import func
from sqlalchemy import String
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from . import models
from .security import get_password_hash, verify_password


def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()


def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()


def get_user_by_id(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_users(db: Session) -> List[models.User]:
    return db.query(models.User).all()


def create_user(
    db: Session,
    username: str,
    email: str,
    password: str,
    role: str = "user",
    permissions: Optional[Dict[str, Any]] = None,
    email_verified: bool = True,
):
    hashed_password = get_password_hash(password)
    user = models.User(
        username=username,
        email=email,
        hashed_password=hashed_password,
        email_verified=email_verified,
        role=role,
        permissions=permissions,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def save_otp(db: Session, email: str, otp_code: str, expires_at: datetime):
    user = get_user_by_email(db, email)
    if not user:
        return None
    user.otp_code = otp_code
    user.otp_expires_at = expires_at
    db.commit()
    db.refresh(user)
    return user


def verify_otp(db: Session, email: str, otp_code: str) -> bool:
    user = get_user_by_email(db, email)
    if not user or not user.otp_code or not user.otp_expires_at:
        return False
    if user.otp_code != otp_code:
        return False
    if user.otp_expires_at < datetime.now(timezone.utc).replace(tzinfo=None):
        return False
    user.email_verified = True
    user.otp_code = None
    user.otp_expires_at = None
    db.commit()
    db.refresh(user)
    return True


def authenticate_user(db: Session, username: str, password: str):
    user = get_user_by_username(db, username)
    if not user:
        user = get_user_by_email(db, username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    if not user.email_verified:
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


def delete_user(db: Session, user: models.User):
    db.delete(user)
    db.commit()


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


def _serialize_activity(activity: models.UserActivity, username: Optional[str] = None, cache_entry: Optional[models.PipelineCache] = None):
    details = dict(activity.details or {}) if isinstance(activity.details, dict) else (activity.details or {})
    if cache_entry is not None and isinstance(details, dict):
        details.setdefault("stock", cache_entry.stock)
        details.setdefault("mode", cache_entry.mode)
        details.setdefault("timeframe", cache_entry.timeframe)
        details.setdefault("start_date", cache_entry.start_date)
        details.setdefault("end_date", cache_entry.end_date)
        details.setdefault("features", cache_entry.features)
        details.setdefault("rows", len(cache_entry.data or []))
    return {
        "id": activity.id,
        "user_id": activity.user_id,
        "username": username,
        "action": activity.action,
        "resource": activity.resource,
        "details": details,
        "created_at": activity.created_at,
    }


def get_user_activity(db: Session, user_id: int, limit: Optional[int] = None):
    query = (
        db.query(models.UserActivity, models.User.username)
        .join(models.User, models.User.id == models.UserActivity.user_id)
        .filter(models.UserActivity.user_id == user_id)
        .order_by(models.UserActivity.created_at.desc())
    )
    if limit is not None:
        query = query.limit(limit)
    rows = query.all()
    cache_hashes = [activity.details.get("config_hash") for activity, _ in rows if isinstance(activity.details, dict) and activity.details.get("config_hash")]
    cache_entries = {
        cache.config_hash: cache
        for cache in db.query(models.PipelineCache).filter(models.PipelineCache.config_hash.in_(cache_hashes)).all()
    }
    return [_serialize_activity(activity, username, cache_entries.get(activity.details.get("config_hash")) if isinstance(activity.details, dict) else None) for activity, username in rows]


def get_activity(db: Session, user_id: Optional[int] = None, q: Optional[str] = None, start: Optional[str] = None, end: Optional[str] = None, page: Optional[int] = None, page_size: Optional[int] = None):
    query = db.query(models.UserActivity)
    if user_id is not None:
        query = query.filter(models.UserActivity.user_id == user_id)
    if q:
        pattern = f"%{q}%"
        query = query.filter((models.UserActivity.action.ilike(pattern)) | (models.UserActivity.resource.ilike(pattern)))
    if start:
        try:
            start_dt = datetime.strptime(start, "%Y-%m-%d")
            query = query.filter(models.UserActivity.created_at >= start_dt)
        except Exception:
            pass
    if end:
        try:
            end_dt = datetime.strptime(end, "%Y-%m-%d")
            query = query.filter(models.UserActivity.created_at <= end_dt)
        except Exception:
            pass

    total = query.count()
    query = query.order_by(models.UserActivity.created_at.desc())
    if page is not None and page_size is not None:
        try:
            p = max(1, int(page))
            ps = max(1, int(page_size))
            query = query.offset((p - 1) * ps).limit(ps)
        except Exception:
            pass

    items = query.all()
    usernames = {
        user.id: user.username
        for user in db.query(models.User).filter(models.User.id.in_([activity.user_id for activity in items])).all()
    }
    cache_hashes = [activity.details.get("config_hash") for activity in items if isinstance(activity.details, dict) and activity.details.get("config_hash")]
    cache_entries = {
        cache.config_hash: cache
        for cache in db.query(models.PipelineCache).filter(models.PipelineCache.config_hash.in_(cache_hashes)).all()
    }
    return {
        "items": [
            _serialize_activity(
                activity,
                usernames.get(activity.user_id),
                cache_entries.get(activity.details.get("config_hash")) if isinstance(activity.details, dict) else None,
            )
            for activity in items
        ],
        "total": total,
    }


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
    data_path: Optional[str] = None,
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
        data_path=data_path,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def set_analysis_favorite(db: Session, analysis_id: int, user_id: int, favorite: bool):
    analysis = db.query(models.UserAnalysis).filter(models.UserAnalysis.id == analysis_id).first()
    if not analysis or analysis.user_id != user_id:
        return None
    analysis.is_favorite = favorite
    db.commit()
    db.refresh(analysis)
    return analysis


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


def create_explanation(db: Session, user_id: int, explanation: Dict[str, Any], analysis_id: Optional[int] = None, metadata: Optional[Dict[str, Any]] = None, artifact_path: Optional[str] = None, artifact_hash: Optional[str] = None):
    # Store only compact metadata and artifact reference to keep DB lightweight
    entry = models.Explanation(
        analysis_id=analysis_id,
        user_id=user_id,
        model=explanation.get("source") or explanation.get("model"),
        model_version=explanation.get("model_version"),
        artifact_path=artifact_path,
        artifact_hash=artifact_hash,
        summary=explanation.get("summary") or explanation.get("raw_summary"),
        highlights=explanation.get("highlights"),
        anomaly_count=explanation.get("anomaly_count"),
        meta=metadata,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def get_explanations_by_analysis(db: Session, analysis_id: int, limit: Optional[int] = None):
    query = db.query(models.Explanation).filter(models.Explanation.analysis_id == analysis_id).order_by(models.Explanation.created_at.desc())
    if limit is not None:
        query = query.limit(limit)
    return query.all()


def get_explanations_by_user(db: Session, user_id: int, limit: Optional[int] = None):
    query = db.query(models.Explanation).filter(models.Explanation.user_id == user_id).order_by(models.Explanation.created_at.desc())
    if limit is not None:
        query = query.limit(limit)
    return query.all()


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
