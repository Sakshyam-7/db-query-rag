"""
Chat routes.

Uses the chat orchestration service: generates scoped SQL, runs it
read-only, and asks the LLM to phrase the final answer.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_readonly_db
from app.dependencies import get_current_user
from app.llm.factory import get_llm_provider
from app.models.user import User
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat import answer_chat_message

router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
)


@router.post(
    "",
    response_model=ChatResponse,
)
async def chat(
    payload: ChatRequest,
    current_user: User = Depends(get_current_user),
    readonly_db: Session = Depends(get_readonly_db),
) -> ChatResponse:
    llm = get_llm_provider()
    reply = await answer_chat_message(
        message=payload.message,
        current_user=current_user,
        readonly_db=readonly_db,
        llm=llm,
    )
    return ChatResponse(reply=reply)