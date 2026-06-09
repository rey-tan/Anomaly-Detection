# import os
# import tempfile
# from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker

# from src.api import models, crud
# from src.api.database import Base


# def get_test_db():
#     engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
#     TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
#     Base.metadata.create_all(bind=engine)
#     return TestingSessionLocal()


# def test_create_explanation_inserts_row(monkeypatch):
#     db = get_test_db()
#     # create a user
#     user = models.User(username="tester", hashed_password="x", role="user")
#     db.add(user)
#     db.commit()
#     db.refresh(user)

#     explanation_obj = {"summary": "test", "anomaly_count": 1}
#     entry = crud.create_explanation(db, user_id=user.id, explanation=explanation_obj, analysis_id=None, metadata={"k": "v"}, artifact_path="/tmp/x.json", artifact_hash="abc123")
#     assert entry.id is not None
#     assert entry.user_id == user.id
#     assert entry.artifact_path == "/tmp/x.json"
#     assert entry.artifact_hash == "abc123"
#     assert entry.summary == "test"
