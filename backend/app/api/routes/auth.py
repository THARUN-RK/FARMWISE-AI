"""
Authentication routes: register, login, me, profile CRUD.

Logic is identical to the original main.py implementation — only
the file location has changed to follow proper FastAPI router structure.
"""
import logging
import secrets
from datetime import datetime, timedelta
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from google.auth.exceptions import TransportError
from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2 import id_token
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.api.deps import current_user, farmer_only, oauth2
from app.core.config import settings
from app.core.database import get_db
from app.core.limiter import limiter
from app.core.security import create_access_token, hash_password, hash_refresh_token, verify_password
from app.models.entities import ContactDetail, Farmer, RefreshToken
from app.services.audit import record_audit_event
from app.schemas.common import (
    ContactDetailsRequest,
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


def _set_refresh_cookie(response: Response, token: str) -> None:
    secure = settings.app_env in ("staging", "production")
    response.set_cookie(
        "farmwise_refresh",
        token,
        max_age=settings.refresh_token_expire_days * 24 * 60 * 60,
        httponly=True,
        secure=secure,
        samesite="none" if secure else "lax",
        path="/api/v1/auth",
    )
    response.headers["Cache-Control"] = "no-store"


def _clear_refresh_cookie(response: Response) -> None:
    secure = settings.app_env in ("staging", "production")
    response.delete_cookie(
        "farmwise_refresh",
        httponly=True,
        secure=secure,
        samesite="none" if secure else "lax",
        path="/api/v1/auth",
    )


def _issue_session(
    db: Session,
    user: Farmer,
    response: Response,
    action: str,
    family_id: str | None = None,
) -> str:
    raw_refresh_token = secrets.token_urlsafe(48)
    token_hash = hash_refresh_token(raw_refresh_token)
    refresh = RefreshToken(
        farmer_id=user.id,
        token_hash=token_hash,
        family_id=family_id or str(uuid4()),
        expires_at=datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days),
    )
    db.add(refresh)
    db.flush()
    record_audit_event(
        db,
        actor_user_id=user.id,
        action=action,
        resource_type="refresh_session",
        resource_id=refresh.id,
        details={"role": user.role},
    )
    access_token = create_access_token(str(user.id), user.role, refresh.id)
    db.commit()
    _set_refresh_cookie(response, raw_refresh_token)
    return access_token


@router.post("/register", status_code=201)
@limiter.limit("5/minute")
def register(request: Request, body: RegisterRequest, response: Response, db: Session = Depends(get_db)):
    """Create a new farmer/buyer account."""
    if body.role not in ("farmer", "buyer"):
        raise HTTPException(422, "Choose Farmer or Buyer account type")
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
    db.flush()
    access_token = _issue_session(db, user, response, "auth.register")
    db.refresh(user)
    log.info("register user_id=%s role=%s", user.id, user.role)
    return _response(
        {"user": CurrentUser.model_validate(user), "access_token": access_token},
        "Account created",
    )


