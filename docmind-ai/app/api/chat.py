import logging
import uuid

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse, StreamingResponse
from sqlalchemy.orm import Session

from app.core.rate_limit import rate_limit
from app.core.templates import templates
from app.db.session import get_db
from app.services.conversation_service import (
    add_message,
    create_conversation,
    get_conversation,
    list_conversations,
)
from app.services.llm_service import stream_answer
from app.services.rag_service import NO_CONTEXT_ANSWER
from app.services.search_service import semantic_search
from app.utils.sse import format_sse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/chat")
def chat_page(request: Request):
    return templates.TemplateResponse(
        request, "chat.html", {"active": "chat", "conversation": None, "messages": []}
    )


@router.get("/chat/stream", dependencies=[Depends(rate_limit)])
def stream_chat(conversation_id: uuid.UUID, message: str, db: Session = Depends(get_db)):
    def event_stream():
        try:
            chunks = semantic_search(db, message)
        except Exception:
            logger.exception("Semantic search failed for conversation %s", conversation_id)
            error_message = "Something went wrong generating a response. Please try again."
            add_message(db, conversation_id, "assistant", error_message, sources=None)
            yield format_sse(error_message)
            yield format_sse("done", event="done")
            return

        if not chunks:
            add_message(db, conversation_id, "assistant", NO_CONTEXT_ANSWER, sources=None)
            yield format_sse(NO_CONTEXT_ANSWER)
            yield format_sse("done", event="done")
            return

        full_answer = ""
        try:
            for delta in stream_answer(message, [chunk.content for chunk in chunks]):
                full_answer += delta
                yield format_sse(delta)
        except Exception:
            logger.exception("Streaming generation failed for conversation %s", conversation_id)
            if not full_answer:
                full_answer = "Something went wrong generating a response. Please try again."
                yield format_sse(full_answer)

        source_filenames = sorted({chunk.document.filename for chunk in chunks})
        add_message(db, conversation_id, "assistant", full_answer, sources=source_filenames)

        sources_html = templates.env.get_template("partials/sources_fragment.html").render(
            filenames=source_filenames
        )
        yield format_sse(sources_html, event="sources")
        yield format_sse("done", event="done")

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.get("/chat/{conversation_id}")
def reopen_chat(conversation_id: uuid.UUID, request: Request, db: Session = Depends(get_db)):
    conversation = get_conversation(db, conversation_id)
    if conversation is None:
        return RedirectResponse(url="/chat", status_code=303)
    return templates.TemplateResponse(
        request,
        "chat.html",
        {"active": "chat", "conversation": conversation, "messages": conversation.messages},
    )


@router.get("/history")
def history_page(request: Request, db: Session = Depends(get_db)):
    conversations = list_conversations(db)
    return templates.TemplateResponse(
        request, "history.html", {"active": "history", "conversations": conversations}
    )


@router.post("/chat/message", dependencies=[Depends(rate_limit)])
def send_message(
    request: Request,
    db: Session = Depends(get_db),
    message: str = Form(...),
    conversation_id: str = Form(""),
):
    conversation = get_conversation(db, uuid.UUID(conversation_id)) if conversation_id else None
    if conversation is None:
        conversation = create_conversation(db, message)

    add_message(db, conversation.id, "user", message)

    return templates.TemplateResponse(
        request,
        "partials/chat_stream_start.html",
        {"query": message, "conversation_id": str(conversation.id)},
    )
