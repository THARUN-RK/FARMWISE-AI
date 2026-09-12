"""
Shared FastAPI dependency injectors.

These replace the inline `current_user` and `farmer_only` functions
that were previously defined in main.py. Import from here in every router.
"""
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_token
from app.models.entities import Farmer

oauth2 = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def current_user(token: str = Depends(oauth2), db: Session = Depends(get_db)) -> Farmer:
    """Return the authenticated Farmer, or raise 401."""
    try:
        payload = decode_token(token)
        user = db.get(Farmer, int(payload["sub"]))
    except (ValueError, KeyError, TypeError):
        user = None
    if not user:
        raise HTTPException(
            status_code=401,
            detail={"code": "UNAUTHORIZED", "message": "Invalid or expired token"},
        )
    return user


def farmer_only(user: Farmer = Depends(current_user)) -> Farmer:
    """Require farmer or admin role, raise 403 otherwise."""
    if user.role not in ("farmer", "admin"):
        raise HTTPException(status_code=403, detail="Farmer access required")
    return user
