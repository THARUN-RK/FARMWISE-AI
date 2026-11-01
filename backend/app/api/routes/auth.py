"""
Authentication routes: register, login, me, profile CRUD.

Logic is identical to the original main.py implementation — only
the file location has changed to follow proper FastAPI router structure.
"""
import hashlib
import logging
import secrets
import smtplib
from datetime import datetime, timedelta
from email.message import EmailMessage
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
from app.models.entities import EmailOTP, Farmer, RefreshToken
from app.services.audit import record_audit_event
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


def _hash_otp(value: str) -> str:
    return hashlib.sha256(value.strip().encode("utf-8")).hexdigest()


def _send_otp_email(to_email: str, code: str) -> None:
    if not settings.smtp_host or not settings.smtp_from_email:
        log.warning("OTP email delivery is not configured; skipping send for %s", to_email)
        return
    message = EmailMessage()
    message["Subject"] = "FarmWise AI: Your verification code"
    message["From"] = settings.smtp_from_email
    message["To"] = to_email
    message.set_content(
        f"Your FarmWise AI verification code is {code}. This code expires in 5 minutes and can only be used once."
    )
    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port or 587, timeout=20) as server:
            if settings.smtp_username and settings.smtp_password:
                server.starttls()
                server.login(settings.smtp_username, settings.smtp_password)
            server.send_message(message)
    except (smtplib.SMTPException, OSError) as exc:
        log.exception("Failed to send OTP email to %s", to_email)
        raise HTTPException(503, "Unable to send the OTP email right now. Please try again.") from exc


def _create_otp_record(db: Session, user: Farmer, purpose: str = "google_login") -> str:
    code = f"{secrets.randbelow(1_000_000):06d}"
    otp_record = EmailOTP(
        farmer_id=user.id,
        purpose=purpose,
        code_hash=_hash_otp(code),
        expires_at=datetime.utcnow() + timedelta(minutes=settings.otp_lifetime_minutes),
    )
    db.add(otp_record)
    db.flush()
    return code


def _send_google_otp(db: Session, user: Farmer) -> None:
    if not user.email:
        raise HTTPException(400, "A verified email address is required before OTP verification")
    last_recent = db.scalar(
        select(EmailOTP)
        .where(EmailOTP.farmer_id == user.id, EmailOTP.purpose == "google_login")
        .order_by(EmailOTP.created_at.desc())
    )
    if last_recent and last_recent.created_at + timedelta(seconds=settings.otp_resend_seconds) > datetime.utcnow():
        raise HTTPException(429, "Please wait a moment before requesting a new OTP")
    code = _create_otp_record(db, user)
    _send_otp_email(user.email, code)


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
    """Verify a Google ID token, send a secure OTP to the user email, and require verification before session creation."""
    claims = verify_google_credential(body.credential)
    email = str(claims["email"]).strip().lower()
    name = str(claims.get("name") or email.split("@", 1)[0]).strip()[:120]
    google_id = str(claims.get("sub") or "")
    profile_picture = claims.get("picture")

    user = db.scalar(select(Farmer).where(func.lower(Farmer.email) == email))
    if not user:
        unique_phone = f"+1555{secrets.token_hex(5)}"[:20]
        user = Farmer(
            name=name,
            phone=unique_phone,
            mobile_number=unique_phone,
            email=email,
            google_id=google_id or None,
            profile_picture=profile_picture,
            password_hash=hash_password(secrets.token_urlsafe(48)),
            role="farmer",
            email_verified=False,
            account_status="pending_otp",
        )
        db.add(user)
        db.flush()
    else:
        if google_id:
            user.google_id = google_id
        if profile_picture:
            user.profile_picture = profile_picture
        if user.name != name:
            user.name = name
        if user.email_verified is False and not user.phone:
            user.phone = f"+1555{secrets.token_hex(5)}"[:20]
            user.mobile_number = user.phone
        user.account_status = user.account_status if user.account_status else "active"
        db.flush()

    try:
        _send_google_otp(db, user)
    except HTTPException:
        raise
    db.commit()
    log.info("google_otp_sent user_id=%s email=%s", user.id, email)
    return _response(
        {
            "requires_otp": True,
            "phone_required": False,
            "email": email,
            "name": user.name,
            "message": "Verification code sent to your email.",
        },
        "Google account verified. Enter the OTP sent to your email.",
    )


@router.post("/google/otp/verify")
@limiter.limit("20/minute")
def verify_google_otp(request: Request, body: dict, response: Response, db: Session = Depends(get_db)):
    """Validate a Google-sign-in OTP and create a refresh-backed authenticated session."""
    email = str(body.get("email", "")).strip().lower()
    otp = str(body.get("otp", "")).strip()
    if not email or not otp:
        raise HTTPException(400, "Email and OTP are required")

    user = db.scalar(select(Farmer).where(func.lower(Farmer.email) == email))
    if not user:
        raise HTTPException(401, "Google sign-in session is invalid or expired")

    otp_record = db.scalar(
        select(EmailOTP)
        .where(EmailOTP.farmer_id == user.id, EmailOTP.purpose == "google_login")
        .order_by(EmailOTP.created_at.desc())
    )
    if not otp_record or otp_record.used_at is not None:
        raise HTTPException(401, "The verification code has already been used or is no longer valid")
    if otp_record.expires_at <= datetime.utcnow():
        otp_record.used_at = datetime.utcnow()
        db.commit()
        raise HTTPException(401, "The verification code has expired")

    if otp_record.attempts >= settings.otp_max_attempts:
        otp_record.used_at = datetime.utcnow()
        db.commit()
        raise HTTPException(401, "Too many incorrect attempts. Request a new verification code.")

    if _hash_otp(otp) != otp_record.code_hash:
        otp_record.attempts += 1
        db.commit()
        remaining_attempts = max(settings.otp_max_attempts - otp_record.attempts, 0)
        if remaining_attempts <= 0:
            raise HTTPException(401, "Too many incorrect attempts. Request a new verification code.")
        raise HTTPException(401, f"Incorrect verification code. {remaining_attempts} attempts remaining")

    otp_record.used_at = datetime.utcnow()
    user.email_verified = True
    user.account_status = "active"
    user.last_login = datetime.utcnow()
    access_token = _issue_session(db, user, response, "auth.google_otp_verify")
    db.commit()
    log.info("google_otp_verified user_id=%s", user.id)
    return _response({
        "access_token": access_token,
        "token_type": "bearer",
        "user": CurrentUser.model_validate(user),
    }, "Google authentication verified")


@router.post("/google/otp/resend")
@limiter.limit("5/minute")
def resend_google_otp(request: Request, body: dict, db: Session = Depends(get_db), response: Response = None):
    """Send another one-time verification code to the same Gmail account."""
    email = str(body.get("email", "")).strip().lower()
    if not email:
        raise HTTPException(400, "Email is required")
    user = db.scalar(select(Farmer).where(func.lower(Farmer.email) == email))
    if not user:
        raise HTTPException(404, "No active FarmWise account was found for this email")
    _send_google_otp(db, user)
    db.commit()
    return _response({"email": email}, "A new verification code has been sent")


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
