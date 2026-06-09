import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.api.app import app
from src.api.routes.admin import _run_scrape_job
from src.api import models, database, crud, security


@pytest.fixture(scope="function")
def test_db_with_admin():
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
    admin_user = crud.create_user(
        db,
        username="admin_user",
        email="admin_user@example.com",
        password="adminpass",
        role="admin",
    )
    yield db, admin_user
    app.dependency_overrides.clear()
    db.close()


def auth_headers(user):
    token = security.create_access_token({"sub": user.username, "role": user.role})
    return {"Authorization": f"Bearer {token}"}


def test_admin_can_create_user(test_db_with_admin):
    db, admin_user = test_db_with_admin
    client = TestClient(app)
    headers = auth_headers(admin_user)

    response = client.post(
        "/admin/users",
        json={
            "username": "new_user",
            "email": "new_user@example.com",
            "password": "newpass123",
            "role": "analyst",
        },
        headers=headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["username"] == "new_user"
    assert body["email"] == "new_user@example.com"
    assert body["role"] == "analyst"
    assert crud.get_user_by_username(db, "new_user") is not None


def test_admin_can_delete_user(test_db_with_admin):
    db, admin_user = test_db_with_admin
    client = TestClient(app)
    headers = auth_headers(admin_user)

    user_to_delete = crud.create_user(
        db,
        username="delete_me",
        email="delete_me@example.com",
        password="deletepass",
        role="analyst",
    )

    response = client.delete(f"/admin/users/{user_to_delete.id}", headers=headers)

    assert response.status_code == 200
    assert crud.get_user_by_username(db, "delete_me") is None


def test_admin_cannot_delete_self(test_db_with_admin):
    db, admin_user = test_db_with_admin
    client = TestClient(app)
    headers = auth_headers(admin_user)

    response = client.delete(f"/admin/users/{admin_user.id}", headers=headers)

    assert response.status_code == 400
    assert response.json()["detail"] == "You cannot delete your own account"
    assert crud.get_user_by_username(db, "admin_user") is not None


def test_run_scrape_job_calls_share_sansar_scrape(monkeypatch):
    captured = {}

    def fake_scrape(self, scrape_date):
        captured["scrape_date"] = scrape_date
        return {"success": True, "records_count": 5}

    monkeypatch.setattr("src.api.routes.admin.ShareSansarScraper.scrape", fake_scrape)

    result = _run_scrape_job("sharesansar", "2024-01-01", max_pages=1, output_format="json")

    assert result == {"success": True, "records_count": 5}
    assert captured["scrape_date"] == "2024-01-01"
