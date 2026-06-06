from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional
from pathlib import Path
import json
import os
import math

from fastapi import Depends, FastAPI, HTTPException, status, Body
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session
import numpy as np
import pandas as pd
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from src.pipelines.anomaly_detection_pipeline import run_pipeline
import time
from src.utils.load import load_json
from src.utils.paths import HYPERPARAMS, DATA
from fastapi.responses import FileResponse
from src.utils.io import write_result_artifact, write_explanation_artifact, read_result_artifact, get_symbols
from src.utils.paths import ARTIFACTS
from src.utils.otp import generate_otp, get_otp_expiration, send_otp_email
from src.components.sharesansar_scraper import ShareSansarScraper
from . import crud, database, models, schemas, security, ai_services

load_dotenv()


from contextlib import asynccontextmanager





@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup code
    models.Base.metadata.create_all(bind=database.engine)

    db = database.SessionLocal()
    try:
        admin = crud.get_user_by_username(db, "admin")
        if admin is None:
            crud.create_user(
                db,
                "admin",
                "admin@gmail.com",
                "admin123",
                role="admin",
                email_verified=True,
            )
    finally:
        db.close()

    yield
    # shutdown code (if needed)

app = FastAPI(title="Anomaly Engine API",lifespan = lifespan)

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
        value = float(obj)
        return value if math.isfinite(value) else None
    elif isinstance(obj, float):
        return obj if math.isfinite(obj) else None
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


def format_analyze_response(metrics: Dict[str, Any], data: List[Dict[str, Any]], best_params: Dict[str, Any]) -> Dict[str, Any]:
    """Format analysis response by embedding params with their corresponding metrics."""
    models = {}
    for model_name, model_metrics in metrics.items():
        # Handle both 'zscore' and 'z_score' keys for consistency
        param_key = model_name if model_name in best_params else ('z_score' if model_name == 'zscore' else model_name)
        models[model_name] = {
            "metrics": model_metrics,
            "params": best_params.get(param_key, {}),
        }
    return {"data": data, "models": models}





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
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(database.get_db),
): 
    print(f"Login attempt for username: {form_data.username}, with password: {form_data.password}")
    
    user = crud.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = security.create_access_token(data={"sub": user.username, "role": user.role})
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/register/request", response_model=schemas.OTPRequestResponse)
def register_request(request: schemas.UserCreate, db: Session = Depends(database.get_db)):
    """Public registration request that sends an OTP to the provided email."""
    existing_user = crud.get_user_by_username(db, request.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists",
        )
    if crud.get_user_by_email(db, request.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )
    if request.role and request.role != "analyst":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only analyst role can be self-registered. Contact an admin for higher privileges.",
        )

    user = crud.create_user(
        db,
        username=request.username,
        email=request.email,
        password=request.password,
        role="analyst",
        permissions=None,
        email_verified=False,
    )
    otp_code = generate_otp()
    expires_at = get_otp_expiration()
    crud.save_otp(db, request.email, otp_code, expires_at)
    send_otp_email(request.email, otp_code)
    return {
        "message": "OTP sent to email. Verify within 10 minutes.",
        "email": request.email,
        "user_id": user.id,
    }


