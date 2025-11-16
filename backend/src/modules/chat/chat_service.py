from __future__ import annotations

from typing import List, Literal, Optional
import httpx
from pydantic import BaseModel, Field
from fastapi import HTTPException

from src.core.config.settings import settings
from src.core.db.prisma import get_db


class ChatMessage(BaseModel):
	role: Literal["system", "user", "assistant"]
	content: str


class ChatContext(BaseModel):
	document_summary: str = Field(..., description="Brief summary of the document content")
	document_type: str = Field(..., description="Type of the document, e.g. contract")
	fraud_sentences: List[str] = Field(default_factory=list, description="Potentially fraudulent sentences")
	mistake_words: List[str] = Field(default_factory=list, description="Misspelled words")
	has_stamp: bool = Field(False, description="Whether a stamp was detected")
	has_signature: bool = Field(False, description="Whether a signature was detected")


class ChatRequest(BaseModel):
	messages: List[ChatMessage]
	context: ChatContext
	target_language: Optional[str] = Field(None, description="If provided, answer in this language (e.g. 'ru', 'en')")


class ChatResponse(BaseModel):
	answer: str
	model: Optional[str] = None
	prompt_tokens: Optional[int] = None
	completion_tokens: Optional[int] = None
	total_tokens: Optional[int] = None


