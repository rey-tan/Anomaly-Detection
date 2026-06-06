# Implementation Details and Developer Guide

This file documents the exact implementation details required to support explanation artifacts: API contracts, DB schema, artifact storage, migration steps, tests, and operational concerns. Use this as the canonical implementation section for the project report and handoff notes.

## Overview

- Backend: FastAPI app at `src/api/app.py`.
- ORM: SQLAlchemy declarative models in `src/api/models.py` and CRUD helpers in `src/api/crud.py`.
- Artifact I/O: `src/utils/io.py` contains `write_explanation_artifact` and related helpers.
- Frontend: Streamlit (`main.py`) for internal demos and React UI in `AnomalyUI` for production UI.
- Storage: Explanation JSON artifacts are stored under `artifacts/explanations/{user_id}/` on local disk (development) and referenced in the DB by path + hash.

## DB Schema (explanations table)

Model: `src/api/models.py::Explanation` (SQLAlchemy declarative)

- `id` Integer, primary key
- `analysis_id` Integer, foreign key -> `user_analysis.id`, nullable
- `user_id` Integer, foreign key -> `users.id`
- `artifact_path` String, filesystem path (relative to project root)
- `artifact_hash` String(64), SHA256 hex digest, indexed
- `model` String (optional) — which LLM/model generated the explanation
- `model_version` String (optional)
- `summary` Text — short one-line summary for UI lists
- `highlights` JSON — small extracted highlights (list)
- `entries` JSON — small structured entries (optional; already compact)
- `anomaly_count` Integer
- `meta` JSON — minimal request/response metadata (do not include full raw explanation)
- `created_at` DateTime (UTC)

Design note: the DB stores only compact metadata and a pointer (`artifact_path`) to the full JSON file on disk. This keeps the DB fast and easy to migrate.

## Artifact storage contract

- Directory: `artifacts/explanations/{user_id}/`
- Filename pattern: `explanation_{uuid4().hex}.json` (no timestamps in filename)
- File format: UTF-8 JSON, stable dump using `json.dumps(obj, separators=(",",":"), sort_keys=True)` to ensure deterministic ordering for hashing.
- Hash: SHA256 of the stable JSON bytes (hex digest) used as `artifact_hash`.

Example `write_explanation_artifact` (pseudocode):

```python
import json, hashlib, uuid, os

def write_explanation_artifact(user_id: int, explanation_obj: dict) -> dict:
      # normalize/remove volatile fields if deduplication is desired
      stable = json.dumps(explanation_obj, sort_keys=True, separators=(",",":"), ensure_ascii=False)
      digest = hashlib.sha256(stable.encode("utf-8")).hexdigest()
      dirname = os.path.join("artifacts", "explanations", str(user_id))
      os.makedirs(dirname, exist_ok=True)
      fname = f"explanation_{uuid.uuid4().hex}.json"
      path = os.path.join(dirname, fname)
      with open(path, "w", encoding="utf-8") as f:
            f.write(stable)
      return {"path": path, "hash": digest}
```

Security note: artifact files are stored on local disk; when serving them via API, always authorize the requesting user and ensure they own the artifact or have permission.

## API Contract (recommended endpoints)

1) POST /analyze/explain
- Purpose: request an explanation; same as current implementation.
- Request body: `AnomalyExplanationRequest` (see `src/api/schemas.py`) including `stock`, `timeframe`, `start_date`, `end_date`, `data`, etc.
- Behaviour: backend calls AI service, obtains structured explanation, calls `write_explanation_artifact`, then `crud.create_explanation` storing `artifact_path`, `artifact_hash`, `summary`, `highlights`, `anomaly_count`, `meta`.
- Response: `AnomalyExplanationResponse` including compact fields and the `explanation_id` (DB id) and summary metadata. Do NOT return raw artifact content unless explicitly requested.

2) GET /me/explanations[?page=&limit=&after=]
- Purpose: list explanation history for authenticated user (UI history view).
- Response fields (per item): `id`, `artifact_hash`, `summary`, `highlights`, `anomaly_count`, `model`, `model_version`, `created_at`, `analysis_id`.
- Pagination: limit + offset or cursor-based `after` (ISO timestamp or id).

3) GET /explanations/{id}
- Purpose: return detail metadata for explanation id (authorized).
- Response: same fields as history item plus `meta` and `entries` (if small). Do NOT return the full raw explanation unless requested.

