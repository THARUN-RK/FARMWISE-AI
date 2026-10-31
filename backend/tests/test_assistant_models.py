from sqlalchemy.exc import IntegrityError

from app.core.database import SessionLocal
from app.models.entities import ChatConversation, ChatMessage, Farmer


def test_assistant_history_persists_with_farm_context_opt_in_and_sources():
    db = SessionLocal()
    farmer = Farmer(name="Assistant Test Farmer", phone="+918888888801", password_hash="test-hash")
    db.add(farmer)
    db.flush()
    conversation = ChatConversation(farmer_id=farmer.id, language="kn")
    db.add(conversation)
    db.flush()
    db.add(
        ChatMessage(
            conversation_id=conversation.id,
            role="assistant",
            content="Example response from a test fixture.",
            language="kn",
            source_references=[{"title": "Test source", "url": "https://example.test/guide"}],
            model_name="test-model",
        )
    )
    db.commit()

    saved = db.get(ChatConversation, conversation.id)
    assert saved is not None
    assert saved.include_farm_context is False
    assert saved.language == "kn"
    assert len(saved.messages) == 1
    assert saved.messages[0].source_references == [{"title": "Test source", "url": "https://example.test/guide"}]
    db.close()


def test_assistant_message_role_is_constrained():
    db = SessionLocal()
    farmer = Farmer(name="Assistant Role Test", phone="+918888888802", password_hash="test-hash")
    db.add(farmer)
    db.flush()
    conversation = ChatConversation(farmer_id=farmer.id)
    db.add(conversation)
    db.flush()
    db.add(ChatMessage(conversation_id=conversation.id, role="system", content="must be rejected"))
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
    else:
        raise AssertionError("ChatMessage role must be user or assistant")
    finally:
        db.close()
