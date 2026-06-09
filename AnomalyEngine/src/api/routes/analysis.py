import time
import math
import logging
from datetime import datetime, date
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.pipelines.analysis_engine import AnalysisEngine
from src.components.explanation_engine import ExplanationEngine
from src.utils.load import load_json
from src.utils.paths import HYPERPARAMS
from src.utils.io import write_result_artifact, write_explanation_artifact, read_result_artifact
from .. import crud, database, models, schemas
from ..dependencies import get_current_user
from src.utils.io import get_symbols


router = APIRouter(tags=["analysis"])
logger = logging.getLogger(__name__)


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


def format_analyze_response(
    metrics: Dict[str, Any],
    data: List[Dict[str, Any]],
    best_params: Dict[str, Any],
    analysis_id: Optional[int] = None
) -> Dict[str, Any]:
    """Format analysis response by embedding params with their corresponding metrics."""
    models = {}
    for model_name, model_metrics in metrics.items():
        # Handle both 'zscore' and 'z_score' keys for consistency
        param_key = model_name if model_name in best_params else ('z_score' if model_name == 'zscore' else model_name)
        models[model_name] = {
            "metrics": model_metrics,
            "params": best_params.get(param_key, {}),
        }
    return {"data": data, "models": models, "analysis_id": analysis_id}



@router.get("/symbols")
def read_symbols(current_user: models.User = Depends(get_current_user)):
    """Get list of available stock symbols."""
    return get_symbols()

@router.post("/analyze", response_model=schemas.AnalyzeResponse)
def analyze(
    request: schemas.AnalyzeConfig,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Run anomaly analysis on stock data."""
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
                "timeframe": config["timeframe"],
                "start_date": config["start_date"],
                "end_date": config["end_date"],
                "cache_hit": True,
            },
        )
        return format_analyze_response(
            cache_entry.metrics or {},
            cache_entry.data or [],
            cache_entry.best_params or {},
            cache_entry.analysis_id
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

    start_ts = time.time()
    try:
        print(f"Starting pipeline for {config['stock']} with timeframe {config['timeframe']}", flush=True)
        engine = AnalysisEngine(config, best_params)
        analysis_result = engine.run()
        results = analysis_result.as_response()

    except KeyError as e:
        logger.error("Missing config key: %s", e)
    except ValueError as e:
        logger.error("Value error: %s", e)
    except Exception:
        logger.exception("Unexpected error running pipeline")
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
                "timeframe": config["timeframe"],
                "start_date": config["start_date"],
                "end_date": config["end_date"],
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

    

    crud.log_user_activity(
        db,
        current_user.id,
        "analysis_run",
        resource=config["stock"],
        details={
            "config_hash": cache_key,
            "stock": config["stock"],
            "timeframe": config["timeframe"],
            "start_date": config["start_date"],
            "end_date": config["end_date"],
            "rows": len(data),
        },
    )
    print("analysis completed, now persisting results to DB and cache", flush=True)
    analysis = crud.create_user_analysis(
        db=db,
        user_id=current_user.id,
        config_hash=cache_key,
        stock=config["stock"],
        timeframe=config["timeframe"],
        start_date=config["start_date"],
        end_date=config["end_date"],
        best_params=best_params,
        metrics=metrics,
        data_path=data_path,
        status="success",
        duration_seconds=None,
    )

    crud.create_cache_entry(
        db=db,
        analysis_id = analysis.id,
        config_hash=cache_key,
        stock=config["stock"],
        timeframe=config["timeframe"],
        start_date=config["start_date"],
        end_date=config["end_date"],
        best_params=best_params,
        metrics=metrics,
        data=data,
    )

    return format_analyze_response(metrics, data, best_params,analysis.id)


@router.post("/analyze/explain", response_model=schemas.AnomalyExplanationResponse)
def explain_analysis(
    request: schemas.AnomalyExplanationRequest,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Generate explanation for anomalies detected in analysis."""
    try:
        explanation_engine = ExplanationEngine(request)
        explanation = explanation_engine.explain()
        print(request.data)

    except Exception as e:
        print("Error generating explanation:", e)
    
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
            analysis_id=request.analysis_id,
            artifact_path=artifact_path,
            artifact_hash=artifact_hash,
        )

    except Exception as e:
        # don't break functionality if DB write fails
        print("Failed to save explanation metadata to DB, but returning explanation response", e)
        pass
   
    # Log user activity
    try:
        crud.log_user_activity(
            db=db,
            user_id=current_user.id,
            action="explanation_generated",
            resource=request.stock,
            details={"analysis_id": request.analysis_id},
        )
    except Exception:
        # don't break functionality if activity logging fails
        pass

    return {
        "raw_summary": explanation.get("raw_summary", explanation.get("summary", "")),
        "summary": explanation.get("summary", ""),
        "entries": explanation.get("entries", []),
        "anomaly_count": explanation.get("anomaly_count", 0),
        "source": explanation.get("source", "heuristic"),
    }


@router.get("/cache/{config_hash}", response_model=schemas.AnalyzeResponse)
def get_cache(
    config_hash: str,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Retrieve cached analysis result."""
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




@router.get("/me/analyses", response_model=List[schemas.UserAnalysisRead])
def read_my_analyses(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get list of user's analyses."""
    return crud.get_user_analyses(db, current_user.id)
