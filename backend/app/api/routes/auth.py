"""
Authentication routes: register, login, me, profile CRUD.

Logic is identical to the original main.py implementation — only
the file location has changed to follow proper FastAPI router structure.
"""
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import current_user, farmer_only
from app.core.database import get_db
from app.core.security import create_access_token, hash_password, verify_password
from app.models.entities import Farmer
from app.schemas.common import (
    CurrentUser,
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
        select(Farmer).where((Farmer.phone == identifier) | (Farmer.email == identifier))
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


@router.get("/me")
def me(user: Farmer = Depends(current_user)):
    """Return the currently authenticated user."""
    return _response(CurrentUser.model_validate(user))


@router.post("/profile")
def create_profile(
    body: ProfileUpdate,
    user: Farmer = Depends(farmer_only),
    db: Session = Depends(get_db),
):
    """Create or overwrite farmer profile fields."""
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
    user: Farmer = Depends(farmer_only),
    db: Session = Depends(get_db),
):
    """Update farmer profile (alias for POST /profile)."""
    return create_profile(body, user, db)