@router.post("/login")
@limiter.limit("10/minute")
def login(request: Request, body: LoginRequest, response: Response, db: Session = Depends(get_db)):
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
    access_token = _issue_session(db, user, response, "auth.login")
    log.info("login user_id=%s", user.id)
    return _response(
        {
            "access_token": access_token,
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
@limiter.limit("10/minute")
def google_login(request: Request, body: GoogleLoginRequest, response: Response, db: Session = Depends(get_db)):
    """Verify a Google ID token and sign in or create a farmer account."""
    claims = verify_google_credential(body.credential)
    email = str(claims["email"]).strip().lower()
    user = db.scalar(select(Farmer).where(func.lower(Farmer.email) == email))
    if user:
        access_token = _issue_session(db, user, response, "auth.google_login")
        log.info("google_login user_id=%s", user.id)
        return _response({
            "access_token": access_token,
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
    db.flush()
    access_token = _issue_session(db, user, response, "auth.google_register")
    db.refresh(user)
    log.info("google_register user_id=%s", user.id)
    return _response({
        "access_token": access_token,
        "token_type": "bearer",
        "user": CurrentUser.model_validate(user),
    }, "Google account created")


@router.post("/refresh")
@limiter.limit("30/minute")
def refresh_session(request: Request, response: Response, db: Session = Depends(get_db)):
    """Rotate one HTTP-only refresh cookie and revoke a family on replay."""
    origin = request.headers.get("origin")
    if (
        request.headers.get("x-farmwise-refresh") != "1"
        or (origin and origin not in settings.cors_origin_list)
    ):
        raise HTTPException(403, "Refresh request origin is not allowed")
    raw_token = request.cookies.get("farmwise_refresh")
    if not raw_token:
        _clear_refresh_cookie(response)
        raise HTTPException(401, "Refresh session is missing or expired")

    token_hash = hash_refresh_token(raw_token)
    refresh = db.scalar(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash).with_for_update()
    )
    if not refresh:
        _clear_refresh_cookie(response)
        raise HTTPException(401, "Refresh session is invalid or expired")

    now = datetime.utcnow()
    if refresh.revoked_at is not None:
        db.execute(
            update(RefreshToken)
            .where(RefreshToken.family_id == refresh.family_id, RefreshToken.revoked_at.is_(None))
            .values(revoked_at=now)
        )
        db.commit()
        _clear_refresh_cookie(response)
        raise HTTPException(401, "Refresh token replay detected; sign in again")
    if refresh.expires_at <= now:
        refresh.revoked_at = now
        db.commit()
        _clear_refresh_cookie(response)
        raise HTTPException(401, "Refresh session is expired")

    user = db.get(Farmer, refresh.farmer_id)
    if not user:
        refresh.revoked_at = now
        db.commit()
        _clear_refresh_cookie(response)
        raise HTTPException(401, "Account is no longer available")

    next_raw_token = secrets.token_urlsafe(48)
    next_hash = hash_refresh_token(next_raw_token)
    refresh.revoked_at = now
    refresh.replaced_by_hash = next_hash
    next_refresh = RefreshToken(
        farmer_id=user.id,
        token_hash=next_hash,
        family_id=refresh.family_id,
        expires_at=now + timedelta(days=settings.refresh_token_expire_days),
    )
    db.add(next_refresh)
    db.flush()
    record_audit_event(
        db,
        actor_user_id=user.id,
        action="auth.refresh",
        resource_type="refresh_session",
        resource_id=next_refresh.id,
    )
    access_token = create_access_token(str(user.id), user.role, next_refresh.id)
    db.commit()
    _set_refresh_cookie(response, next_raw_token)
    return _response({"access_token": access_token, "token_type": "bearer"}, "Session refreshed")


@router.post("/logout")
def logout(
    response: Response,
    token: str = Depends(oauth2),
    user: Farmer = Depends(current_user),
    db: Session = Depends(get_db),
):
    """Revoke this refresh session; its access token becomes invalid too."""
    from app.core.security import decode_token

    payload = decode_token(token)
    refresh = db.get(RefreshToken, int(payload["sid"]))
    if refresh and refresh.farmer_id == user.id and refresh.revoked_at is None:
        refresh.revoked_at = datetime.utcnow()
        record_audit_event(
            db,
            actor_user_id=user.id,
            action="auth.logout",
            resource_type="refresh_session",
            resource_id=refresh.id,
        )
        db.commit()
    _clear_refresh_cookie(response)
    return _response(None, "Logged out")


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
    for key, value in body.model_dump(exclude_none=True).items():
        setattr(user, key, value)
    db.commit()
    db.refresh(user)
    return _response(CurrentUser.model_validate(user), "Profile saved")


@router.get("/profile")
def get_profile(user: Farmer = Depends(current_user)):
    """Get the current user's profile."""
    return _response(CurrentUser.model_validate(user))


@router.get("/contact-details")
def get_contact_details(user: Farmer = Depends(current_user), db: Session = Depends(get_db)):
    """Fetch the current user's saved contact details."""
    query = select(ContactDetail).where(ContactDetail.farmer_id == user.id)
    if user.role == "buyer":
        query = select(ContactDetail).where(ContactDetail.buyer_id == user.id)
    contact = db.scalar(query.order_by(ContactDetail.is_primary.desc(), ContactDetail.updated_at.desc(), ContactDetail.id.desc()))
    if not contact:
        return _response(None, "No contact details saved yet")
    return _response({
        "id": contact.id,
        "phone": contact.phone,
        "alternate_phone": contact.alternate_phone,
        "email": contact.email,
        "whatsapp": contact.whatsapp,
        "address_line1": contact.address_line1,
        "address_line2": contact.address_line2,
        "city": contact.city,
        "district": contact.district,
        "state": contact.state,
        "pincode": contact.pincode,
        "preferred_contact_method": contact.preferred_contact_method,
        "is_primary": contact.is_primary,
    }, "Contact details loaded")


@router.post("/contact-details")
def save_contact_details(
    body: ContactDetailsRequest,
    user: Farmer = Depends(current_user),
    db: Session = Depends(get_db),
):
    """Save or update the current user's contact details."""
    if body.phone is None and body.email is None and body.whatsapp is None and body.address_line1 is None:
        raise HTTPException(400, "At least one contact field is required")

    where_clause = (ContactDetail.farmer_id == user.id) if user.role != "buyer" else (ContactDetail.buyer_id == user.id)
    contact = db.scalar(select(ContactDetail).where(where_clause).order_by(ContactDetail.is_primary.desc(), ContactDetail.updated_at.desc(), ContactDetail.id.desc()))

    if contact is None:
        contact = ContactDetail(
            farmer_id=user.id if user.role != "buyer" else None,
            buyer_id=user.id if user.role == "buyer" else None,
            preferred_contact_method=body.preferred_contact_method,
            is_primary=body.is_primary,
        )
        db.add(contact)
    else:
        contact.preferred_contact_method = body.preferred_contact_method
        contact.is_primary = body.is_primary

    contact.phone = body.phone or contact.phone
    contact.alternate_phone = body.alternate_phone or contact.alternate_phone
    contact.email = body.email or contact.email
    contact.whatsapp = body.whatsapp or contact.whatsapp
    contact.address_line1 = body.address_line1 or contact.address_line1
    contact.address_line2 = body.address_line2 or contact.address_line2
    contact.city = body.city or contact.city
    contact.district = body.district or contact.district
    contact.state = body.state or contact.state
    contact.pincode = body.pincode or contact.pincode

    if body.is_primary and user.role != "buyer":
        db.execute(
            update(ContactDetail)
            .where(ContactDetail.farmer_id == user.id, ContactDetail.id != contact.id)
            .values(is_primary=False)
        )
    elif body.is_primary and user.role == "buyer":
        db.execute(
            update(ContactDetail)
            .where(ContactDetail.buyer_id == user.id, ContactDetail.id != contact.id)
            .values(is_primary=False)
        )

    db.commit()
    db.refresh(contact)
    return _response({
        "id": contact.id,
        "phone": contact.phone,
        "alternate_phone": contact.alternate_phone,
        "email": contact.email,
        "whatsapp": contact.whatsapp,
        "address_line1": contact.address_line1,
        "address_line2": contact.address_line2,
        "city": contact.city,
        "district": contact.district,
        "state": contact.state,
        "pincode": contact.pincode,
        "preferred_contact_method": contact.preferred_contact_method,
        "is_primary": contact.is_primary,
    }, "Contact details saved")


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
