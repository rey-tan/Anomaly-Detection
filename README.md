# Anomaly Engine (NEPSE stock anomaly detection)

A production-ready stock anomaly detection system with a FastAPI backend and Streamlit dashboard. Detects unusual price behavior using DBSCAN clustering and supports both static and realtime simulation modes with result caching, user authentication, role-based authorization, and comprehensive audit trails.

## Architecture

```
Anomaly Engine/
├── main.py                      # Streamlit dashboard (frontend + admin UI)
├── flask.py                     # Alternative Flask API (legacy)
├── src/
│   ├── api/                     # FastAPI backend
│   │   ├── app.py               # FastAPI app with auth, RBAC, analyze endpoints
│   │   ├── database.py          # SQLAlchemy setup (SQLite)
│   │   ├── models.py            # SQLAlchemy models (User, Cache, Activity, etc.)
│   │   ├── schemas.py           # Pydantic request/response models
│   │   ├── crud.py              # Database operations
│   │   ├── security.py          # JWT tokens, password hashing
│   │   └── __init__.py
│   ├── pipelines/               # Analysis pipelines
│   │   ├── anomaly_detection_pipeline.py
│   │   └── realtime_detection_pipeline.py
│   ├── components/              # Feature engineering, scaling, visualization
│   ├── models/                  # ML models (DBSCAN, etc.)
│   ├── analysis/                # Candlestick visualizers
│   └── utils/                   # Data loading, paths, helpers
├── configs/
│   └── config.yaml              # Feature definitions, timeframes
├── data/
│   ├── processed/               # Processed OHLCV data by date
│   └── raw/                     # Raw CSV exports
├── artifacts/
│   ├── models/                  # Trained model artifacts
│   ├── hyperparams/             # Best hyperparameters per symbol/timeframe
│   ├── metrics/                 # Pipeline metrics
│   └── allowed_symbols.json     # Valid stock symbols
├── pyproject.toml               # Package metadata
├── requirements.txt             # Dependencies
└── README.md
```

## How it works

1. **Backend (FastAPI)**: Handles authentication, authorization, pipeline execution, caching, and user management
   - `/login` — JWT-based user authentication with role assignment
   - `/me` — Get current user profile and notifications
   - `/analyze` — Execute pipeline with automatic caching and logging
   - `/cache/{hash}` — Retrieve cached results
   - `/users` — Admin user management (CRUD operations)
   - `/users/{id}/activity` — Admin audit log access

2. **Frontend (Streamlit)**: Interactive dashboard with role-based UI
   - Login required before access
   - Role-specific features (admin panel for user management)
   - Real-time visual feedback and notifications
   - Admin controls for system management

3. **Database (SQLite)**: Persistent storage for users, cache, audit trails, and notifications

## Prerequisites

- Python **3.10+**
- `pip` and `venv`

## Quick Start

### 1. Set up the environment

```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Start the FastAPI backend

```bash
uvicorn src.api.app:app --reload
```

This will:
- Create the SQLite database (`anomaly_engine.db`)
- Create the default admin user: `admin` / `admin123`
- Start the backend on `http://localhost:8000`

### 3. Start the Streamlit frontend (in a new terminal)

```bash
source venv/bin/activate   # If not already activated
streamlit run main.py
```

The dashboard opens at `http://localhost:8501`

### 4. Log in

- Username: `admin`
- Password: `admin123`

## Features

### Authentication & Authorization

- JWT-based session tokens with role assignment
- Password hashing with bcrypt
- Role-based access control (user, analyst, admin)
- Admin panel for user management

### Analysis Modes

- **Static**: Analyze historical data for a date range
- **Realtime Simulation**: Simulate rolling-window anomaly detection

### Result Caching

- Automatic cache on `/analyze` endpoint
- Configurable cache lookup before expensive pipeline runs
- Explicit cache save via `/cache` endpoint for re-runs

### Audit & Monitoring

- Complete activity logging for all user actions
- Analysis history tracking with performance metrics
- System notifications for completion and errors
- Admin access to user activity logs

### Visualizations

- Time series with anomaly markers
- Scatter plot (price vs. volume, colored by cluster)
- Technical analysis (SMA, RSI, Bollinger Bands)

## Configuration

Edit `configs/config.yaml` to define:
- Feature columns for analysis
- Valid timeframes
- Market holidays

Example:

```yaml
features:
  - close
  - volume
  - returns
  - volatility
```

Edit hyperparameters in `artifacts/hyperparams/{SYMBOL}.json`:

```json
{
  "1H": {
    "dbscan": {
      "eps": 0.5,
      "min_pts": 5
    }
  }
}
```

## Deployment

### For local development

```bash
# Terminal 1: Backend
uvicorn src.api.app:app --reload

# Terminal 2: Frontend
streamlit run main.py
```

### For production

1. Change `SECRET_KEY` in `src/api/security.py`
2. Use a production WSGI server (e.g., Gunicorn)
3. Use PostgreSQL instead of SQLite for scaling
4. Deploy frontend behind a reverse proxy

Example production backend startup:

```bash
gunicorn -w 4 -k uvicorn.workers.UvicornWorker src.api.app:app
```

## Development Notes

- Add new users via the backend API (extend the `/users` endpoint)
- Modify caching strategy in `src/api/crud.py` and `src/api/app.py`
- Pipeline logic is independent of the API; swap pipelines in `src/pipelines/`
- Visualizations use Plotly; customize in `src/components/visualization.py`

## Troubleshooting

**Backend fails to start:**
- Ensure port 8000 is not in use: `lsof -i :8000` (Mac/Linux) or `netstat -ano | findstr :8000` (Windows)
- Check that the venv is activated

**Frontend shows "Could not validate credentials":**
- Verify the backend is running on `http://localhost:8000`
- Check that you're using correct username/password (default: `admin` / `admin123`)

**Results not caching:**
- Verify the database file exists: `ls anomaly_engine.db`
- Check backend logs for database errors
- Ensure the same config payload is used (hash is based on stock, dates, features, timeframe, mode)

**API keeps creating the default admin user:**
- Delete `anomaly_engine.db` and restart the backend to reset

## License

Educational project for stock anomaly detection on NEPSE data.
