import json
from fastapi.testclient import TestClient
from src.api import app as api_app
from src.api import database, crud, security


def test_login_and_me_endpoint():
    client = TestClient(api_app.app)
    db = database.SessionLocal()
    username = "test_auth_user"
    password = "pw12345"

    # ensure user exists
    user = crud.get_user_by_username(db, username)
    if not user:
        user = crud.create_user(db, username, f"{username}@example.com", password, role="analyst")

    # attempt login via /login (OAuth2PasswordRequestForm simulated)
    resp = client.post("/login", data={"username": username, "password": password})
    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body

    token = body["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    me = client.get("/me", headers=headers)
    assert me.status_code == 200
    payload = me.json()
    assert payload["username"] == username

    protected = client.get("/me/analyses", headers=headers)
    assert protected.status_code == 200
    assert isinstance(protected.json(), list)


def test_view_analysis_history():
    client = TestClient(api_app.app)
    db = database.SessionLocal()
    username = "regular_user"
    password = "pw12345"

    user = crud.get_user_by_username(db, username)
    if not user:
        user = crud.create_user(db, username, f"{username}@example.com", password, role="analyst")

    resp = client.post("/login", data={"username": username, "password": password})
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    protected = client.get("/me/analyses", headers=headers)
    assert protected.status_code == 200
    assert isinstance(protected.json(), list)
