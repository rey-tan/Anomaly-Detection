# Anomaly Engine UI

The Anomaly Engine UI is a React + Vite frontend for the NEPSE anomaly detection platform. This app connects to the FastAPI backend in `../AnomalyEngine` and lets users run analysis, inspect results, and manage admin workflows.

## What this UI includes

- User login and role-based access control
- Analysis run flow with results dashboard
- AI explanation requests for flagged anomalies
- Admin user management (create / delete users)
- Admin activity audit log

## Repository layout

- `src/` — frontend source code
- `public/` — static assets
- `e2e/` — Playwright end-to-end tests

## Prerequisites

- Node.js 18 or newer
- `npm` installed
- Backend API available at `http://localhost:8000`

## Frontend setup

Install dependencies:

```bash
cd AnomalyUI
npm install
```

Start the frontend:

```bash
cd AnomalyUI
npm run dev
```

Open the app at `http://localhost:5173`.

## Backend setup

The backend lives in `AnomalyEngine`. Run it in a separate terminal:

```bash
cd AnomalyEngine
.venv\Scripts\Activate.ps1
python -m uvicorn src.api.app:app --reload --host 127.0.0.1 --port 8000
```

## Environment configuration

The UI reads `VITE_API_BASE_URL` to locate the backend service. Configure it in `AnomalyUI/.env` if needed:

```env
VITE_API_BASE_URL=http://localhost:8000
```

The backend also uses `.env` configuration for auth keys and AI integration. See `AnomalyEngine/docs` for backend environment details.

## Testing

Run unit tests for the frontend:

```bash
cd AnomalyUI
npm test
```

Run end-to-end tests:

```bash
cd AnomalyUI
npm run test:e2e
```

## Notes

This UI is designed to work with the FastAPI backend in `AnomalyEngine`. Both services should be running for end-to-end workflows to function correctly.
