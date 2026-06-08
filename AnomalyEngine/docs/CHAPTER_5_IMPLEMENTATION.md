5. Chapter 5: Implementation and Testing

5.1. Implementation

5.1.1. Tools Used

- Programming languages: Python 3.10+ (backend), JavaScript / React (frontend), Bash for scripts.
- Frameworks and libraries:
  - FastAPI (backend HTTP API)
  - SQLAlchemy (ORM)
  - Pydantic (request/response schemas)
  - Uvicorn (ASGI server)
  - React + Vite (AnomalyUI production UI)
  - pytest (testing)
- Database platforms: SQLite for development; instructions provided for Alembic migrations targeting PostgreSQL or MySQL for production.
- Tools: git, Dockerfile provided for containerization, CLI: curl, sqlite3 for quick DB inspection.

5.1.2. Implementation Details of Modules

 Overview
 - The system separates concerns between: API (FastAPI), persistence (SQLAlchemy models, CRUD), artifact I/O (`src/utils/io.py`), AI integration (`src/api/ai_services.py`), and frontend clients (React UI).

Modules and responsibilities

1) src/api/app.py
- Registers API routes.
- Expose endpoints for analysis and explanation generation (`POST /analyze/explain`).
- Handles request authentication/authorization, invokes service layer, returns compact responses.

2) src/api/models.py
- Declarative SQLAlchemy models for `User`, `UserAnalysis`, `UserActivity`, `Notification` and the new `Explanation` model.
- `Explanation` fields: `id`, `analysis_id`, `user_id`, `artifact_path`, `artifact_hash`, `model`, `model_version`, `summary`, `highlights`, `entries`, `anomaly_count`, `meta`, `created_at`.
- Note: attribute named `meta` to avoid SQLAlchemy reserved `metadata` name.

3) src/api/schemas.py
- Pydantic schemas for request/response validation.
- Added `ExplanationRead` for history listing: exposes `id`, `artifact_path`, `artifact_hash`, `summary`, `highlights`, `anomaly_count`, `meta`, `created_at`.

4) src/api/crud.py
- DB helper functions:
  - `create_explanation(db, user_id, explanation_obj, analysis_id=None, metadata=None)` — writes artifact (calls I/O util), inserts compact DB row, returns created instance.
  - `get_explanations_by_user(db, user_id, limit=20, offset=0)` — paginated list of metadata.
  - `get_explanation(db, id)` — fetch single record.
  - `get_explanations_older_than(db, cutoff)` — for cleanup.

5) src/utils/io.py
- `write_explanation_artifact(user_id, explanation_obj)`
  - Deterministic JSON serialization: `json.dumps(obj, sort_keys=True, separators=(",",":"), ensure_ascii=False)`.
  - Compute SHA256 over JSON bytes: `sha256(json_bytes).hexdigest()`.
  - Persist file to `artifacts/explanations/{user_id}/explanation_{uuid}.json`.
  - Return `{"path": str(path), "hash": digest}`.
- `read_explanation_artifact(path)` reads and returns JSON.

6) src/api/ai_services.py
- Builds prompt context, calls AI model, and parses LLM output into structured `explanation_obj`.
- The parser extracts `summary`, `highlights`, `entries`, and `anomaly_count` used for DB metadata.

7) Frontend (AnomalyUI)
- Implements a history view that calls `GET /me/explanations` to list compact history.
- On demand, requests `GET /explanations/{id}/artifact` to display the full JSON explanation.

Design decisions
- Persist artifacts as files on disk for simplicity and eventual migration to object storage (S3) if needed.
- Store only compact metadata in DB to keep queries fast and schema small.
- Use deterministic JSON dumps to allow optional deduplication by hash.
- Keep artifact retrieval behind an authorized API route to enforce ownership.

5.2. Testing

5.2.1. Test Cases for Unit Testing

Unit tests should be small and deterministic. Key unit tests include:

- test_write_explanation_artifact: verify deterministic JSON, file exists, and SHA256 digest matches file bytes.
  - Input: small explanation dict
  - Expected: file written, returned hash equals recomputed hash

- test_create_explanation_inserts_row (uses in-memory SQLite session):
  - Setup: in-memory DB session, mock `write_explanation_artifact` to return known path/hash
  - Action: call `create_explanation`
  - Expected: DB row created with artifact_path and artifact_hash set

- test_get_explanations_pagination:
  - Create N rows, request pages and verify correct counts and ordering.

- test_read_artifact_fails_on_missing_file:
  - Verify `read_explanation_artifact` raises or returns proper error when file missing.

5.2.2. Test Cases for System Testing

System/integration tests validate full flow using FastAPI `TestClient` with mocked AI service:

- test_explain_flow_end_to_end:
  - Mock AI service to return deterministic structured explanation.
  - POST `/analyze/explain` as authenticated user.
  - Verify: response status 200, `explanation_id` present, artifact file exists under `artifacts/explanations/{user_id}` and DB row exists.

- test_history_and_artifact_fetch:
  - Create explanation entries (via API or directly via CRUD), call `GET /me/explanations` and assert list includes created items.
  - Call `GET /explanations/{id}/artifact` and assert the JSON content matches the stored file.

- test_authorization_on_artifact:
  - Attempt to fetch an artifact for another user; expect 403 Forbidden.

- test_deduplication_by_hash (if implemented):
  - Send two identical explanation requests with volatile fields normalized; expect second call to reference existing artifact (same `artifact_hash`) or return existing artifact id.

5.3. Result Analysis

Summary of results from development verification (June 2026):

- Artifact write and DB history insert: PASS
  - The `write_explanation_artifact` utility produced stable JSON and SHA256 digests for identical inputs.
  - The DB `explanations` rows recorded artifact path and hash; `Base.metadata.create_all` created the table in dev.

- UI history behaviour: PASS
  - The UI lists compact metadata only; full artifact is retrieved on-demand via authorized route.

- Edge cases and observations:
  - Transient fields (timestamps, request ids) in the explanation JSON will cause different hashes across runs; if deduplication is required, remove or canonicalize these fields before hashing.
  - Storing artifacts on disk is suitable for development; for production, object storage with lifecycle policies is recommended.

Recommendations

- Add Alembic migrations for production schema changes (create `explanations` table).
- Implement automated unit and integration tests in CI (GitHub Actions or similar), mocking AI calls to keep tests deterministic and fast.
- Provide a cleanup script or object-store lifecycle to manage storage growth.
- Consider background workers (Celery/RQ) for slow AI operations and artifact writes at scale.

Appendix

- Example commands to run locally:

```bash
source venv/bin/activate
uvicorn src.api.app:app --reload --port 8000
pytest -q
```

- Example sqlite3 verification:

```bash
sqlite3 anomaly_engine.db "SELECT id, user_id, artifact_path, artifact_hash, summary FROM explanations ORDER BY created_at DESC LIMIT 5;"
```
