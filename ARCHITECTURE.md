# Anomaly Engine — System Architecture

## Overview

Anomaly Engine is a distributed stock anomaly detection system with:
- **FastAPI backend** for pipeline execution, authentication, and caching
- **Streamlit frontend** for interactive dashboard and visualization
- **SQLite database** for user management and result persistence

## Component Design

### Backend (FastAPI)

**Entry point:** `src/api/app.py`

#### Authentication (`src/api/security.py`)

- JWT token-based auth with HS256
- Password hashing using bcrypt (via passlib)
- Default admin user created on startup

**Token flow:**
1. Client POSTs credentials to `/login`
2. Backend validates username/password against database
3. Backend returns JWT access token
4. Client includes token in `Authorization: Bearer <token>` header
5. Backend decodes and validates token on protected endpoints

#### Routes

| Route | Method | Auth | Purpose |
|-------|--------|------|---------|
| `/login` | POST | No | Issue JWT token |
| `/analyze` | POST | Yes | Run pipeline + auto-cache |
| `/cache/{hash}` | GET | Yes | Retrieve cached result |
| `/cache` | POST | Yes | Save result explicitly |

#### Database Models (`src/api/models.py`)

**User**
- `id` (PK)
- `username` (unique)
- `hashed_password`
- `is_active`
- `created_at`

**PipelineCache**
- `id` (PK)
- `config_hash` (unique) — SHA256 of config JSON
- `stock`, `mode`, `timeframe`, `start_date`, `end_date`
- `features` (JSON)
- `best_params` (JSON)
- `metrics` (JSON)
- `data` (JSON) — full result dataframe as list of dicts
- `created_at`

#### Pipeline Execution

When `/analyze` is called:

1. **Validate** request against `AnalyzeConfig` schema
2. **Hash** the config to generate `config_hash`
3. **Check cache** in `pipeline_cache` table
   - If hit: return cached data
   - If miss: continue
4. **Load hyperparams** from `artifacts/hyperparams/{stock}.json`
5. **Execute pipeline** (static or realtime mode)
   - `run_pipeline()` for static analysis
   - `run_realtime_pipeline()` for rolling-window simulation
6. **Serialize results** to JSON (convert DataFrame)
7. **Save to cache** in database
8. **Return** results to client

#### Caching Strategy

- **Config hash** is deterministic SHA256 of `{stock, mode, timeframe, start_date, end_date, features, best_params}`
- Same config = same hash = cache hit
- Cache is per-user (JWT token validates ownership implicitly; can be extended)
- Manual cache write via `/cache` POST for explicit control

### Frontend (Streamlit)

**Entry point:** `main.py`

#### Session State

```python
st.session_state["authenticated"]  # Boolean
st.session_state["auth_token"]     # JWT string
st.session_state["username"]       # Username string
st.session_state["results"]        # Analysis results dict
```

#### Flow

1. **Login check** — if not authenticated, show login form
2. **API login** — POST credentials to backend, store token
3. **Dashboard** — show controls (stock, date range, timeframe, mode)
4. **Analysis** — POST analysis config to `/analyze`, get results
5. **Cache save** — POST results to `/cache` (non-blocking, warnings only)
6. **Visualization** — render plots using Plotly

#### API Integration (`main.py` functions)

- `login(username, password)` — Call `/login`, store token
- `logout()` — Clear session state
- `analyze_via_api(payload)` — Call `/analyze`, handle errors
- `save_cache_via_api(payload, results)` — Call `/cache` to persist

### Data Pipeline

**Static Mode** (`src/pipelines/anomaly_detection_pipeline.py`)
- Load historical data for date range
- Preprocess (handle missing values, NaNs)
- Engineer features (SMA, RSI, volatility)
- Scale features
- Train DBSCAN on full dataset
- Return labeled clusters + metrics

**Realtime Mode** (`src/pipelines/realtime_detection_pipeline.py`)
- Load historical data
- Preprocess and engineer features
- Simulate rolling window (last 500 rows)
- Re-train DBSCAN for each step
- Return full dataset with rolling labels

### Visualization

**Plotly-based** (`src/components/visualization.py`)

- `plot_analysis()` — Price + technical indicators (SMA, RSI, Bollinger Bands)
- `plot_scatter()` — Price vs. volume, colored by cluster (-1 = anomaly)
- `plot_timeseries()` — Price line with anomaly markers

## Data Flow Diagram

