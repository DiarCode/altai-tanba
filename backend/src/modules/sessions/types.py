from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


def to_camel(s: str) -> str:
	parts = s.split("_")
	return parts[0] + "".join(p.capitalize() for p in parts[1:])


class SessionDTO(BaseModel):
	model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

	id: str
	total_documents: int
	created_at: datetime
	updated_at: datetime


# SessionStats intentionally omitted; frontend will compute stats

class SessionDocumentStatus(str, Enum):
	PENDING = "PENDING"
	SUCCESSFUL = "SUCCESSFUL"
	FAILED = "FAILED"


class SessionDocumentVerification(BaseModel):
	model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

	has_qr: bool = Field(..., alias="hasQR")
	has_stamp: bool
	has_signature: bool


class SessionDocumentDTO(BaseModel):
	model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

	id: str
	document_url: str
	original_name: str
	status: SessionDocumentStatus
	created_at: datetime
	updated_at: datetime
	verification: Optional[SessionDocumentVerification] = None


class SessionDocumentDetailsDto(SessionDocumentDTO):
	model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

	labeled_document_url: Optional[str] = None
	labels_position: Optional[dict] = None

__all__ = [
	"SessionDTO",
	"SessionDocumentStatus",
	"SessionDocumentVerification",
	"SessionDocumentDTO",
	"SessionDocumentDetailsDto",
    # keep exports stable
]

