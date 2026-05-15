from datetime import date, datetime

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import numpy as np
import pandas as pd

from src.pipelines.anomaly_detection_pipeline import run_pipeline
from src.pipelines.realtime_detection_pipeline import run_realtime_pipeline
from src.utils.load import load_json
from src.utils.paths import HYPERPARAMS
from . import crud, database, models, schemas, security

app = FastAPI(title="Anomaly Engine API")

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


@app.post("/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    user = crud.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = security.create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/analyze", response_model=schemas.AnalyzeResponse)
def analyze(request: schemas.AnalyzeConfig, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    config = request.dict()
    cache_key = crud.get_config_hash(config)
    cache_entry = crud.get_cache_entry(db, cache_key)
    if cache_entry:
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
    return {
        "metrics": entry.metrics or {},
        "data": entry.data or [],
        "best_params": entry.best_params or {},
    }


@app.on_event("startup")
def startup_event():
    models.Base.metadata.create_all(bind=database.engine)
    db = database.SessionLocal()
    try:
        admin = crud.get_user_by_username(db, "admin")
        if admin is None:
            crud.create_user(db, "admin", "admin123")
    finally:
        db.close()
