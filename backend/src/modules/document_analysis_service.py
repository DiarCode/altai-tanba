from typing import Dict, Any
from datetime import datetime
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

    def __init__(self):
        self.db = Prisma()

    async def analyze_document(self, document_id: str | int) -> Dict[str, Any]:
        """
        Analyze a document for fraud compliance.
        
        Args:
            document_id: The document ID
            
        Returns:
            Analysis results containing fraudSentences, mistakeWords, and documentType
            
        Raises:
            Exception: If any step of the analysis fails
        """
        analysis_id = None
        
        try:
            # Connect to database
            await self.db.connect()
            
            # Step 1: Create initial database record with PROCESSING status
            # Normalize document id to numeric string key
            try:
                doc_int = int(str(document_id).split('/')[-1])
            except ValueError:
                raise Exception(f"Invalid document id: {document_id}")

            analysis = await self.db.documentanalysis.create(
                data={
                    "documentId": str(doc_int),
                    "status": "PROCESSING"
                }
            )
            analysis_id = analysis.id
            
            # Step 2: Resolve S3 prefix from DB and download images from MinIO
            doc = await self.db.sessiondocument.find_unique(where={"id": doc_int})
            if not doc:
                await self._update_failed_status(analysis_id, f"Document not found: {doc_int}")
                raise Exception(f"Document not found: {doc_int}")

            prefix = f"sessions/{doc.sessionId}/documents/{doc.id}"
            try:
                images = await s3_service.download_document_images(prefix)
            except Exception as e:
                error_msg = f"Failed to download images: {str(e)}"
                await self._update_failed_status(analysis_id, error_msg)
                raise Exception(error_msg)
            
            # Step 3: Extract text from images using OCR
            try:
                extracted_text = await ocr_service.extract_text_from_images(images)
            except Exception as e:
                error_msg = f"Failed to extract text from images: {str(e)}"
                await self._update_failed_status(analysis_id, error_msg)
                raise Exception(error_msg)
            
            # Step 4: Analyze text with LLM
            try:
                llm_results = await llm_service.analyze_document_text(extracted_text)
            except Exception as e:
                error_msg = f"Failed to analyze text with LLM: {str(e)}"
                await self._update_failed_status(analysis_id, error_msg)
                raise Exception(error_msg)
            
            # Step 5: Update database with results and COMPLETED status
            updated_analysis = await self.db.documentanalysis.update(
                where={"id": analysis_id},
                data={
                    "status": "COMPLETED",
                    "fraudSentences": llm_results["fraudSentences"],
                    "mistakeWords": llm_results["mistakeWords"],
                    "documentType": llm_results["documentType"],
                    "updatedAt": datetime.utcnow()
                }
            )
            
            # Return the analysis results
            return {
                "fraudSentences": updated_analysis.fraudSentences,
                "mistakeWords": updated_analysis.mistakeWords,
                "documentType": updated_analysis.documentType
            }
            
        except Exception as e:
            # If we haven't already marked as failed, do so now
            if analysis_id:
                try:
                    await self._update_failed_status(analysis_id, str(e))
                except:
                    pass  # Best effort to update status
            raise
            
        finally:
            # Ensure database connection is closed
            await self.db.disconnect()

    async def get_analysis_status(self, document_id: str) -> Dict[str, Any]:
        """
        Get the current analysis status for a document.
        
        Args:
            document_id: The document ID
            
        Returns:
            Analysis status and results if available
        """
        try:
            await self.db.connect()
            
            # Accept either numeric id or legacy prefix; normalize to numeric string
            try:
                key = str(int(document_id.split('/')[-1]))
            except ValueError:
                key = document_id

            analysis = await self.db.documentanalysis.find_unique(where={"documentId": key})
            
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
                    "documentType": analysis.documentType
                })
            elif analysis.status == "FAILED":
                result["errorLog"] = analysis.errorLog
            
            return result
            
        finally:
            await self.db.disconnect()

    async def _update_failed_status(self, analysis_id: str, error_message: str):
        """Update the analysis record with failed status and error log."""
        try:
            await self.db.documentanalysis.update(
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
