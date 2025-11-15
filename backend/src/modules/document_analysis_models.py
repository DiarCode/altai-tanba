from pydantic import BaseModel, Field
from typing import List
from enum import Enum


class DocumentAnalysisStatus(str, Enum):
    """Document analysis status enum."""
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    NOT_FOUND = "NOT_FOUND"


class AnalyzeDocumentRequest(BaseModel):
    """Request model for document analysis."""
    documentId: str = Field(..., description="The ID of the document to analyze")


class AnalyzeDocumentResponse(BaseModel):
    """Response model for document analysis."""
    fraudSentences: List[str] = Field(..., description="List of fraudulent sentences detected")
    mistakeWords: List[str] = Field(..., description="List of misspelled words detected")
    documentType: str = Field(..., description="Type of the document (e.g., Договор)")


class DocumentAnalysisStatusResponse(BaseModel):
    """Response model for document analysis status."""
    status: str = Field(..., description="Current status of the analysis")
    documentId: str = Field(..., description="The document ID")
    fraudSentences: List[str] | None = Field(None, description="List of fraudulent sentences (if completed)")
    mistakeWords: List[str] | None = Field(None, description="List of misspelled words (if completed)")
    documentType: str | None = Field(None, description="Type of the document (if completed)")
    errorLog: str | None = Field(None, description="Error message (if failed)")
    message: str | None = Field(None, description="Additional information")
