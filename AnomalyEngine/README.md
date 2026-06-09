# Anomaly Engine Backend

Anomaly Engine is the FastAPI backend for NEPSE stock anomaly detection. It manages authentication, user roles, anomaly analysis pipelines, caching, audit logs, and AI explanation artifacts.

## What this repository contains

- `src/api/` — FastAPI application, routes, database models, and security
- `src/pipelines/` — analysis pipeline implementation and runtime orchestration
- `src/components/` — data loading, feature engineering, anomaly detection, visualization, and explanation services
- `src/models/` — ML model implementations used by the analysis engine
- `src/utils/` — helper utilities for I/O, OTP, and environment handling
- `configs/` — configuration for feature definitions and timeframes
- `data/` — dataset CSV files for stock symbols
- `artifacts/` — cached results, hyperparameters, explanations, and model metadata
- `requirements.txt` — Python dependency list
- `pyproject.toml` — package metadata and dependency declaration

## Quick start

### 1. Create and activate a Python environment

```bash
cd AnomalyEngine
python -m venv .venv
.venv\Scripts\Activate.ps1   # Windows PowerShell
# or use `source .venv/bin/activate` on macOS/Linux
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Start the backend

```bash
uvicorn src.api.app:app --reload --host 127.0.0.1 --port 8000
```

The backend will:
- create the SQLite database schema automatically
- create a default admin user if none exists (`admin` / `admin123`)
- start the API on `http://localhost:8000`

### 3. Start the frontend

The frontend is located in the sibling `AnomalyUI/` folder:

```bash
cd ../AnomalyUI
npm install
npm run dev
```

Then open `http://localhost:5173` in your browser.

## Default credentials

- Username: `admin`
- Password: `admin123`

## Environment variables

Create a `.env` file in `AnomalyEngine/` to configure optional services:

```env
ENV=development
ARTIFACTS=./artifacts
GMAIL_ADDRESS=your-email@example.com
GMAIL_APP_PASSWORD=your-app-password
TAVILY_API_KEY=your-tavily-api-key
TOKEN=your-azure-keyvault-token-or-openai-token
MODEL_ENDPOINT=https://your-azure-openai-endpoint
MODEL_NAME=openai/gpt-4.1
```

These values are used for:
- artifact path overrides
- OTP email notifications
- AI explanation integration via Azure / Tavily

## Key features

- JWT authentication with bcrypt password hashing
- Role-based access control for users, analysts, and admins
- Admin user management and activity audit logs
- Analysis execution with result caching and history
- AI explanations persisted as immutable artifacts
- SQLite storage for persistence and fast local development

## Project structure overview

- `src/api/app.py` — FastAPI app setup, CORS, and startup lifecycle
- `src/api/routes/` — route modules for auth, analysis, admin, and artifacts
- `src/api/database.py` — SQLAlchemy engine/session configuration
- `src/api/models.py` — SQLAlchemy ORM models
- `src/api/crud.py` — database access helpers
- `src/api/security.py` — JWT and password utilities
- `src/pipelines/analysis_engine.py` — central analysis engine
- `src/components/explanation_engine.py` — AI explanation logic
- `src/utils/io.py` — artifact path and file I/O helpers

## API routes

- `POST /login` — authenticate and return JWT access/token
- `GET /me` — current user profile and notifications
- `POST /analyze` — execute anomaly analysis and cache results
- `POST /analyze/explain` — execute anomaly analysis and cache results
- `GET /users` — admin list users
- `POST /users` — admin create a user
- `DELETE /users/{id}` — admin delete a user
- `GET /users/{id}/activity` — admin view user audit log

## Running tests

Run the Python test suite from the backend root:

```bash
cd AnomalyEngine
python -m pytest -q
```

If you only want a subset:

```bash
python -m pytest tests/unit -q
python -m pytest tests/integration -q
```

## Development notes

- Update analysis behavior in `src/pipelines/analysis_engine.py`
- Change caching or database logic in `src/api/crud.py`
- Add admin API routes in `src/api/routes/admin.py`
- Customize explanations in `src/components/explanation_engine.py`
- Adjust frontend/backend integration using `AnomalyUI/`

## Troubleshooting

- Backend startup fails: verify `.venv` is activated and `requirements.txt` is installed.
- Port conflict: confirm `127.0.0.1:8000` is available.
- UI authentication issues: make sure frontend is using `VITE_API_BASE_URL=http://localhost:8000`.
- To reset the database: stop the backend, delete `anomaly_engine.db`, then restart.

## Notes

The frontend and backend are separate services. To use the full application, run both `AnomalyEngine` and `AnomalyUI` concurrently.
