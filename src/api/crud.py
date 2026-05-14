import hashlib
import json

from sqlalchemy.orm import Session

from . import models
from .security import get_password_hash, verify_password


def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()


def create_user(db: Session, username: str, password: str):
    hashed_password = get_password_hash(password)
    user = models.User(username=username, hashed_password=hashed_password)
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