@app.post("/register/verify", response_model=schemas.UserRead)
def verify_registration(request: schemas.OTPVerificationRequest, db: Session = Depends(database.get_db)):
    if not crud.verify_otp(db, request.email, request.otp_code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP",
        )
    user = crud.get_user_by_email(db, request.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user


def _iter_date_range(start_date: datetime, end_date: datetime):
    current = start_date
    while current <= end_date:
        yield current.strftime("%Y-%m-%d")
        current += timedelta(days=1)


def _safe_line_count(path: Path) -> int:
    try:
        with path.open("r", encoding="utf-8", errors="ignore") as handle:
            total_lines = sum(1 for _ in handle)
        return max(total_lines - 1, 0)
    except Exception:
        return 0


def _summarize_csv_file(path: Path, preview_limit: int) -> schemas.AdminDataAssetRead:
    
    # cheap sample to discover column names
    try:
        sample = pd.read_csv(path, nrows=1)
    except Exception:
        sample = pd.DataFrame()

    cols_lower = [c.lower() for c in sample.columns] if not sample.empty else []
    date_col = None

    for candidate in ("date", "transaction_time"):
        if candidate in cols_lower:
            date_col = sample.columns[cols_lower.index(candidate)]
            break
    if date_col is None:
        for i, cl in enumerate(cols_lower):
            if 'date' in cl or 'time' in cl or 'timestamp' in cl:
                date_col = sample.columns[i]
                break

    preview = []
    if preview_limit and preview_limit > 0:
        try:
            preview = pd.read_csv(path).tail(preview_limit).to_dict(orient="records")
        except Exception:
            preview = []

    # All data files are treated as market data (no raw/floorsheet sources)
    source = "market"

    stat = path.stat()
    first_date = None
    last_date = None
    if date_col:
        try:
            dates = pd.read_csv(path, usecols=[date_col], parse_dates=[date_col])[date_col]
            if not dates.empty:
                first_date = str(pd.to_datetime(dates.min()).date())
                last_date = str(pd.to_datetime(dates.max()).date())
                print(f"[admin] summarized {path.name} -> date_col={date_col}, first_date={first_date}, last_date={last_date}")
        except Exception:
            first_date = None
            last_date = None

    columns = list(sample.columns) if not sample.empty else []

    return schemas.AdminDataAssetRead(
        name=path.name,
        source=source,
        path=str(path),
        rows=_safe_line_count(path),
        columns=columns,
        size_bytes=stat.st_size,
        modified_at=datetime.fromtimestamp(stat.st_mtime),
        first_date=first_date,
        last_date=last_date,
        preview=preview,
    )


def _list_admin_data_files() -> List[schemas.AdminDataAssetRead]:
    datasets = []
    root = DATA
    if root.exists():
        for path in sorted(root.glob("*.csv")):
            try:
                datasets.append(_summarize_csv_file(path, preview_limit=0))
            except Exception:
                continue
    return datasets


def _list_admin_data_symbols() -> List[schemas.AdminDataSymbolRead]:
    res = []
    for item in _list_admin_data_files():
        res.append(
            {
                "name": item.name.replace(".csv", ""),
                "first_date": item.first_date,
                "last_date": item.last_date,
            }
        )
    return res


def _find_admin_data_asset(symbol: str, preview_limit: int) -> Optional[schemas.AdminDataAssetRead]:
    path = DATA / f"{symbol}.csv"
  
    if path.exists():
        asset = _summarize_csv_file(path, preview_limit=preview_limit)
        if preview_limit > 0:
            asset.preview = pd.read_csv(path, nrows=preview_limit).to_dict(orient="records")
        else:
            asset.preview = []
        return asset
    return None





def _run_scrape_job(source: str, scrape_date: str, max_pages: Optional[int], output_format: str) -> Dict[str, Any]:
    """Run a scrape job. Currently only `sharesansar` is supported.

    Raises HTTPException for unsupported sources.
    """
    if source == "sharesansar":
        scraper = ShareSansarScraper()
        return scraper.scrape(scrape_date)

    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unsupported scrape source: {source}")


@app.get("/symbols", response_model=List[str])
def read_symbols():
    return get_symbols()

@app.get("/admin/data/symbols", response_model=List[schemas.AdminDataSymbolRead], dependencies=[Depends(require_role(["admin"]))])
def read_admin_data_symbols():
    res = _list_admin_data_symbols()
    print("Returning from API", res)
    return res

@app.get("/admin/data/preview/{symbol}", response_model=schemas.AdminDataAssetRead, dependencies=[Depends(require_role(["admin"]))])
def read_admin_data_preview(symbol: str, preview_limit: int = 10):
    selected = _find_admin_data_asset(symbol, preview_limit=preview_limit)
    if selected is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Data not found for {symbol}")
    return selected

@app.get("/me", response_model=schemas.UserRead)
def read_current_user(db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    return current_user


@app.post("/analyze", response_model=schemas.AnalyzeResponse)
def analyze(request: schemas.AnalyzeConfig, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    config = request.dict()
    cache_key = crud.get_config_hash(config)
    cache_entry = crud.get_cache_entry(db, cache_key)
    if cache_entry:
        crud.log_user_activity(
            db,
            current_user.id,
            "analysis_cache_hit",
            resource=config["stock"],
            details={
                "config_hash": cache_key,
                "stock": config["stock"],
                "mode": config["mode"],
                "timeframe": config["timeframe"],
                "start_date": config["start_date"],
                "end_date": config["end_date"],
                "features": config["features"],
                "cache_hit": True,
            },
        )
        return format_analyze_response(
            cache_entry.metrics or {},
            cache_entry.data or [],
            cache_entry.best_params or {},
        )

    hyperparams_file = HYPERPARAMS / f"{config['stock']}.json"
    if not hyperparams_file.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Hyperparameters not found for symbol {config['stock']}"
        )

    print(config)

    best_params = load_json(hyperparams_file)[config["timeframe"]]

    results = None
    if config["mode"] == "Static":
        start_ts = time.time()
        try:
            print(f"Starting pipeline for {config['stock']} with timeframe {config['timeframe']}", flush=True)
            results = run_pipeline(config, best_params)
        except Exception as exc:
            print(f"Pipeline raised exception: {exc}", flush=True)
            results = None
        finally:
            end_ts = time.time()
            print(f"Pipeline execution time: {end_ts - start_ts:.2f}s", flush=True)
   

    if results is None:
        crud.log_user_activity(
            db,
            current_user.id,
            "analysis_error",
            resource=config["stock"],
            details={
                "config_hash": cache_key,
                "stock": config["stock"],
                "mode": config["mode"],
                "timeframe": config["timeframe"],
                "start_date": config["start_date"],
                "end_date": config["end_date"],
                "features": config["features"],
                "cache_hit": False,
            },
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Analysis pipeline failed — check server logs for details",
        )

    df = results["data"].reset_index()
    if "date" in df.columns:
        df["date"] = df["date"].astype(str)

    data = df.to_dict(orient="records")
    metrics = results.get("metrics", {})

    # Convert numpy/pandas types to native JSON-serializable values
    data = convert_numpy_types(data)
    metrics = convert_numpy_types(metrics)
    best_params = convert_numpy_types(best_params)

    # persist full artifact to disk and record path
    artifact_payload = {"metrics": metrics, "data": data, "best_params": best_params}
    try:
        data_path = write_result_artifact(artifact_payload, current_user.id, cache_key)
    except Exception:
        data_path = None

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

    crud.log_user_activity(
        db,
        current_user.id,
        "analysis_run",
        resource=config["stock"],
        details={
            "config_hash": cache_key,
            "stock": config["stock"],
            "mode": config["mode"],
            "timeframe": config["timeframe"],
            "start_date": config["start_date"],
            "end_date": config["end_date"],
            "features": config["features"],
            "rows": len(data),
        },
    )
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
        data_path=data_path,
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

    return format_analyze_response(metrics, data, best_params)


@app.post("/analyze/explain", response_model=schemas.AnomalyExplanationResponse)
def explain_analysis(request: schemas.AnomalyExplanationRequest, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    explanation = ai_services.call_ai_explanation(request)
    try:
        artifact_payload = {
            "requested_at": datetime.utcnow().isoformat(),
            "user_id": current_user.id,
            "request": request.dict(),
            "explanation": explanation,
        }
        artifact_result = write_explanation_artifact(artifact_payload, current_user.id)
    except Exception:
        artifact_result = None

    # Persist explanation metadata to DB (store artifact hash/path, not full payload)
    try:
        artifact_path = artifact_result.get("path") if artifact_result else None
        artifact_hash = artifact_result.get("hash") if artifact_result else None
        crud.create_explanation(
            db=db,
            user_id=current_user.id,
            explanation=explanation,
            analysis_id=None,
            metadata={"request_summary": {"stock": request.stock, "mode": request.mode}},
            artifact_path=artifact_path,
            artifact_hash=artifact_hash,
        )
    except Exception:
        # don't break functionality if DB write fails
        pass

    return {
        "raw_summary": explanation.get("raw_summary", explanation.get("summary", "")),
        "summary": explanation.get("summary", ""),
        "highlights": explanation.get("highlights", []),
        "entries": explanation.get("entries", []),
        "anomaly_count": explanation.get("anomaly_count", 0),
        "source": explanation.get("source", "heuristic"),
    }


@app.get("/cache/{config_hash}", response_model=schemas.AnalyzeResponse)
def get_cache(config_hash: str, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    cache_entry = crud.get_cache_entry(db, config_hash)
    if not cache_entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cache entry not found",
        )
    return format_analyze_response(
        cache_entry.metrics or {},
        cache_entry.data or [],
        cache_entry.best_params or {},
    )


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
    return format_analyze_response(
        entry.metrics or {},
        entry.data or [],
        entry.best_params or {},
    )


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
        email=request.email,
        password=request.password,
        role=role,
        permissions=request.permissions,
        email_verified=True,
    )
    return user


@app.patch("/users/{user_id}/role", response_model=schemas.UserRead, dependencies=[Depends(require_role(["admin"]))])
def update_user_role(
    user_id: int,
    request: schemas.UserRoleUpdate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    allowed_roles = {"analyst", "admin"}
    if request.role not in allowed_roles:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Role must be analyst or admin")

    user = crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if user.id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot update your own account")
    if user.role == "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin accounts cannot be modified")
    return crud.update_user_role(db, user, request.role)


@app.delete("/users/{user_id}", dependencies=[Depends(require_role(["admin"]))])
def delete_user(
    user_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    user = crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if user.id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot delete your own account")
    if user.role == "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin accounts cannot be deleted")
    crud.delete_user(db, user)
    return {"message": "User deleted"}


@app.get("/users/{user_id}/activity", response_model=List[schemas.UserActivityRead], dependencies=[Depends(require_role(["admin"]))])
def read_user_activity(user_id: int, db: Session = Depends(database.get_db)):
    return crud.get_user_activity(db, user_id)


@app.get("/activity", dependencies=[Depends(require_role(["admin"]))])
def read_activity(q: Optional[str] = None, start: Optional[str] = None, end: Optional[str] = None, page: Optional[int] = None, page_size: Optional[int] = None, db: Session = Depends(database.get_db)):
    result = crud.get_activity(db, user_id=None, q=q, start=start, end=end, page=page, page_size=page_size)
    return {"items": result.get("items", []), "total": result.get("total", 0)}


@app.post("/admin/scrape", response_model=schemas.AdminScrapeResponse, dependencies=[Depends(require_role(["admin"]))])
def run_admin_scrape(
    request: schemas.AdminScrapeRequest,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    start_raw = request.start_date or datetime.now().strftime("%Y-%m-%d")
    end_raw = request.end_date or start_raw

    try:
        start_date = datetime.strptime(start_raw, "%Y-%m-%d")
        end_date = datetime.strptime(end_raw, "%Y-%m-%d")
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Dates must use YYYY-MM-DD") from exc

    if end_date < start_date:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="end_date must be on or after start_date")

    runs = []
    total_records = 0
    for scrape_date in _iter_date_range(start_date, end_date):
        try:
            result = _run_scrape_job(request.source, scrape_date, request.max_pages, request.output_format)
            records_count = int(result.get("records_count") or 0)
            total_records += records_count
            runs.append({"date": scrape_date, "success": bool(result.get("success", True)), **result})
        except Exception as exc:
            runs.append({"date": scrape_date, "success": False, "error": str(exc)})

    crud.log_user_activity(
        db,
        current_user.id,
        "admin_scrape",
        resource=request.source,
        details={"start_date": start_raw, "end_date": end_raw, "max_pages": request.max_pages},
    )

    return {
        "source": request.source,
        "start_date": start_raw,
        "end_date": end_raw,
        "total_records": total_records,
        "runs": runs,
    }


@app.get("/admin/data/file/{filename}", dependencies=[Depends(require_role(["admin"]))])
def admin_download_file(filename: str):
    # Only allow files under DATA
    path = DATA / filename
  
    if path.exists() and path.is_file():
        return FileResponse(path, media_type="text/csv", filename=path.name)
    
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")


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






@app.get("/me/analyses/{analysis_id}/data")
def get_analysis_data(
    analysis_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    analysis = db.query(models.UserAnalysis).filter(models.UserAnalysis.id == analysis_id).first()
    if not analysis or analysis.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found")
    if not analysis.data_path:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Data artifact not available")
    path = Path(analysis.data_path)
    if not path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artifact file not found")

    artifact = read_result_artifact(str(path))
    if artifact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artifact file not found")
    
    artifact = convert_numpy_types(artifact)
    # Format the artifact response with params embedded in models
    return format_analyze_response(
        artifact.get("metrics", {}),
        artifact.get("data", []),
        artifact.get("best_params", {}),
    )


@app.post("/me/analyses/{analysis_id}/favorite", response_model=schemas.UserAnalysisRead)
def toggle_favorite(
    analysis_id: int,
    payload: dict = Body(...),
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    favorite = bool(payload.get("favorite", False))
    updated = crud.set_analysis_favorite(db, analysis_id, current_user.id, favorite)
    if updated is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found or not owned")
    return updated
