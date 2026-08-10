import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.conversation import Conversation, Message

TITLE_MAX_LENGTH = 60


def create_conversation(db: Session, first_message: str) -> Conversation:
    title = first_message.strip()[:TITLE_MAX_LENGTH] or "New conversation"
    conversation = Conversation(title=title)
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation


def get_conversation(db: Session, conversation_id: uuid.UUID) -> Conversation | None:
    stmt = (
        select(Conversation)
        .options(selectinload(Conversation.messages))
        .where(Conversation.id == conversation_id)
    )
    return db.scalars(stmt).first()


def list_conversations(db: Session) -> list[Conversation]:
    stmt = select(Conversation).order_by(Conversation.created_at.desc())
    return list(db.scalars(stmt))


def add_message(
    db: Session, conversation_id: uuid.UUID, role: str, content: str, sources: list[str] | None = None
) -> Message:
    message = Message(conversation_id=conversation_id, role=role, content=content, sources=sources)
    db.add(message)
    db.commit()
    db.refresh(message)
    return message
