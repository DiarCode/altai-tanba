from fastapi import APIRouter, HTTPException, BackgroundTasks
from src.modules.document_analysis.document_analysis_models import (
    AnalyzeDocumentRequest,
    AnalyzeDocumentResponse,
    DocumentAnalysisStatusResponse
)
from src.modules.document_analysis.document_analysis_service import document_analysis_service


router = APIRouter(prefix="/document-analysis", tags=["Document Analysis"])


@router.post("/analyze", response_model=AnalyzeDocumentResponse, status_code=200)
async def analyze_document(request: AnalyzeDocumentRequest):
    """
    Analyze a document for fraud compliance.
    
    This endpoint:
    1. Downloads images from MinIO (documentId/pages/*.png)
    2. Extracts text using OCR
    3. Analyzes with LLM for fraud detection, spelling mistakes, and document type
    4. Saves results to database
    
    The analysis runs synchronously and returns results when complete.
    Status is tracked in the database (PROCESSING -> COMPLETED/FAILED).
    """
    try:
        result = await document_analysis_service.analyze_document(request.documentId)
        return AnalyzeDocumentResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze-async", status_code=202)
async def analyze_document_async(request: AnalyzeDocumentRequest, background_tasks: BackgroundTasks):
    """
    Start document analysis in the background.
    
    This endpoint immediately returns a 202 Accepted status.
    Use the GET /document-analysis/status/{documentId} endpoint to check progress.
    """
    background_tasks.add_task(document_analysis_service.analyze_document, request.documentId)
    return {
        "message": "Analysis started",
        "documentId": request.documentId,
        "status": "PROCESSING"
    }


@router.get("/status/{document_id:path}", response_model=DocumentAnalysisStatusResponse)
async def get_analysis_status(document_id: str):
    """
    Get the current analysis status for a document.
    
    Returns:
    - PROCESSING: Analysis is in progress
    - COMPLETED: Analysis finished successfully (includes results)
    - FAILED: Analysis failed (includes error log)
    - NOT_FOUND: No analysis found for this document
    """
    try:
        result = await document_analysis_service.get_analysis_status(document_id)
        return DocumentAnalysisStatusResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