4) GET /explanations/{id}/artifact
- Purpose: returns the full artifact JSON file (read from `artifact_path`) — only for authorized users.
- Response: `application/json` stream of the artifact file.

Auth rules: All endpoints require authentication. For `GET /explanations/{id}` and `/artifact`, verify current user is the owner or an admin.

## CRUD behaviour (implementation notes)

- `create_explanation(db, user_id, explanation_obj, analysis_id=None, meta=None)`:
   - write artifact using `write_explanation_artifact`
   - assemble `summary`, `highlights`, `anomaly_count` from parsed explanation
   - insert `Explanation` row with `artifact_path`, `artifact_hash`, `meta`
   - return created DB instance

- `get_explanations_by_user(db, user_id, limit, offset)` returns paginated metadata only.

## Migration guidance

Option A — Development (quick): remove dev sqlite DB and let `Base.metadata.create_all(bind=engine)` recreate schema.

Option B — Production (recommended): use Alembic migrations. Example alembic revision skeleton:

```bash
alembic revision -m "create explanations table" --autogenerate
alembic upgrade head
```

Migration notes:
- If your dev environment uses a local SQLite DB and you can accept dropping it, the simplest path is to remove `anomaly_engine.db` and let `Base.metadata.create_all(bind=engine)` recreate schemas during startup.

## Tests (unit / integration)

Add tests under `tests/unit/` and `tests/integration/`.

Example unit test for `write_explanation_artifact`:

```python
def test_write_explanation_artifact(tmp_path):
      obj = {"a": 1, "b": [2,3]}
      res = write_explanation_artifact(user_id=1, explanation_obj=obj)
      assert os.path.exists(res['path'])
      assert len(res['hash']) == 64
```

Integration test for endpoints using FastAPI `TestClient`:

```bash
pytest -q
```

## Retention & cleanup

Provide a small maintenance script `scripts/cleanup_explanations.py`:

```python
from datetime import datetime, timedelta
import os
from src.api import crud, database

def cleanup(days=90):
      cutoff = datetime.utcnow() - timedelta(days=days)
      db = database.SessionLocal()
      old = crud.get_explanations_older_than(db, cutoff)
      for e in old:
            try:
                  os.remove(e.artifact_path)
            except FileNotFoundError:
                  pass
            db.delete(e)
      db.commit()

if __name__ == '__main__':
      cleanup(90)
```

Schedule in production via cron or systemd timer, or run on deployment lifecycle hooks.

## Frontend contract (history list)

The UI should request `GET /me/explanations` and render list items using these fields:

- `id`, `summary`, `highlights`, `anomaly_count`, `model`, `model_version`, `artifact_hash`, `created_at`, `analysis_id`.

On user click, the UI requests `GET /explanations/{id}/artifact` to stream and render the full explanation JSON.

## Operational recommendations

- Production storage: move artifacts to object storage (S3) and store an `s3://` URL in `artifact_path`. Add lifecycle rules for retention.
- Access control: verify ownership before serving artifacts; do not expose artifact path directly to clients.
- Backups: include `artifacts/explanations/` in regular backups or export blobs to object storage.

## How to run locally

```bash
cd AnomalyEngine
source venv/bin/activate
uvicorn src.api.app:app --reload --port 8000

# run unit tests
pytest -q
```

## Appendix: Example API JSONs

Sample history item (list):

```json
{
   "id": 12,
   "analysis_id": null,
   "user_id": 1,
   "artifact_hash": "d2c9f3a1...",
   "summary": "Price spike on 2024-01-05; multiple detectors agree.",
   "highlights": ["Price was 4.2σ above mean", "Volume 6.3× average"],
   "anomaly_count": 3,
   "model": "gpt-xyz",
   "model_version": "1.0",
   "created_at": "2026-06-06T12:34:56Z"
}
```

Full artifact JSON (served by `/explanations/{id}/artifact`) is project-dependent; include it in reports as an appendix (redact secrets).

---

If you'd like, I can now:

- add the API routes (`GET /me/explanations`, `GET /explanations/{id}`, `GET /explanations/{id}/artifact`) and tests,
- or scaffold an Alembic migration for the `explanations` table.

Tell me which you'd like me to implement next.

