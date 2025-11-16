from fastapi import APIRouter, Request
from pydantic import BaseModel
from .chat_service import ChatResponse, chat_service

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatQueryRequest(BaseModel):
    message: str


@router.post("/{document_id}", response_model=ChatResponse)
async def chat(document_id: str, body: ChatQueryRequest, request: Request) -> ChatResponse:
    """Generate an answer for a single user message using DB-backed context.

    - Loads analysis results + verification signals for the given document id
    - Uses the request's Accept-Language as target language
    - Sends a single prompt to the Modal LLM endpoint
    """
    accept_language = request.headers.get("accept-language")
    return await chat_service.generate_document_chat(document_id, body.message, accept_language)

__all__ = ["router"]
