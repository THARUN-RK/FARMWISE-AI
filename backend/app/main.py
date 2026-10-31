"""
FarmWise AI — FastAPI application factory.

All routes have been moved to app/api/routes/*.

This file is responsible for:
- Creating the FastAPI app
- Registering middleware (CORS, exception handlers)
- Including all routers
- Registering route-level rate limiting
"""

import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.api.routes import (
    auth,
    buyers,
    crops,
    dashboard,
    farms,
    harvests,
    markets,
    translate,
    weather,
)
from app.core.config import settings
from app.core.limiter import limiter


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

log = logging.getLogger("farmwise")


# ── Database initialisation ───────────────────────────────────────────────────

# ── Application ───────────────────────────────────────────────────────────────

app = FastAPI(
    title="FarmWise AI API",
    version="1.1.0",
    description=(
        "India-realistic crop-to-market decision intelligence for farmers. "
        "All AI scores are estimates and decision-support tools, not guarantees."
    ),
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)


# ── CORS ──────────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Global exception handler ──────────────────────────────────────────────────

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """Return a clean JSON error for any unhandled exception."""
    log.exception(
        "Unhandled error on %s %s",
        request.method,
        request.url.path,
    )

    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "An unexpected server error occurred. Please try again.",
        },
    )


# ── Health ────────────────────────────────────────────────────────────────────

@app.get("/health", tags=["health"])
def health():
    """Simple liveness probe."""
    return {
        "status": "ok",
        "version": app.version,
    }


# ── Routers ───────────────────────────────────────────────────────────────────

PREFIX = "/api/v1"

# Authentication
app.include_router(auth.router, prefix=PREFIX)

# Farms
app.include_router(
    farms.router,
    prefix=PREFIX,
)

# Harvests
app.include_router(
    harvests.router,
    prefix=PREFIX,
)

# Crops
app.include_router(
    crops.router,
    prefix=PREFIX,
)
app.include_router(
    crops.catalog_router,
    prefix=PREFIX,
)

# Markets
app.include_router(
    markets.router,
    prefix=PREFIX,
)

# Buyers
app.include_router(
    buyers.router,
    prefix=PREFIX,
)

# Weather
app.include_router(
    weather.router,
    prefix=f"{PREFIX}/weather",
)

# Dashboard
app.include_router(
    dashboard.router,
    prefix=PREFIX,
)

# Translation
app.include_router(
    translate.router,
    prefix=PREFIX,
)


# ── Backward-compatible farmer profile routes ─────────────────────────────────
# The original /api/v1/farmers/profile routes are kept for compatibility.

app.include_router(
    auth.profile_router,
    prefix=f"{PREFIX}/farmers",
    include_in_schema=False,
)
