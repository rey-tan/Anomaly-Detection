# Development Guide

## Project Setup

### 1. Clone and Environment

```bash
cd /path/to/AnomalyEngine
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install -e .  # Optional: editable install for library access
```

### 2. Start Backend

```bash
uvicorn src.api.app:app --reload
```

Backend available at `http://localhost:8000`

API docs (Swagger UI): `http://localhost:8000/docs`

### 3. Start Frontend (new terminal)

```bash
cd AnomalyUI
npm install
npm run dev
```

Frontend available at the AnomalyUI dev server (typically `http://localhost:5173` for Vite)

## Code Structure

### `src/api/` — FastAPI Backend

- `app.py` — Main app, routes (`/login`, `/me`, `/analyze`, `/users`, `/cache`)
- `database.py` — SQLAlchemy engine, session factory
 - `models.py` — SQLAlchemy ORM models (`User`, `UserActivity`, `Notification`, `UserAnalysis`)
- `schemas.py` — Pydantic request/response models
- `crud.py` — Database CRUD operations + config hashing + activity logging
- `security.py` — JWT token, password hashing, role-based authorization

**When to modify:**
- Add a new endpoint → update `app.py`
- Change database schema → update `models.py` and `schemas.py`
- Add new auth/authorization flow → update `security.py` and `crud.py`
- Add user management features → update `app.py`, `crud.py`, `models.py`

### `src/pipelines/` — Analysis Pipelines

- `anomaly_detection_pipeline.py` — Static pipeline
- `realtime_detection_pipeline.py` — Realtime/rolling-window pipeline

**When to modify:**
- Change preprocessing → update `preprocess()` in `components/preprocessing.py`
- Add features → update `build_features()` in `components/feature_engineering.py`
- Swap ML model → update `train_model()` in `components/anomaly_detection.py`

### `src/components/` — Pipeline Utilities

- `data_loader.py` — Load CSV data from disk
- `preprocessing.py` — Clean, filter, handle NaNs
- `feature_engineering.py` — SMA, RSI, Bollinger Bands, returns, volatility
- `scaling.py` — Normalize features
- `anomaly_detection.py` — DBSCAN model
- `evaluation.py` — Compute metrics (anomaly_rate, cluster stats)
- `visualization.py` — Plotly plots

### `src/models/` — ML Models

- `dbscan.py` — DBSCAN implementation

### `src/utils/` — Utilities

- `paths.py` — Project directory paths
- `load.py` — Load config YAML, JSON hyperparams
- `timeframes.py` — Valid timeframes, holiday generation

## Common Tasks

### Add a new analysis feature

1. Implement in `src/components/feature_engineering.py`:
   ```python
   def build_features(df: pd.DataFrame, features: list) -> pd.DataFrame:
       # ... existing code ...
       df["my_new_feature"] = ...
       return df
   ```

2. Add to `config.yaml`:
   ```yaml
   features:
     - close
     - my_new_feature  # Add here
   ```

3. Test:
   ```bash
   python -c "from src.components.feature_engineering import build_features; ..."
   ```

### Add a new user

Via backend startup (default `admin` / `admin123`):
   ```python
   # In src/api/app.py, startup_event():
   crud.create_user(db, "newuser", "password123")
   ```

Or via API (add endpoint):
   ```python
   @app.post("/users", response_model=schemas.UserRead)
   def create_user(request: schemas.UserCreate, db: Session = Depends(database.get_db)):
       return crud.create_user(db, request.username, request.password)
   ```

### Modify visualization

Edit `src/components/visualization.py`:

```python
def plot_analysis(symbol, df, timeframe):
    # Customize plots here
    fig = go.Figure()
    # ... add traces ...
    return fig
```

Then restart the AnomalyUI dev server if needed (Vite will auto-reload on save).

### Change database (SQLite → PostgreSQL)

1. Update `src/api/database.py`:
   ```python
   SQLALCHEMY_DATABASE_URL = "postgresql://user:password@localhost/anomaly_engine"
   ```

2. Install driver:
   ```bash
   pip install psycopg2-binary
   ```

3. Create database:
   ```bash
   createdb anomaly_engine
   ```

4. Restart backend (schema auto-creates via `metadata.create_all()`)

### Debug

Enable verbose logging:

```python
# In src/api/app.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

Check database:
```bash
sqlite3 anomaly_engine.db
> SELECT * FROM users;
```

Test pipeline directly:
```bash
python -c "
from src.pipelines.anomaly_detection_pipeline import run_pipeline
config = {'stock': 'NABIL', 'start_date': '2024-01-01', 'end_date': '2024-12-31', 'timeframe': '1D', 'features': ['close', 'volume']}
result = run_pipeline(config, {'dbscan': {'eps': 0.5, 'min_pts': 5}})
print(result['metrics'])
"
```

## Testing

### Unit tests

Add to `tests/` directory:

```python
# tests/test_crud.py
from src.api import crud
from src.api.database import SessionLocal

