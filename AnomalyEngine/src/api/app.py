import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from . import database, models
from .routes import auth, analysis, admin, artifacts
from .dependencies import get_current_user, require_role
from src.pipelines.analysis_engine import AnalysisEngine
from src.utils.io import write_result_artifact, write_explanation_artifact, read_result_artifact

load_dotenv()
logger = logging.getLogger(__name__)
print("MODE:", os.getenv("ENV"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown logic."""
    # startup code
    models.Base.metadata.create_all(bind=database.engine)

    db = database.SessionLocal()
    try:
        from . import crud
        admin = crud.get_user_by_username(db, "admin")
        if admin is None:
            crud.create_user(db, "admin", "admin@gmail.com", "admin123", role="admin")
    finally:
        db.close()

    yield
    # shutdown code (if needed)


app = FastAPI(title="Anomaly Engine API", lifespan=lifespan)

# CORS configuration
origins = ["http://localhost:5173"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Include routers from route modules
app.include_router(auth.router)
app.include_router(analysis.router)
app.include_router(admin.router)
app.include_router(artifacts.router)


# Public API routes (not requiring authentication)