```
┌─────────────────┐
│  Streamlit UI   │
└────────┬────────┘
         │ 1. POST /login (username, password)
         ▼
┌─────────────────────────────────────────┐
│         FastAPI Backend                 │
│  ┌──────────────────────────────────┐  │
│  │ 1. Validate credentials          │  │
│  │ 2. Generate JWT token            │  │
│  │ 3. Return token to Streamlit     │  │
│  └──────────────────────────────────┘  │
│  ┌──────────────────────────────────┐  │
│  │ POST /analyze                    │  │
│  │ 1. Hash config → cache_key       │  │
│  │ 2. Lookup in PipelineCache DB    │  │
│  │ 3. If miss: Run pipeline()       │  │
│  │ 4. Save to cache                 │  │
│  │ 5. Return {metrics, data}        │  │
│  └──────────────────────────────────┘  │
│              ▲                          │
│              │ 2. JWT in header         │
└──────────────┼──────────────────────────┘
               │
         ┌─────┴──────┐
         │            │
         ▼            ▼
    ┌────────────┐  ┌──────────────┐
    │ Hyperparams│  │SQLite DB     │
    │ JSON files │  │ (Users,      │
    │            │  │  Cache)      │
    └────────────┘  └──────────────┘
```

## Security Considerations

### Authentication
- JWT tokens expire after `ACCESS_TOKEN_EXPIRE_MINUTES` (default 60)
- Passwords hashed with bcrypt (10+ rounds)
- Default credentials should be changed in production

### Caching
- Cache is stored in plaintext in SQLite (not encrypted)
- In production, consider encrypting sensitive columns
- Cache hash is deterministic; users can't forge cache entries (JWT prevents tampering)

### API Access
- All pipeline endpoints require valid JWT
- Database queries are parameterized (SQLAlchemy ORM prevents SQL injection)
- CORS not enabled; assumes same-origin deployment

## Scalability & Production Notes

### Database Scaling
- **SQLite** is fine for single-user / small team
- **PostgreSQL** recommended for multi-user production
  - Update `SQLALCHEMY_DATABASE_URL` in `src/api/database.py`
  - Install `psycopg2-binary`

### Backend Scaling
- **Development:** `uvicorn src.api.app:app --reload`
- **Production:** Use Gunicorn with Uvicorn workers
  ```bash
  gunicorn -w 4 -k uvicorn.workers.UvicornWorker src.api.app:app
  ```

### Frontend Deployment
- Streamlit Cloud, AWS EC2, or Docker
- Set `API_URL` environment variable or hardcode in `main.py`
- Consider Nginx reverse proxy for HTTPS

### Environment Variables
Consider using `.env` file (via `python-dotenv`):
```
DATABASE_URL=sqlite:///anomaly_engine.db
SECRET_KEY=<your-secret-key>
API_URL=http://localhost:8000
```

## Extension Points

### Adding a new user endpoint
```python
@app.post("/users", response_model=schemas.UserRead)
def create_user(request: schemas.UserCreate, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    # Only admin can create users
    if current_user.username != "admin":
        raise HTTPException(status_code=403, detail="Forbidden")
    return crud.create_user(db, request.username, request.password)
```

### Changing the ML model
1. Replace `run_pipeline()` in `src/pipelines/anomaly_detection_pipeline.py`
2. Update feature engineering in `src/components/feature_engineering.py`
3. Adjust schema/frontend visualization as needed

### Adding caching invalidation
```python
@app.delete("/cache/{config_hash}")
def invalidate_cache(config_hash: str, db: Session = Depends(database.get_db)):
    db.query(models.PipelineCache).filter(models.PipelineCache.config_hash == config_hash).delete()
    db.commit()
    return {"status": "deleted"}
```

## Testing

Run syntax checks:
```bash
python -m py_compile main.py src/api/app.py src/api/crud.py
```

Test backend startup:
```bash
uvicorn src.api.app:app --reload &
curl http://localhost:8000/login -X POST -d "username=admin&password=admin123"
```

Test frontend:
```bash
streamlit run main.py
# Navigate to http://localhost:8501 and test login flow
```

## Troubleshooting

### "Incorrect username or password"
- Check database: `sqlite3 anomaly_engine.db "SELECT * FROM users;"`
- Ensure default user exists or create one manually

### Cache not working
- Verify database file is writable
- Check that same config is used (hash must match)
- Inspect `PipelineCache` table for entries

### API timeout
- Increase Streamlit timeout: `timeout=600` in `requests.post()`
- Optimize pipeline (reduce data, features, or model complexity)