def test_create_user():
    db = SessionLocal()
    user = crud.create_user(db, "testuser", "password")
    assert user.username == "testuser"
    db.close()
```

Run:
```bash
pytest tests/
```

### Integration tests

Test the full API:

```bash
# Start backend
uvicorn src.api.app:app &

# Test login
curl -X POST http://localhost:8000/login \
  -d "username=admin&password=admin123"

# Test analyze
curl -X POST http://localhost:8000/analyze \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "stock": "NABIL",
    "start_date": "2024-01-01",
    "end_date": "2024-12-31",
    "timeframe": "1D",
    "features": ["close", "volume"],
    "mode": "Static"
  }'
```

## Deployment

### Docker (Local Testing)

```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY . .
RUN pip install -r requirements.txt

EXPOSE 8000
CMD ["uvicorn", "src.api.app:app", "--host", "0.0.0.0"]
```

Build and run:
```bash
docker build -t anomaly-engine .
docker run -p 8000:8000 anomaly-engine
```

### Systemd Service (Linux)

Create `/etc/systemd/system/anomaly-engine.service`:
```ini
[Unit]
Description=Anomaly Engine API
After=network.target

[Service]
User=www-data
WorkingDirectory=/opt/anomaly-engine
ExecStart=/opt/anomaly-engine/venv/bin/uvicorn src.api.app:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable anomaly-engine
sudo systemctl start anomaly-engine
```

## Code Style

Use [Black](https://black.readthedocs.io/) for formatting:

```bash
pip install black
black src/ main.py
```

Use [isort](https://pycqa.github.io/isort/) for import sorting:

```bash
pip install isort
isort src/ main.py
```

Use [pylint](https://www.pylint.org/) for linting (optional):

```bash
pip install pylint
pylint src/
```

## Contributing

1. Create a feature branch: `git checkout -b feature/my-feature`
2. Make changes and test locally
3. Format code: `black src/ main.py && isort src/ main.py`
4. Commit: `git commit -m "Add my feature"`
5. Push and open a PR

## Common Issues

### Import errors

Ensure venv is activated:
```bash
source venv/bin/activate
```

Or add `src/` to PYTHONPATH:
```bash
export PYTHONPATH="${PYTHONPATH}:/path/to/AnomalyEngine/src"
python main.py
```

### Port already in use

Kill the process:
```bash
lsof -i :8000  # Find process ID
kill -9 <PID>
```

Or use a different port:
```bash
uvicorn src.api.app:app --port 8001
```

### Database locked (SQLite)

If you see "database is locked", ensure only one process is writing. Close all terminals and restart.

For production, use PostgreSQL instead of SQLite.

## Performance Tuning

### Cache hit rate

Monitor cache effectiveness:
```sql
SELECT COUNT(*) as total, COUNT(DISTINCT config_hash) as unique_configs FROM pipeline_cache;
```

### Pipeline optimization

Profile with:
```python
import cProfile
cProfile.run("run_pipeline(config, best_params)")
```

Focus optimizations on:
- Feature engineering (vectorize with NumPy)
- DBSCAN parameters (eps, min_pts trade-off)
- Data loading (cache raw data if loading frequently)

### API response time

Add middleware:
```python
from fastapi import Request
import time

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response
```

## Next Steps

- [ ] Add user management endpoint (`/users`)
- [ ] Implement cache invalidation (`DELETE /cache/{hash}`)
- [ ] Add audit logging (who ran what analysis, when)
- [ ] Support multiple ML models (IsolationForest, LOF, Mahalanobis)
- [ ] Add email alerts for major anomalies
- [ ] Implement data export (CSV, JSON download)
- [ ] Build admin dashboard for user/cache management

### Explanation artifact development notes

- Explanations generated by the AI are written to `artifacts/explanations/{user_id}` as JSON files. The writing function `src/utils/io.py::write_explanation_artifact` returns both the file path and a SHA256 hash of the stable JSON dump.
- The database stores a compact history record in the new `explanations` table with `artifact_path`, `artifact_hash`, `summary`, `highlights`, `anomaly_count`, `user_id`, and `created_at`.
- UI changes: The UI only shows the history entry (no full explanation persisted in DB). To view the full explanation, the UI should request the artifact file via a backend route that reads the JSON file and returns it to the client.

Developer checklist for explanation artifacts:

1. Generate explanation via `/analyze/explain` (backend handles artifact writing automatically).
2. Backend computes hash and persists a history record via `crud.create_explanation`.
3. To inspect artifacts manually, open `artifacts/explanations/{user_id}` and verify JSON files and SHA256 digests.
4. Consider adding retention/cleanup scripts for `artifacts/explanations/` (cron or management command).
