from __future__ import annotations

from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class DetectionOut(BaseModel):
    category: str
    x: float
    y: float
    width: float
    height: float
    area: float
    confidence: float


class PageArtifacts(BaseModel):
    pageIndex: int
    imageUrl: str
    labeledImageUrl: Optional[str] = None


class DocumentArtifacts(BaseModel):
    originalPdfUrl: str
    labeledPdfUrl: Optional[str] = None
    pages: List[PageArtifacts] = Field(default_factory=list)


class LabelsPositionPayload(BaseModel):
    artifacts: DocumentArtifacts
    # Use string keys to ensure GraphQL-safe JSON object keys when persisting
    detections: Dict[str, List[DetectionOut]]


# Constants to avoid stringly-typed access
ARTIFACTS = "artifacts"
ORIGINAL_PDF_URL = "originalPdfUrl"
LABELED_PDF_URL = "labeledPdfUrl"
PAGES = "pages"
PAGE_INDEX = "pageIndex"
IMAGE_URL = "imageUrl"
LABELED_IMAGE_URL = "labeledImageUrl"
