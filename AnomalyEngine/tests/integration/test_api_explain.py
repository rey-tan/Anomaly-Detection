import os
import json
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.api import models, database
from src.api.app import app
from src.api.database import Base
from sqlalchemy.pool import StaticPool


def override_get_db():
    # will be set in test setup
    yield None


def test_explain_endpoint_writes_artifact(monkeypatch, tmp_path):
    # setup in-memory DB
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    models.Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()

    # create a test user and patch database.get_db to use this session
    user = models.User(username="intuser", hashed_password="x", role="user")
    db.add(user)
    db.commit()
    db.refresh(user)
    user_id = user.id

    def _get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[database.get_db] = _get_db

    # override auth to return our user
    def fake_current_user():
        return user

    from src.api.app import get_current_user
    app.dependency_overrides[get_current_user] = lambda: user

    # mock AI service to return a deterministic explanation
    def fake_call_ai_explanation(request):
        return {"summary": "ok", "raw_summary": "ok", "entries": [], "anomaly_count": 1}

    import src.components.explanation_engine as ee
    monkeypatch.setattr(ee.ExplanationEngine, "explain", fake_call_ai_explanation)

    client = TestClient(app)
    payload = {
        "stock": "NABIL",
        "mode": "Static",
        "timeframe": "1D",
        "start_date": "2024-01-01",
        "end_date": "2024-01-10",
        "data": [],
    }

    resp = client.post("/analyze/explain", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body["summary"] == "ok"

    # check that DB has an explanation row
    rows = db.query(models.Explanation).filter(models.Explanation.user_id == user_id).all()
    assert len(rows) >= 1
    e = rows[0]
    assert e.artifact_hash is not None or e.artifact_path is not None
