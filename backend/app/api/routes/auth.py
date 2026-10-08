"""
Authentication routes: register, login, me, profile CRUD.

Logic is identical to the original main.py implementation — only
the file location has changed to follow proper FastAPI router structure.
"""
import logging
import secrets

from fastapi import APIRouter, Depends, HTTPException
from google.auth.exceptions import TransportError
from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2 import id_token
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import current_user, farmer_only
from app.core.config import settings
from app.core.database import get_db
from app.core.security import create_access_token, hash_password, verify_password
from app.models.entities import Farmer
from app.schemas.common import (
    CurrentUser,
    GoogleLoginRequest,
    LoginRequest,
    ProfileUpdate,
    RegisterRequest,
)

log = logging.getLogger("farmwise.auth")
router = APIRouter(prefix="/auth", tags=["auth"])


def _response(data, message: str = ""):
    return {"success": True, "data": data, "message": message}


@router.post("/register", status_code=201)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    """Create a new farmer/buyer account."""
    if body.role not in ("farmer", "buyer", "admin"):
        raise HTTPException(422, "Unsupported role")
    if db.scalar(select(Farmer).where(Farmer.phone == body.phone)):
        raise HTTPException(409, "Phone already registered")
    if body.email and db.scalar(select(Farmer).where(Farmer.email == body.email)):
        raise HTTPException(409, "Email already registered")

    user = Farmer(
        name=body.name,
        phone=body.phone,
        email=body.email,
        password_hash=hash_password(body.password),
        role=body.role,
        language=body.language,
        state=body.state,
        district=body.district,
        location_name=body.district,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    log.info("register user_id=%s role=%s", user.id, user.role)
    return _response(
        {"user": CurrentUser.model_validate(user), "access_token": create_access_token(str(user.id), user.role)},
        "Account created",
    )


@router.post("/login")
def login(body: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate with phone/email + password, return JWT."""
    identifier = body.identifier or body.phone
    user = db.scalar(
        select(Farmer).where(
            (Farmer.phone == identifier)
            | (func.lower(Farmer.email) == identifier.lower())
        )
    )
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(401, "Invalid credentials")
    log.info("login user_id=%s", user.id)
    return _response(
        {
            "access_token": create_access_token(str(user.id), user.role),
            "token_type": "bearer",
            "user": CurrentUser.model_validate(user),
        },
        "Login successful",
    )


def verify_google_credential(credential: str) -> dict:
    if not settings.google_client_id:
        raise HTTPException(503, "Google sign-in is not configured on this backend")
    try:
        claims = id_token.verify_oauth2_token(
            credential,
            GoogleRequest(),
            audience=settings.google_client_id,
        )
    except ValueError as exc:
        raise HTTPException(401, "Google credential is invalid or expired") from exc
    except TransportError as exc:
        log.exception("Google token verification unavailable")
        raise HTTPException(503, "Google sign-in verification is temporarily unavailable") from exc
    if claims.get("iss") not in ("accounts.google.com", "https://accounts.google.com"):
        raise HTTPException(401, "Google credential issuer is invalid")
    if claims.get("email_verified") not in (True, "true"):
        raise HTTPException(401, "A verified Google email is required")
    if not claims.get("sub") or not claims.get("email"):
        raise HTTPException(401, "Google account is missing a verified email")
    return claims


@router.post("/google")
def google_login(body: GoogleLoginRequest, db: Session = Depends(get_db)):
    """Verify a Google ID token and sign in or create a farmer account."""
    claims = verify_google_credential(body.credential)
    email = str(claims["email"]).strip().lower()
    user = db.scalar(select(Farmer).where(func.lower(Farmer.email) == email))
    if user:
        log.info("google_login user_id=%s", user.id)
        return _response({
            "access_token": create_access_token(str(user.id), user.role),
            "token_type": "bearer",
            "user": CurrentUser.model_validate(user),
        }, "Google login successful")

    if not body.phone:
        return _response({
            "phone_required": True,
            "email": email,
            "name": claims.get("name", email.split("@", 1)[0]),
        }, "Add a phone number to finish creating your farmer account")
    if db.scalar(select(Farmer).where(Farmer.phone == body.phone)):
        raise HTTPException(409, "Phone already registered to another account")

    user = Farmer(
        name=str(claims.get("name") or email.split("@", 1)[0])[:120],
        phone=body.phone,
        email=email,
        password_hash=hash_password(secrets.token_urlsafe(48)),
        role="farmer",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    log.info("google_register user_id=%s", user.id)
    return _response({
        "access_token": create_access_token(str(user.id), user.role),
        "token_type": "bearer",
        "user": CurrentUser.model_validate(user),
    }, "Google account created")


@router.get("/me")
def me(user: Farmer = Depends(current_user)):
    """Return the currently authenticated user."""
    return _response(CurrentUser.model_validate(user))


@router.post("/profile")
def create_profile(
    body: ProfileUpdate,
    user: Farmer = Depends(current_user),
    db: Session = Depends(get_db),
):
    """Create or overwrite authenticated account profile fields."""
    for key, value in body.model_dump().items():
        setattr(user, key, value)
    db.commit()
    db.refresh(user)
    return _response(CurrentUser.model_validate(user), "Profile saved")


@router.get("/profile")
def get_profile(user: Farmer = Depends(current_user)):
    """Get the current user's profile."""
    return _response(CurrentUser.model_validate(user))


@router.put("/profile")
def update_profile(
    body: ProfileUpdate,
    user: Farmer = Depends(current_user),
    db: Session = Depends(get_db),
):
    """Update authenticated account profile (alias for POST /profile)."""
    return create_profile(body, user, db)


profile_router = APIRouter(tags=["auth"])
profile_router.add_api_route(
    "/profile", create_profile, methods=["POST"], include_in_schema=False
)
profile_router.add_api_route(
    "/profile", get_profile, methods=["GET"], include_in_schema=False
)
profile_router.add_api_route(
    "/profile", update_profile, methods=["PUT"], include_in_schema=False
)
