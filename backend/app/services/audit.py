"""Write compact audit events without storing credentials or user message bodies."""
from sqlalchemy.orm import Session

from app.models.entities import AuditLog

_SENSITIVE_KEYS = {
    "authorization",
    "content",
    "email",
    "message",
    "password",
    "phone",
    "prompt",
    "refresh_token",
    "token",
}


def _sanitize(value):
    if isinstance(value, dict):
        return {
            key: _sanitize(item)
            for key, item in value.items()
            if str(key).lower() not in _SENSITIVE_KEYS
        }
    if isinstance(value, list):
        return [_sanitize(item) for item in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def record_audit_event(
    db: Session,
    *,
    actor_user_id: int | None,
    action: str,
    resource_type: str,
    resource_id: int | str | None = None,
    outcome: str = "success",
    details: dict | None = None,
) -> AuditLog:
    """Add a sanitized event to the caller's current transaction."""
    safe_details = _sanitize(details) if details else None
    event = AuditLog(
        actor_user_id=actor_user_id,
        action=action,
        resource_type=resource_type,
        resource_id=str(resource_id) if resource_id is not None else None,
        outcome=outcome,
        details=safe_details,
    )
    db.add(event)
    return event
