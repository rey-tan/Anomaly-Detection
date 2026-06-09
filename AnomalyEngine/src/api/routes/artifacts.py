from pathlib import Path

from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import crud, database, models, schemas
from ..dependencies import get_current_user
from .analysis import convert_numpy_types, format_analyze_response
from src.utils.io import read_result_artifact

router = APIRouter(tags=["artifacts"])


@router.get("/me/analyses/{analysis_id}/data")
def get_analysis_data(
    analysis_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Get full analysis data artifact for a specific analysis."""
    analysis = db.query(models.UserAnalysis).filter(
        models.UserAnalysis.id == analysis_id
    ).first()
    
    if not analysis or analysis.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found"
        )
    
    if not analysis.data_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Data artifact not available"
        )
    
    path = Path(analysis.data_path)
    if not path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Artifact file not found"
        )

    artifact = read_result_artifact(str(path))
    if artifact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Artifact file not found"
        )
    
    artifact = convert_numpy_types(artifact)
    # Format the artifact response with params embedded in models
    return format_analyze_response(
        artifact.get("metrics", {}),
        artifact.get("data", []),
        artifact.get("best_params", {}),
    )


@router.post("/me/analyses/{analysis_id}/favorite", response_model=schemas.UserAnalysisRead)
def toggle_favorite(
    analysis_id: int,
    payload: dict = Body(...),
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Mark or unmark an analysis as favorite."""
    favorite = bool(payload.get("favorite", False))
    updated = crud.set_analysis_favorite(db, analysis_id, current_user.id, favorite)
    if updated is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found or not owned"
        )
    return updated
