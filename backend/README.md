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
# Copy .env.example to .env, then set a strong JWT_SECRET. For Google sign-in,
# set GOOGLE_CLIENT_ID to the same value used by the frontend.
docker compose up --build
```

The container API is available at `http://localhost:8000`. Set `DATABASE_URL` and `JWT_SECRET` from `.env.example` in real environments. Do not commit secrets.

## Runtime environment

Set `APP_ENV=production` on production hosts. The API refuses to start when
`JWT_SECRET` is the development placeholder or contains fewer than 32 UTF-8
bytes. Generate a unique secret (for example, with Python's
`secrets.token_urlsafe(48)`) and store it in the host's secret manager. Do not
reuse the example value or commit a real secret. Local development defaults to
`APP_ENV=development`; production hosts must set the environment explicitly.

## Main endpoints

- `POST /api/v1/auth/register`, `POST /api/v1/auth/login`, `GET /api/v1/auth/me`
- `POST|GET|PUT /api/v1/farmers/profile`
- `POST /api/v1/farms`, `GET /api/v1/farms`, `PUT /api/v1/farms/{id}`
- `POST /api/v1/recommendations/crops`
- `GET /api/v1/recommendations/sowing-window/{crop_id}`
- `POST /api/v1/harvests`
- `GET /api/v1/harvests` (the farmer's harvests and listing status)
- `GET /api/v1/crops` (crop choices for harvest forms)
- `GET /api/v1/marketplace/listings` (authenticated crop photo/video listings without private contact details)
- `GET /api/v1/buyers` (buyer directory with public business/profile details)
- `GET|POST /api/v1/conversations`, `POST /api/v1/conversations/{id}/messages` (participant-only messaging with per-account contact/location consent)
- `GET /api/v1/markets`, `GET /api/v1/markets/prices`, `POST /api/v1/markets/recommend`
- `POST /api/v1/buyers/match`
- `POST|GET /api/v1/enquiries`, `PATCH /api/v1/enquiries/{id}/status`
- `POST /api/v1/profit/calculate`
- `POST /api/v1/dashboard/financial-forecast` (farmer-only low/expected/high budget and profit/loss scenarios)
- `GET /api/v1/translate/interface-strings/{language}` (fetch interface translations for a language from Google Cloud Translation API)
- `GET /api/v1/weather/current`, `GET /api/v1/alerts`, `GET /api/v1/dashboard/impact`
- `GET /api/v1/admin/analytics`

All success payloads follow `{ success, data, message }`; validation and domain errors use FastAPI HTTP status codes.

To share crop media, include `photo_data_url` as a base64 JPEG, PNG, WebP, MP4,
WebM, or QuickTime/MOV data URL in `POST /api/v1/harvests`. Decoded media is
limited to 10 MB. Listings do not disclose phone, email, or precise coordinates.
Each conversation participant independently chooses whether to share contact
details and saved location.

## Demo credentials

After seeding: phone `+919999999999`, password `DemoPass123!`. This account is for local demonstration only.

Google sign-in requires `GOOGLE_CLIENT_ID` to contain the same OAuth Web client
ID used by the frontend. The backend verifies Google ID-token signatures and
audience before creating or authenticating an account. New Google accounts
must supply a unique phone number. When using Docker Compose, put this value in
`backend/.env`; Compose passes it to the backend container.

To enable translation for supported language codes, set
`GOOGLE_TRANSLATE_API_KEY` to a Google Cloud Translation API key in the backend
environment (keep it secret; never commit it). The endpoint translates only a
fixed set of interface strings; it does not localize every screen, and some
scheduled-language codes are mapped to a nearby language or left in English.
User data (crop notes, profiles, private messages) is never sent for translation.
If translation is requested without a configured key or the provider fails, the
endpoint returns an error rather than claiming English text was translated.

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

Weather is a mock provider, market/buyer records may be simulated, and the financial forecast is an explainable scenario baseline rather than a trained predictive model. Add a real weather adapter, Alembic environment, rate limiting, structured JSON logging, and live data provenance before production deployment.
