from typing import Dict, Any
from datetime import datetime
import time
from prisma import Prisma
from src.core.s3.s3_service import s3_service
from src.core.services.ocr_service import ocr_service
from src.core.services.llm_service import llm_service


class DocumentAnalysisService:
    """
    Main service for document fraud compliance analysis.
    
    Orchestrates the workflow:
    1. Download images from MinIO
    2. Extract text using OCR
    3. Analyze with LLM
    4. Save results to database
    """

    async def analyze_document(self, session_id: int, document_id: str | int) -> Dict[str, Any]:
        """
        Analyze a document for fraud compliance.
        
        Args:
            document_id: The document ID
            
        Returns:
            Analysis results containing fraudSentences, mistakeWords, documentType, and documentSummary
            
        Raises:
            Exception: If any step of the analysis fails
        """
        analysis_id = None
        db = Prisma()
        
        try:
            # Connect to database
            print(f"[DEBUG] Starting database connection...")
            start = time.time()
            await db.connect()
            print(f"[DEBUG] Database connected in {time.time() - start:.2f}s")
            
            # Step 1: Create initial database record with PROCESSING status
            print(f"[DEBUG] Creating analysis record...")
            start = time.time()
            # Normalize document id to numeric string key
            try:
                doc_int = int(str(document_id).split('/')[-1])
            except ValueError:
                raise Exception(f"Invalid document id: {document_id}")

            analysis = await db.documentanalysis.create(
                data={
                    "documentId": str(doc_int),
                    "status": "PROCESSING"
                }
            )
            analysis_id = analysis.id
            print(f"[DEBUG] Analysis record created in {time.time() - start:.2f}s")
            
            # Step 2: Download original PDF from MinIO
            try:
                print(f"[DEBUG] Downloading original PDF from S3...")
                start = time.time()
                pdf_bytes = await s3_service.download_original_pdf(session_id, document_id)
                print(f"[DEBUG] PDF downloaded in {time.time() - start:.2f}s")
            except Exception as e:
                error_msg = f"Failed to download PDF: {str(e)}"
                await self._update_failed_status(db, analysis_id, error_msg)
                raise Exception(error_msg)
            
            # Step 3: Extract text from PDF using OCR
            try:
                print(f"[DEBUG] Extracting text from PDF with OCR...")
                start = time.time()
                extracted_text = await ocr_service.extract_text_from_pdf(pdf_bytes)
                print(f"[DEBUG] Text extracted in {time.time() - start:.2f}s")
            except Exception as e:
                error_msg = f"Failed to extract text from PDF: {str(e)}"
                await self._update_failed_status(db, analysis_id, error_msg)
                raise Exception(error_msg)
            
            # Step 4: Analyze text with LLM
            try:
                print(f"[DEBUG] Analyzing text with LLM...")
                start = time.time()
                llm_results = await llm_service.analyze_document_text(extracted_text)
                print(f"[DEBUG] LLM analysis completed in {time.time() - start:.2f}s")
            except Exception as e:
                error_msg = f"Failed to analyze text with LLM: {str(e)}"
                await self._update_failed_status(db, analysis_id, error_msg)
                raise Exception(error_msg)
            
            # Step 5: Update database with results and COMPLETED status
            updated_analysis = await db.documentanalysis.update(
                where={"id": analysis_id},
                data={
                    "status": "COMPLETED",
                    "fraudSentences": llm_results["fraudSentences"],
                    "mistakeWords": llm_results["mistakeWords"],
                    "documentType": llm_results["documentType"],
                    "documentSummary": llm_results["documentSummary"],
                    "documentText": extracted_text,
                    "updatedAt": datetime.utcnow()
                }
            )
            
            # Return the analysis results
            return {
                "fraudSentences": updated_analysis.fraudSentences,
                "mistakeWords": updated_analysis.mistakeWords,
                "documentType": updated_analysis.documentType,
                "documentSummary": updated_analysis.documentSummary
            }
            
        except Exception as e:
            # If we haven't already marked as failed, do so now
            if analysis_id:
                try:
                    await self._update_failed_status(db, analysis_id, str(e))
                except:
                    pass  # Best effort to update status
            raise
            
        finally:
            # Ensure database connection is closed
            await db.disconnect()

    async def get_analysis_status(self, document_id: str) -> Dict[str, Any]:
        """
        Get the current analysis status for a document.
        
        Args:
            document_id: The document ID
            
        Returns:
            Analysis status and results if available
        """
        db = Prisma()
        try:
            await db.connect()
            
            # Accept either numeric id or legacy prefix; normalize to numeric string
            try:
                key = str(int(document_id.split('/')[-1]))
            except ValueError:
                key = document_id

            analysis = await db.documentanalysis.find_unique(where={"documentId": key})
            
            if not analysis:
                return {
                    "status": "NOT_FOUND",
                    "message": "No analysis found for this document"
                }
            
            result = {
                "status": analysis.status,
                "documentId": analysis.documentId
            }
            
            if analysis.status == "COMPLETED":
                result.update({
                    "fraudSentences": analysis.fraudSentences,
                    "mistakeWords": analysis.mistakeWords,
                    "documentType": analysis.documentType,
                    "documentSummary": analysis.documentSummary
                })
            elif analysis.status == "FAILED":
                result["errorLog"] = analysis.errorLog
            
            return result
            
        finally:
            await db.disconnect()

    async def _update_failed_status(self, db: Prisma, analysis_id: str, error_message: str):
        """Update the analysis record with failed status and error log."""
        try:
            await db.documentanalysis.update(
                where={"id": analysis_id},
                data={
                    "status": "FAILED",
                    "errorLog": error_message,
                    "updatedAt": datetime.utcnow()
                }
            )
        except Exception as e:
            # Log error but don't raise - this is a best-effort update
            print(f"Failed to update analysis status: {str(e)}")


# Singleton instance
document_analysis_service = DocumentAnalysisService()