class ChatService:
	"""Service generating contextual chat responses over analyzed document data.

	It composes a system prompt embedding:
	  - Document summary & type
	  - Fraudulent sentences & mistakes
	  - Presence of stamp / signature (verification signals)

	The service is stateless: conversation history is passed in the request.
	"""

	def __init__(self, llm_endpoint: str, use_stub: bool = False):
		self._endpoint = llm_endpoint.rstrip("/")
		self._use_stub = use_stub

	async def generate_response(self, req: ChatRequest) -> ChatResponse:
		system_prompt = self._build_system_prompt(req.context, req.target_language)
		# Prepend/replace any existing system message
		messages_payload: List[dict] = []
		messages_payload.append({"role": "system", "content": system_prompt})
		for m in req.messages:
			if m.role == "system":
				# Ignore user-provided system (we replaced with contextual one)
				continue
			messages_payload.append({"role": m.role, "content": m.content})

		if self._use_stub:
			# Simple deterministic stub for local development
			answer = self._stub_answer(messages_payload)
			return ChatResponse(answer=answer, model="stub")

		try:
			async with httpx.AsyncClient(timeout=30) as client:
				response = await client.post(
					f"{self._endpoint}",
					json={
						"messages": messages_payload,
						"stream": False,
						"temperature": 0.2,
					},
				)
		except httpx.RequestError as e:
			raise HTTPException(status_code=502, detail=f"LLM endpoint unreachable: {e}")

		if response.status_code >= 400:
			raise HTTPException(status_code=502, detail=f"LLM error: {response.text}")

		data = response.json()
		# Attempt flexible extraction; adapt if endpoint schema differs
		answer = (
			data.get("answer")
			or data.get("content")
			or data.get("message", {}).get("content")
			or data.get("choices", [{}])[0].get("message", {}).get("content")
			or "(No answer returned)"
		)

		usage = data.get("usage", {})
		return ChatResponse(
			answer=answer.strip(),
			model=data.get("model"),
			prompt_tokens=usage.get("prompt_tokens"),
			completion_tokens=usage.get("completion_tokens"),
			total_tokens=usage.get("total_tokens"),
		)

	async def generate_document_chat(
		self,
		document_id: str | int,
		message: str,
		accept_language: Optional[str] = None,
	) -> ChatResponse:
		"""Generate answer for a single message using DB-backed context.

		- Loads analysis and verification signals from DB by document id
		- Builds single "prompt" string and calls Modal endpoint at /chat
		"""
		# TODO: Restore DB-backed context when analysis pipeline is ready
		# ctx = await self._load_context_from_db(document_id)
		# For now, use placeholder context without DB
		ctx = ChatContext(
			document_summary="",
			document_type="",
			fraud_sentences=[],
			mistake_words=[],
			has_stamp=False,
			has_signature=False,
		)
		target_lang = _pick_language(accept_language)
		system_prompt = self._build_system_prompt(ctx, target_lang)
		prompt = f"{system_prompt}\n\nUser question: {message.strip()}"

		if self._use_stub:
			answer = f"(stub) {ctx.document_type or 'document'} | sig={ctx.has_signature} stamp={ctx.has_stamp} -> {message[:200]}"
			return ChatResponse(answer=answer, model="stub")

		# Align with existing usage patterns (llm_service.py): POST {base}/chat {prompt: str}
		try:
			timeout_cfg = httpx.Timeout(timeout=60.0, connect=10.0, read=60.0, write=10.0)
			async with httpx.AsyncClient(timeout=timeout_cfg) as client:
				resp = await client.post(
					f"{self._endpoint}/chat",
					json={
						"prompt": prompt,
						"max_tokens": 1024,
						"temperature": 0.4,
					},
				)
				resp.raise_for_status()
		except httpx.RequestError as e:
			raise HTTPException(status_code=502, detail=f"LLM endpoint unreachable: {e}")
		except httpx.HTTPStatusError as e:
			raise HTTPException(status_code=502, detail=f"LLM error: {e.response.text}")

		data = resp.json()
		answer = data.get("response") or data.get("answer") or "(No answer returned)"
		return ChatResponse(answer=answer.strip(), model=data.get("model"))

	async def _load_context_from_db(self, document_id: str | int) -> ChatContext:
		# Normalize id like other services do
		try:
			doc_int = int(str(document_id).split("/")[-1])
		except ValueError:
			raise HTTPException(status_code=400, detail=f"Invalid document id: {document_id}")

		db = await get_db()

		# Verification signals from session_documents
		session_doc = await db.sessiondocument.find_unique(where={"id": doc_int})
		if not session_doc:
			raise HTTPException(status_code=404, detail=f"Document not found: {doc_int}")

		# Analysis results from document_analyses by documentId (string)
		analysis = await db.documentanalysis.find_unique(where={"documentId": str(doc_int)})
		if not analysis or analysis.status != "COMPLETED":
			raise HTTPException(status_code=409, detail="Document analysis not ready")

		return ChatContext(
			document_summary=analysis.documentSummary or "",
			document_type=analysis.documentType or "",
			fraud_sentences=analysis.fraudSentences or [],
			mistake_words=analysis.mistakeWords or [],
			has_stamp=bool(session_doc.hasStamp),
			has_signature=bool(session_doc.hasSignature),
		)

	def _build_system_prompt(self, ctx: ChatContext, target_language: Optional[str]) -> str:
		lines: List[str] = []
		lines.append("You are an expert assistant helping with document review.")
		if target_language:
			lines.append(f"Respond in language: {target_language}.")
		lines.append(f"Document type: {ctx.document_type}.")
		lines.append("Document summary:")
		lines.append(ctx.document_summary.strip())
		lines.append("Verification signals:")
		lines.append(f" - Signature present: {'yes' if ctx.has_signature else 'no'}")
		lines.append(f" - Stamp present: {'yes' if ctx.has_stamp else 'no'}")
		if ctx.fraud_sentences:
			lines.append("Potential fraud sentences:")
			for s in ctx.fraud_sentences[:10]:
				lines.append(f" - {s}")
		if ctx.mistake_words:
			lines.append("Detected misspelled words:")
			lines.append(", ".join(ctx.mistake_words[:50]))
		lines.append(
			"Use the above context to answer user questions, explain risks, suggest corrections, and provide concise, actionable guidance."
		)
		lines.append("Answers should be clear and to the point. Maximum 200 characters.")
		return "\n".join(lines)

	def _stub_answer(self, messages: List[dict]) -> str:
		# Very naive echo for development
		last_user = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
		return f"(stub) Context processed. Last user message: {last_user[:200]}"


chat_service = ChatService(settings.MODAL_LLM_ENDPOINT, use_stub=settings.USE_STUB_ADAPTER)


def _pick_language(accept_language_header: Optional[str]) -> Optional[str]:
	"""Pick the primary language code from Accept-Language header.

	Examples:
	  - "ru,en;q=0.9" -> "ru"
	  - "en-US,en;q=0.5" -> "en"
	"""
	if not accept_language_header:
		return None
	raw = accept_language_header.split(",")[0].strip()
	if not raw:
		return None
	# reduce regional form like en-US to en
	return raw.split("-")[0].lower()

__all__ = [
	"ChatMessage",
	"ChatContext",
	"ChatRequest",
	"ChatResponse",
	"ChatService",
	"chat_service",
]

