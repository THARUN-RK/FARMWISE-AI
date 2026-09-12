"""
FarmWise AI — FastAPI application factory.

All routes have been moved to app/api/routes/*.
This file is responsible for:
  - Creating the FastAPI app
  - Registering middleware (CORS, exception handlers)
  - Including all routers
  - Initialising the database schema on startup
"""
import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import auth, buyers, crops, dashboard, farms, harvests, markets, weather
from app.core.config import settings
from app.core.database import Base, engine, ensure_local_schema

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
log = logging.getLogger("farmwise")

# ── Database initialisation ────────────────────────────────────────────────────
Base.metadata.create_all(bind=engine)
ensure_local_schema()

# ── Application ────────────────────────────────────────────────────────────────
app = FastAPI(
    title="FarmWise AI API",
    version="1.1.0",
    description=(
        "India-realistic crop-to-market decision intelligence for farmers. "
        "All AI scores are estimates and decision-support tools, not guarantees."
    ),
)

# ── CORS ───────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Global exception handler ───────────────────────────────────────────────────
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """Return a clean JSON error for any unhandled exception (never expose a stack trace)."""
    log.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"success": False, "message": "An unexpected server error occurred. Please try again."},
    )


# ── Health ─────────────────────────────────────────────────────────────────────
@app.get("/health", tags=["health"])
def health():
    """Simple liveness probe."""
    return {"status": "ok", "version": app.version}


# ── Routers ────────────────────────────────────────────────────────────────────
PREFIX = "/api/v1"

app.include_router(auth.router, prefix=f"{PREFIX}/auth")
app.include_router(farms.router, prefix=f"{PREFIX}/farms")
app.include_router(harvests.router, prefix=f"{PREFIX}/harvests")
app.include_router(crops.router, prefix=f"{PREFIX}")
app.include_router(markets.router, prefix=f"{PREFIX}")
app.include_router(buyers.router, prefix=f"{PREFIX}")
app.include_router(weather.router, prefix=f"{PREFIX}/weather")
app.include_router(dashboard.router, prefix=f"{PREFIX}")

# ── Backward-compat aliases ────────────────────────────────────────────────────
# The original /api/v1/farmers/profile routes are kept for compatibility
# with any existing client that already uses them.
app.include_router(
    auth.router,
    prefix=f"{PREFIX}/farmers",
    include_in_schema=False,   # hide duplicates from Swagger
)
