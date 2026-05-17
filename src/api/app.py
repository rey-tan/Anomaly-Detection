from datetime import date, datetime
from typing import List

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import numpy as np
import pandas as pd
from fastapi.middleware.cors import CORSMiddleware

from src.pipelines.anomaly_detection_pipeline import run_pipeline
from src.pipelines.realtime_detection_pipeline import run_realtime_pipeline
from src.utils.load import load_json
from src.utils.paths import HYPERPARAMS
from . import crud, database, models, schemas, security

app = FastAPI(title="Anomaly Engine API")

origins = ["http://localhost:5173"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")


def convert_numpy_types(obj):
    """Convert numpy, pandas, and datetime types to JSON-serializable native types."""
    if isinstance(obj, (np.integer,)):
        return int(obj)
    elif isinstance(obj, (np.floating,)):
        return float(obj)
    elif isinstance(obj, (np.ndarray,)):
        return obj.tolist()
    elif isinstance(obj, (np.datetime64,)):
        return str(obj)
    elif isinstance(obj, (np.timedelta64,)):
        return str(obj)
    elif isinstance(obj, (datetime, date)):
        return obj.isoformat()
    elif isinstance(obj, (pd.Timestamp,)):
        return obj.isoformat()
    elif isinstance(obj, (pd.Timedelta,)):
        return str(obj)
    elif isinstance(obj, pd.Series):
        return convert_numpy_types(obj.tolist())
    elif isinstance(obj, pd.DataFrame):
        return convert_numpy_types(obj.to_dict(orient="records"))
    elif isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [convert_numpy_types(item) for item in obj]
    else:
        return obj


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(database.get_db)):
    payload = security.decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    username = payload.get("sub")
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = crud.get_user_by_username(db, username)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def require_role(allowed_roles: List[str]):
    def role_dependency(current_user: models.User = Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user
    return role_dependency


@app.post("/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    user = crud.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    crud.log_user_activity(db, user.id, "login", resource="/login", details={"status": "success"})
    access_token = security.create_access_token(data={"sub": user.username, "role": user.role})
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/me", response_model=schemas.UserRead)
def read_current_user(db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    return current_user


@app.post("/analyze", response_model=schemas.AnalyzeResponse)
def analyze(request: schemas.AnalyzeConfig, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    config = request.dict()
    cache_key = crud.get_config_hash(config)
    cache_entry = crud.get_cache_entry(db, cache_key)
    if cache_entry:
        crud.log_user_activity(db, current_user.id, "analysis_cache_hit", resource=config["stock"], details={"config_hash": cache_key})
        return {
            "metrics": cache_entry.metrics or {},
            "data": cache_entry.data or [],
            "best_params": cache_entry.best_params or {},
        }

    hyperparams_file = HYPERPARAMS / f"{config['stock']}.json"
    if not hyperparams_file.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Hyperparameters not found for symbol {config['stock']}"
        )

    best_params = load_json(hyperparams_file)[config["timeframe"]]

    if config["mode"] == "Static":
        results = run_pipeline(config, best_params)
    else:
        results = run_realtime_pipeline(config, best_params)

    df = results["data"].reset_index()
    if "transaction_time" in df.columns:
        df["transaction_time"] = df["transaction_time"].astype(str)

    data = df.to_dict(orient="records")
    metrics = results.get("metrics", {})

    # Convert numpy/pandas types to native JSON-serializable values
    data = convert_numpy_types(data)
    metrics = convert_numpy_types(metrics)
    best_params = convert_numpy_types(best_params)

    crud.create_cache_entry(
        db=db,
        config_hash=cache_key,
        stock=config["stock"],
        mode=config["mode"],
        timeframe=config["timeframe"],
        start_date=config["start_date"],
        end_date=config["end_date"],
        features=config["features"],
        best_params=best_params,
        metrics=metrics,
        data=data,
    )

    crud.log_user_activity(db, current_user.id, "analysis_run", resource=config["stock"], details={"config_hash": cache_key, "mode": config["mode"]})
    crud.create_user_analysis(
        db=db,
        user_id=current_user.id,
        config_hash=cache_key,
        stock=config["stock"],
        mode=config["mode"],
        timeframe=config["timeframe"],
        start_date=config["start_date"],
        end_date=config["end_date"],
        features=config["features"],
        best_params=best_params,
        metrics=metrics,
        status="success",
        duration_seconds=None,
    )
    crud.create_notification(
        db=db,
        user_id=current_user.id,
        title="Analysis complete",
        message=f"Your analysis for {config['stock']} completed successfully.",
        type="analysis",
    )

    return {"metrics": metrics, "data": data, "best_params": best_params}


@app.get("/cache/{config_hash}", response_model=schemas.AnalyzeResponse)
def get_cache(config_hash: str, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    cache_entry = crud.get_cache_entry(db, config_hash)
    if not cache_entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cache entry not found",
        )
    return {
        "metrics": cache_entry.metrics or {},
        "data": cache_entry.data or [],
        "best_params": cache_entry.best_params or {},
    }


@app.post("/cache", response_model=schemas.AnalyzeResponse)
def save_cache(request: schemas.CacheCreate, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    config = request.config.dict()
    config_hash = crud.get_config_hash(config)
    entry = crud.create_or_update_cache_entry(
        db=db,
        config_hash=config_hash,
        stock=config["stock"],
        mode=config["mode"],
        timeframe=config["timeframe"],
        start_date=config["start_date"],
        end_date=config["end_date"],
        features=config["features"],
        best_params=request.best_params,
        metrics=request.metrics,
        data=request.data,
    )
    crud.log_user_activity(db, current_user.id, "cache_save", resource=config["stock"], details={"config_hash": config_hash})
    return {
        "metrics": entry.metrics or {},
        "data": entry.data or [],
        "best_params": entry.best_params or {},
    }


@app.get("/users", response_model=List[schemas.UserRead], dependencies=[Depends(require_role(["admin"]))])
def read_users(db: Session = Depends(database.get_db)):
    return crud.get_users(db)


@app.post("/users", response_model=schemas.UserRead, dependencies=[Depends(require_role(["admin"]))])
def create_user(request: schemas.UserCreate, db: Session = Depends(database.get_db)):
    allowed_roles = {"analyst", "admin"}
    role = request.role
    if role not in allowed_roles:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Role must be analyst or admin")

    user = crud.create_user(
        db,
        username=request.username,
        password=request.password,
        role=role,
        permissions=request.permissions,
    )
    return user


@app.patch("/users/{user_id}/role", response_model=schemas.UserRead, dependencies=[Depends(require_role(["admin"]))])
def update_user_role(user_id: int, request: schemas.UserRoleUpdate, db: Session = Depends(database.get_db)):
    allowed_roles = {"analyst", "admin"}
    if request.role not in allowed_roles:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Role must be analyst or admin")

    user = crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return crud.update_user_role(db, user, request.role)


@app.delete("/users/{user_id}", dependencies=[Depends(require_role(["admin"]))])
def delete_user(user_id: int, db: Session = Depends(database.get_db)):
    user = crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    crud.delete_user(db, user)
    return {"message": "User deleted"}


@app.get("/users/{user_id}/activity", response_model=List[schemas.UserActivityRead], dependencies=[Depends(require_role(["admin"]))])
def read_user_activity(user_id: int, db: Session = Depends(database.get_db)):
    return crud.get_user_activity(db, user_id)


@app.get("/me/analyses", response_model=List[schemas.UserAnalysisRead])
def read_my_analyses(db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    return crud.get_user_analyses(db, current_user.id)


@app.get("/me/notifications", response_model=List[schemas.NotificationRead])
def read_my_notifications(db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    return crud.get_user_notifications(db, current_user.id)


@app.post("/me/notifications/{notification_id}/read", response_model=schemas.NotificationRead)
def mark_my_notification_read(notification_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    updated = crud.mark_notification_read(db, notification_id)
    if updated is None or updated.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    return updated


@app.post("/notifications", response_model=schemas.NotificationRead, dependencies=[Depends(require_role(["admin"]))])
def create_notification(request: schemas.NotificationCreate, db: Session = Depends(database.get_db)):
    return crud.create_notification(
        db=db,
        user_id=request.user_id,
        title=request.title,
        message=request.message,
        type=request.type or "info",
    )


@app.on_event("startup")
def startup_event():
    models.Base.metadata.create_all(bind=database.engine)
    db = database.SessionLocal()
    try:
        admin = crud.get_user_by_username(db, "admin")
        if admin is None:
            crud.create_user(db, "admin", "admin123", role="admin")
    finally:
        db.close()
