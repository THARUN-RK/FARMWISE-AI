# FarmWise AI Backend

Production-oriented MVP backend for **India-Realistic Crop-to-Market Decision Intelligence**. The API connects farm inputs to crop recommendations, sowing windows, harvests, net-realization market ranking, buyer matching, enquiries, profit estimates, alerts, and impact metrics.

All seeded values are explicitly `DEMO DATA`; they are not live market quotes or validated agronomic guarantees.

## Architecture

FastAPI routes are backed by SQLAlchemy 2.x models and focused service engines in `app/services/engines.py`. PostgreSQL is the Docker target; SQLite is the default local fallback for quick tests. JWT bearer auth supports farmer, buyer, and admin roles. Crop, market, and buyer decisions are deterministic and explainable.

## Run locally

```powershell
cd backend
..\.venv\Scripts\python.exe -m pip install -r requirements.txt
$env:DATABASE_URL = "sqlite:///./farmwise.db" # omit when using .env/Postgres
..\.venv\Scripts\python.exe scripts/seed_database.py
..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

Swagger is available at `http://localhost:8000/docs`; OpenAPI JSON is at `/openapi.json`.

## Docker/Postgres

```powershell
cd backend
docker compose up --build
```

The container API is available at `http://localhost:8000`. Set `DATABASE_URL` and `JWT_SECRET` from `.env.example` in real environments. Do not commit secrets.

## Main endpoints

- `POST /api/v1/auth/register`, `POST /api/v1/auth/login`, `GET /api/v1/auth/me`
- `POST|GET|PUT /api/v1/farmers/profile`
- `POST /api/v1/farms`, `GET /api/v1/farms`, `PUT /api/v1/farms/{id}`
- `POST /api/v1/recommendations/crops`
- `GET /api/v1/recommendations/sowing-window/{crop_id}`
- `POST /api/v1/harvests`
- `GET /api/v1/markets`, `GET /api/v1/markets/prices`, `POST /api/v1/markets/recommend`
- `POST /api/v1/buyers/match`
- `POST|GET /api/v1/enquiries`, `PATCH /api/v1/enquiries/{id}/status`
- `POST /api/v1/profit/calculate`
- `GET /api/v1/weather/current`, `GET /api/v1/alerts`, `GET /api/v1/dashboard/impact`
- `GET /api/v1/admin/analytics`

All success payloads follow `{ success, data, message }`; validation and domain errors use FastAPI HTTP status codes.

## Demo credentials

After seeding: phone `+919999999999`, password `DemoPass123!`. This account is for local demonstration only.

Example:

```powershell
$login = Invoke-RestMethod http://localhost:8000/api/v1/auth/login -Method Post -ContentType 'application/json' -Body '{"phone":"+919999999999","password":"DemoPass123!"}'
$headers = @{ Authorization = "Bearer $($login.data.access_token)" }
Invoke-RestMethod http://localhost:8000/api/v1/farms -Headers $headers
```

## Migrations, tests, and ML roadmap

The SQLAlchemy metadata can be used to initialize Alembic. For a production migration workflow, configure `alembic/env.py` with `Base.metadata` and run `alembic revision --autogenerate` then `alembic upgrade head`. The current MVP uses a transparent moving/rules baseline; future training can add `app/ml` and persist a versioned model after evaluating sufficient historical data.

Run tests with:

```powershell
..\.venv\Scripts\python.exe -m pytest -q
```

## Known limitations

Weather is a mock provider, the forecast endpoint is intentionally not exposed until historical-data validation is added, and market/buyer records are simulated. Add a real weather adapter, Alembic environment, role-specific buyer/admin workflows, rate limiting, structured JSON logging, and live data provenance before production deployment.
