from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from src.components.sharesansar_scraper import ShareSansarScraper
from src.utils.paths import DATA
from .. import crud, database, models, schemas
from ..dependencies import get_current_user, require_role

router = APIRouter(tags=["admin"], prefix="/admin")


def _iter_date_range(start_date: datetime, end_date: datetime):
    """Iterate through date range, yielding dates as YYYY-MM-DD strings."""
    current = start_date
    while current <= end_date:
        yield current.strftime("%Y-%m-%d")
        current += timedelta(days=1)


def _safe_line_count(path: Path) -> int:
    """Safely count lines in a CSV file."""
    try:
        with path.open("r", encoding="utf-8", errors="ignore") as handle:
            total_lines = sum(1 for _ in handle)
        return max(total_lines - 1, 0)
    except Exception:
        return 0


def _summarize_csv_file(path: Path, preview_limit: int) -> schemas.AdminDataAssetRead:
    """Summarize a CSV file with metadata and optional preview."""
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
    """List all data asset files."""
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
    """List all data symbols with date ranges."""
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
    """Find and return a specific data asset."""
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
    """Run a scrape job. Currently only `sharesansar` is supported."""
    if source == "sharesansar":
        scraper = ShareSansarScraper()
        return scraper.scrape(scrape_date)

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"Unsupported scrape source: {source}"
    )


# User Management Routes

@router.get("/users", response_model=List[schemas.UserRead])
def read_users(
    db: Session = Depends(database.get_db),
    _: models.User = Depends(require_role(["admin"]))
):
    """Get list of all users (admin only)."""
    return crud.get_users(db)


@router.post("/users", response_model=schemas.UserRead)
def create_user(
    request: schemas.UserCreate,
    db: Session = Depends(database.get_db),
    _: models.User = Depends(require_role(["admin"]))
):
    """Create a new user (admin only)."""
    allowed_roles = {"analyst", "admin"}
    role = request.role
    if role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role must be analyst or admin"
        )
    print("Creating user")
    user = crud.create_user(
        db,
        username=request.username,
        email=request.email,
        password=request.password,
        role=role,
        email_verified=True,
    )
    return user


@router.patch("/users/{user_id}/role", response_model=schemas.UserRead)
def update_user_role(
    user_id: int,
    request: schemas.UserRoleUpdate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_role(["admin"])),
):
    """Update user role (admin only)."""
    allowed_roles = {"analyst", "admin"}
    if request.role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role must be analyst or admin"
        )

    user = crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot update your own account"
        )
    if user.role == "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin accounts cannot be modified"
        )
    return crud.update_user_role(db, user, request.role)


@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_role(["admin"])),
):
    """Delete a user (admin only)."""
    user = crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot delete your own account"
        )
    if user.role == "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin accounts cannot be deleted"
        )
    crud.delete_user(db, user)
    return {"message": "User deleted"}


# Activity Routes

@router.get("/activity", response_model=dict)
def read_activity(
    q: Optional[str] = None,
    start: Optional[str] = None,
    end: Optional[str] = None,
    page: Optional[int] = None,
    page_size: Optional[int] = None,
    db: Session = Depends(database.get_db),
    _: models.User = Depends(require_role(["admin"]))
):
    """Get activity log (admin only)."""
    result = crud.get_activity(db, user_id=None, q=q, start=start, end=end, page=page, page_size=page_size)
    return {"items": result.get("items", []), "total": result.get("total", 0)}


@router.get("/users/{user_id}/activity", response_model=List[schemas.UserActivityRead])
def read_user_activity(
    user_id: int,
    db: Session = Depends(database.get_db),
    _: models.User = Depends(require_role(["admin"]))
):
    """Get activity log for specific user (admin only)."""
    return crud.get_user_activity(db, user_id)


# Scrape Routes

@router.post("/scrape", response_model=schemas.AdminScrapeResponse)
def run_admin_scrape(
    request: schemas.AdminScrapeRequest,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_role(["admin"])),
):
    """Run scrape job (admin only)."""
    start_raw = request.start_date or datetime.now().strftime("%Y-%m-%d")
    end_raw = request.end_date or start_raw

    try:
        start_date = datetime.strptime(start_raw, "%Y-%m-%d")
        end_date = datetime.strptime(end_raw, "%Y-%m-%d")
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Dates must use YYYY-MM-DD"
        ) from exc

    if end_date < start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="end_date must be on or after start_date"
        )

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
        details={
            "start_date": start_raw,
            "end_date": end_raw,
            "max_pages": request.max_pages
        },
    )

    return {
        "source": request.source,
        "start_date": start_raw,
        "end_date": end_raw,
        "total_records": total_records,
        "runs": runs,
    }


# Data Asset Routes

@router.get("/data/symbols", response_model=List[schemas.AdminDataSymbolRead])
def read_admin_data_symbols(
    _: models.User = Depends(require_role(["admin"]))
):
    """Get list of available data symbols (admin only)."""
    res = _list_admin_data_symbols()
    print("Returning from API", res)
    return res


@router.get("/data/preview/{symbol}", response_model=schemas.AdminDataAssetRead)
def read_admin_data_preview(
    symbol: str,
    preview_limit: int = 10,
    _: models.User = Depends(require_role(["admin"]))
):
    """Get preview of data asset (admin only)."""
    selected = _find_admin_data_asset(symbol, preview_limit=preview_limit)
    if selected is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Data not found for {symbol}"
        )
    return selected


@router.get("/data/file/{filename}")
def admin_download_file(
    filename: str,
    _: models.User = Depends(require_role(["admin"]))
):
    """Download data file (admin only)."""
    # Only allow files under DATA
    path = DATA / filename
    if path.exists() and path.is_file():
        return FileResponse(path, media_type="text/csv", filename=path.name)
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="File not found"
    )
