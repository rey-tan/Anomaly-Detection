import pandas as pd
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.api.app import app
from src.api import models, database, security


@pytest.fixture(scope="function")
def test_db_with_user():
    """Create in-memory SQLite database with a verified test user."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    models.Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def override_get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[database.get_db] = override_get_db

    db = SessionLocal()
    test_user = models.User(
        username="testanalyst",
        email="testanalyst@example.com",
        hashed_password="hashedpassword",
        email_verified=True,
        role="analyst",
    )
    db.add(test_user)
    db.commit()
    db.refresh(test_user)

    yield db, test_user
    app.dependency_overrides.clear()


def auth_headers(user):
    token = security.create_access_token({"sub": user.username, "role": user.role})
    return {"Authorization": f"Bearer {token}"}


def test_analyze_with_invalid_stock_symbol(test_db_with_user):
    """Test that analyze endpoint fails with a nonexistent stock symbol."""
    _, user = test_db_with_user
    client = TestClient(app)
    headers = auth_headers(user)

    payload = {
        "stock": "NONEXISTENT",
        "timeframe": "1D",
        "start_date": "2024-01-01",
        "end_date": "2024-01-10",
    }

    response = client.post("/analyze", json=payload, headers=headers)
    assert response.status_code == 404
    assert "Hyperparameters not found" in response.json()["detail"]



def test_analyze_with_start_date_after_end_date(test_db_with_user):
    """Test that analyze endpoint fails when start_date > end_date."""
    _, user = test_db_with_user
    client = TestClient(app)
    headers = auth_headers(user)

    payload = {
        "stock": "NABIL",
        "timeframe": "1D",
        "start_date": "2024-01-31",
        "end_date": "2024-01-01",
    }

    response = client.post("/analyze", json=payload, headers=headers)
    assert response.status_code in [400, 500]



def test_analyze_without_authentication(test_db_with_user):
    """Test that analyze endpoint requires authentication."""
    client = TestClient(app)

    payload = {
        "stock": "NABIL",
        "timeframe": "1D",
        "start_date": "2024-01-01",
        "end_date": "2024-01-10",
    }

    response = client.post("/analyze", json=payload)
    assert response.status_code == 401




def test_analyze_successful_run_returns_expected_payload(test_db_with_user, monkeypatch):
    """Test a successful analyze endpoint run returns formatted analysis payload."""
    _, user = test_db_with_user
    client = TestClient(app)
    headers = auth_headers(user)

    payload = {
        "stock": "NABIL",
        "timeframe": "1D",
        "start_date": "2024-01-01",
        "end_date": "2024-01-02",
    }

    dummy_df = pd.DataFrame({"date": ["2024-01-01"], "close": [100.0]})
    monkeypatch.setattr(
        "src.api.app.run_pipeline",
        lambda config, best_params: {"data": dummy_df, "metrics": {"dbscan": {"score": 0.5}}, "labels": {}, "best_params": {}},
    )
    monkeypatch.setattr("src.api.app.write_result_artifact", lambda payload, user_id, cache_key: "dummy_path.json.gz")

    response = client.post("/analyze", json=payload, headers=headers)
    assert response.status_code == 200

    body = response.json()
    assert isinstance(body["data"], list)
    assert "models" in body
    assert "dbscan" in body["models"]
    assert body["models"]["dbscan"]["metrics"]["score"] == 0.5
