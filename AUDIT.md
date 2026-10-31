# FarmWise AI repository audit

Audit date: 2026-10-31
Branch: `main`
Scope: current source tree and deployment configuration; no live account data or secrets inspected.

## Existing working foundations

- React, TypeScript, and Vite frontend with farmer/buyer account flows.
- FastAPI API with JWT authentication, farm and harvest CRUD, marketplace conversations, and account-scoped data.
- SQLAlchemy models for farmers, farms, crops, markets, listings, conversations, and recommendations.
- Open-Meteo weather adapter exists in `backend/app/api/routes/weather.py`.
- Explainable rule-based crop scoring and budget scenarios are baselines, not trained AI predictions.
- Docker, Render Blueprint, and GitHub Pages workflow are present.

## Blocking gaps before the AI assistant phase

- There was no Alembic environment or baseline migration. Production app startup and the seed script initialized schema directly. This session adds the first Alembic environment and a legacy-safe baseline; the empty-Postgres gate still needs to run against PostgreSQL.
- Authentication now issues short-lived access tokens backed by hashed, rotating HTTP-only refresh sessions. Logout and refresh-token replay revoke the active token family.
- SlowAPI limits registration, login/Google login, refresh, and harvest/media submissions. Configure `REDIS_URL` to share counters across multiple backend processes; the fallback is per-process memory storage.
- An `AuditLog` model and sanitized writer now persist authentication lifecycle events. Other sensitive actions still need instrumentation as their modules are built.
- Dedicated assistant conversation/message persistence tables now exist, including language, per-conversation farm-context opt-in, and JSON source references. The authenticated chat API and LLM integration are not implemented yet.
- Soil tests, fertilizer recommendations, disease detections/feedback, notifications, plans, subscriptions, payments, and expert-review persistence tables are now in the schema. Their service APIs, model inference, and business workflows remain unimplemented.
- No LLM, RAG pipeline, embedding store, or disease image model is configured. Do not present generated advice or diagnoses as operational until those services and data sources exist.
- Market prices and buyer requirements include seed/demo data; a live AGMARKNET/data.gov.in feed is not implemented.
- Listing media is persisted as base64 data in the database.
- The frontend is concentrated in `src/App.tsx`; there is no dedicated assistant workspace.
- The translation endpoint was observed returning HTTP 503 because the deployed API lacks `GOOGLE_TRANSLATE_API_KEY`.

## Current gate

Phase 0 is in progress. The initial migration now targets both an empty database and the legacy schema created by the old application. CI is configured to run it on PostgreSQL 15, but the workflow has not run yet. The gate is not considered passed until that CI job and the test suite pass.

The assistant build must not start until the remaining Phase 0 requirements are closed and validated. Provider credentials and the agricultural source corpus will also be required before an LLM/RAG assistant can return real advice.
