import json
from pathlib import Path

from fastapi.testclient import TestClient

from src.api import app as api_app
from src.api import database, crud, security
from src.utils.io import write_result_artifact
from src.utils.paths import ARTIFACTS


def test_get_analysis_artifact(tmp_path, monkeypatch):
    # ensure ARTIFACTS is isolated
    monkeypatch.setattr("src.utils.paths.ARTIFACTS", tmp_path)

    client = TestClient(api_app.app)

    # create DB session and a test user
    db = database.SessionLocal()
    username = "test_integration_user"
    password = "testpass"
    user = crud.get_user_by_username(db, username)
    if not user:
        user = crud.create_user(db, username, password, role="analyst")

    # create a fake artifact
    data = {"metrics": {"score": 0.9}, "data": [{"x": 1}]}
    config_hash = "cfghash123"
    artifact_path = write_result_artifact(data, user.id, config_hash)

    # create a user_analysis record pointing to the artifact
    analysis = crud.create_user_analysis(
        db=db,
        user_id=user.id,
        config_hash=config_hash,
        stock="TEST",
        mode="Static",
        timeframe="1D",
        start_date="2020-01-01",
        end_date="2020-02-01",
        features=["close"],
        best_params={},
        metrics={"score": 0.9},
        data_path=artifact_path,
    )

    token = security.create_access_token({"sub": user.username, "role": user.role})
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.get(f"/me/analyses/{analysis.id}/data", headers=headers)
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("application/json")
    body = resp.content
    loaded = json.loads(body)
    assert loaded["metrics"]["score"] == 0.9
