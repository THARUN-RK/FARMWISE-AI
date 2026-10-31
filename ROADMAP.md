# FarmWise AI development roadmap

Status as of 2026-10-31. Work follows the project's required phase gates and ships one reviewable module at a time.

## Phase 0 — Foundations (current)

- [x] Create Alembic environment and first baseline migration.
- [x] Add dedicated assistant conversation/message tables, including source reference storage and opt-in farm context.
- [x] Add rotating/revocable refresh sessions and auth/media endpoint rate limits.
- [x] Add an audit-log model, sensitive-field filtering, and auth lifecycle events.
- [x] Add the planned soil, fertilizer, disease/feedback, notification, plan, subscription, payment, and expert-review tables.
- [x] Add a PostgreSQL-backed CI migration gate and run the API container as a non-root user.
- [x] Remove application-startup schema creation and run migrations through Render/Docker startup.
- [ ] Verify migration on empty PostgreSQL 15+ and on a database created by the previous application.
- [ ] Instrument remaining sensitive actions and complete the remaining security hardening.
- [ ] Add module-specific API validation and persistence tests as each service is implemented.
- [ ] Pass full backend tests and production secret boot checks.

**Gate:** empty PostgreSQL `alembic upgrade head` succeeds; test suite passes; production refuses weak/missing secrets; rate limits and migration path are validated.

## Phase 1 — Core AI and agronomy (blocked by Phase 0)

1. **Assistant:** authenticated persisted conversations; provider-agnostic OpenAI-compatible API client; English, Kannada, Hindi, Telugu, Tamil, and Malayalam; explicit no-key `503`; retrieval from curated and cited agricultural sources; high-risk escalation; no canned replies.
2. **Soil and fertilizer:** soil-test-backed nutrient guidance with source traces and safe handling of missing measurements.
3. **Disease detection:** secure image validation/storage, real model inference, confidence threshold, history, farmer feedback, and expert escalation. Requires a versioned model artifact.
4. **Real market feed:** official-source ingestion, timestamps, and clear distinction between official data and estimates.
5. **Weather alerts:** notifications based on the existing Open-Meteo adapter and documented alert rules.

Each module requires persistence, validation, authorization, failure-path tests, docs, and frontend loading/error/empty states.

## Phase 2 — SaaS

- Razorpay order creation, signature verification, webhooks, and entitlement checks.
- Admin and agricultural-expert workspaces, notifications, and usage/feedback views.
- Gate: test-mode checkout round trip using configured Razorpay test credentials.

## Phase 3 — Quality

- Split `src/App.tsx` into routes and reusable components; add query/form tooling.
- Frontend component, API integration, and end-to-end journeys.
- Coverage, performance, accessibility, and low-literacy farmer UX passes.

## Phase 4 — Launch

- Managed PostgreSQL, object storage, HTTPS, monitoring, uptime checks, and backups.
- Restore drill and documented operational runbook.
- Final security, data provenance, and go-live review.

## Next session's first task

Run the initial migration against a clean PostgreSQL service and the existing Render schema. Once the Phase 0 gate passes, implement the assistant's persisted conversation model and authenticated API contract before connecting any LLM provider.
