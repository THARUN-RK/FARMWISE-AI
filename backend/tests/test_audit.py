from app.core.database import SessionLocal
from app.models.entities import AuditLog, Farmer
from app.services.audit import record_audit_event


def test_audit_events_persist_and_remove_sensitive_details():
    with SessionLocal() as db:
        farmer = Farmer(name="Audit Test Farmer", phone="+918888888803", password_hash="test-hash")
        db.add(farmer)
        db.flush()
        event = record_audit_event(
            db,
            actor_user_id=farmer.id,
            action="assistant.message",
            resource_type="chat_conversation",
            resource_id=42,
            details={
                "language": "kn",
                "message": "private farmer question",
                "nested": {"token": "secret", "source_count": 2},
            },
        )
        db.commit()
        db.refresh(event)
        saved = db.get(AuditLog, event.id)
        assert saved is not None
        assert saved.actor_user_id == farmer.id
        assert saved.resource_id == "42"
        assert saved.details == {"language": "kn", "nested": {"source_count": 2}}
