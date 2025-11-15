import httpx
from typing import List, Dict, Any
from src.core.config.settings import settings


class LLMService:
    """Service for interacting with Modal Labs LLM endpoint."""

    def __init__(self):
        # Modal Labs endpoint URL (you'll need to add this to settings)
        self.base_url = settings.MODAL_LLM_ENDPOINT
        self.timeout = 120.0  # 2 minutes timeout for LLM requests

    async def analyze_document_text(self, text: str) -> Dict[str, Any]:
        """
        Analyze document text using Modal Labs LLM endpoint.
        
        This sends three separate requests to analyze:
        1. Fraud detection
        2. Spelling mistakes
        3. Document type classification
        
        Args:
            text: The extracted text from the document
            
        Returns:
            Dictionary containing fraudSentences, mistakeWords, and documentType
            
        Raises:
            Exception: If LLM analysis fails
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Request 1: Fraud detection
                fraud_result = await self._detect_fraud(client, text)
                
                # Request 2: Spelling mistakes
                mistakes_result = await self._detect_mistakes(client, text)
                
                # Request 3: Document type
                doc_type_result = await self._classify_document(client, text)
                
                return {
                    "fraudSentences": fraud_result,
                    "mistakeWords": mistakes_result,
                    "documentType": doc_type_result
                }
                
        except Exception as e:
            raise Exception(f"LLM analysis failed: {str(e)}")

    async def _detect_fraud(self, client: httpx.AsyncClient, text: str) -> List[str]:
        """Detect fraudulent sentences in the text."""
        prompt = f"""INSTRUCTIONS: You are an assistant that detects fraudulent or suspicious sentences in documents. You should identify sentences that contain fraudulent content, scams, illegal requests, or suspicious clauses. Return ONLY the fraudulent sentences separated by semicolons (;). If no fraud is detected, return an empty string.

TEXT FOR ANALYSIS:
{text}

RESPONSE FORMAT: sentence1; sentence2; sentence3"""

        try:
            response = await client.post(
                f"{self.base_url}/chat",
                json={
                    "prompt": prompt,
                    "max_tokens": 2048,
                    "temperature": 0.3
                }
            )
            response.raise_for_status()
            
            result = response.json()
            fraud_text = result.get("response", "").strip()
            
            # Parse the semicolon-separated list
            if not fraud_text:
                return []
            
            sentences = [s.strip() for s in fraud_text.split(";") if s.strip()]
            return sentences
            
        except Exception as e:
            raise Exception(f"Fraud detection failed: {str(e)}")

    async def _detect_mistakes(self, client: httpx.AsyncClient, text: str) -> List[str]:
        """Detect spelling mistakes in the text."""
        prompt = f"""INSTRUCTIONS: You are an assistant that determines spelling problems in the text and should send back list of words that has problems. Return ONLY the misspelled words separated by semicolons (;). If no mistakes are found, return an empty string.

EXAMPLE:
Input: "Ппривет, меня зовут Алексей, а вас как завут?"
Response: "Ппривет; завут"

TEXT FOR ANALYSIS:
{text}

RESPONSE FORMAT: word1; word2; word3"""

        try:
            response = await client.post(
                f"{self.base_url}/chat",
                json={
                    "prompt": prompt,
                    "max_tokens": 2048,
                    "temperature": 0.3
                }
            )
            response.raise_for_status()
            
            result = response.json()
            mistakes_text = result.get("response", "").strip()
            
            # Parse the semicolon-separated list
            if not mistakes_text:
                return []
            
            words = [w.strip() for w in mistakes_text.split(";") if w.strip()]
            return words
            
        except Exception as e:
            raise Exception(f"Mistake detection failed: {str(e)}")

    async def _classify_document(self, client: httpx.AsyncClient, text: str) -> str:
        """Classify the document type."""
        prompt = f"""INSTRUCTIONS: You are an assistant that determines the type of document. Analyze the following document and classify it into one of these categories: Договор, Соглашение, Акт, Спецификация, or another appropriate document type. Return ONLY the document type name.

DOCUMENT:
{text}

RESPONSE FORMAT: Single word or short phrase representing the document type (e.g., "Договор")"""

        try:
            response = await client.post(
                f"{self.base_url}/chat",
                json={
                    "prompt": prompt,
                    "max_tokens": 512,
                    "temperature": 0.3
                }
            )
            response.raise_for_status()
            
            result = response.json()
            doc_type = result.get("response", "").strip()
            
            return doc_type if doc_type else "Неизвестный тип"
            
        except Exception as e:
            raise Exception(f"Document classification failed: {str(e)}")


# Singleton instance
llm_service = LLMService()
