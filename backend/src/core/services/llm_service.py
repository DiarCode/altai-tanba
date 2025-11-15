import httpx
import time
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
        
        This sends four separate requests to analyze:
        1. Fraud detection
        2. Spelling mistakes
        3. Document type classification
        4. Document summary
        
        Args:
            text: The extracted text from the document
            
        Returns:
            Dictionary containing fraudSentences, mistakeWords, documentType, and documentSummary
            
        Raises:
            Exception: If LLM analysis fails
        """
        try:
            print(f"[DEBUG] Creating httpx client with timeout={self.timeout}s...")
            start = time.time()
            # Configure httpx with explicit timeouts and connection settings
            timeout_config = httpx.Timeout(
                timeout=self.timeout,
                connect=10.0,  # 10 seconds for connection
                read=self.timeout,
                write=10.0,
                pool=5.0
            )
            async with httpx.AsyncClient(timeout=timeout_config) as client:
                print(f"[DEBUG] httpx client created in {time.time() - start:.2f}s")
                
                # Request 1: Fraud detection
                fraud_result = await self._detect_fraud(client, text)
                
                # Request 2: Spelling mistakes
                mistakes_result = await self._detect_mistakes(client, text)
                
                # Request 3: Document type
                doc_type_result = await self._classify_document(client, text)
                
                # Request 4: Document summary
                summary_result = await self._generate_summary(client, text)
                
                return {
                    "fraudSentences": fraud_result,
                    "mistakeWords": mistakes_result,
                    "documentType": doc_type_result,
                    "documentSummary": summary_result
                }
                
        except Exception as e:
            raise Exception(f"LLM analysis failed: {str(e)}")

    async def _detect_fraud(self, client: httpx.AsyncClient, text: str) -> List[str]:
        """Detect fraudulent sentences in the text."""
        prompt = f"""INSTRUCTIONS: You are an assistant that detects fraudulent or suspicious content in documents. Analyze the text and identify any fraudulent content, scams, illegal requests, or suspicious clauses. Instead of returning the exact sentences from the document, return brief summary descriptions of the fraud found. Return ONLY the fraud summaries separated by semicolons (;). If no fraud is detected, return an empty string.

EXAMPLE:
Input: "Вы должны заплатить 10000 долларов просто так без причины"
Response: "В тексте документа замечен неправомерный перевод больших сумм"

TEXT FOR ANALYSIS:
{text}

RESPONSE FORMAT: fraud_summary1; fraud_summary2; fraud_summary3"""

        try:
            print(f"[DEBUG] Sending fraud detection request to {self.base_url}/chat...")
            start = time.time()
            response = await client.post(
                f"{self.base_url}/chat",
                json={
                    "prompt": prompt,
                    "max_tokens": 2048,
                    "temperature": 0.3
                }
            )
            print(f"[DEBUG] Fraud detection request completed in {time.time() - start:.2f}s")
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
        """Generate improvement suggestions for the document."""
        prompt = f"""ИНСТРУКЦИЯ: Вы помощник, который анализирует документы и предлагает улучшения. Проанализируйте следующий текст и дайте ровно 3 конкретные рекомендации по улучшению документа. Каждая рекомендация должна быть одним предложением на русском языке.

Опишите ОБЩИЕ проблемы документа, такие как:
- Качество распознавания текста (если есть ошибки OCR)
- Орфографические и грамматические ошибки (в целом)
- Проблемы со структурой документа
- Неясные формулировки
- Полнота информации
- Профессиональное оформление

ВАЖНО: НЕ нумеруйте рекомендации. НЕ пишите "Рекомендация 1", "Рекомендация 2" и т.д. НЕ перечисляйте конкретные ошибки. Верните ТОЛЬКО сами рекомендации, разделенные точкой с запятой (;).

ПРИМЕР ПРАВИЛЬНОГО ОТВЕТА:
Необходимо улучшить качество распознавания текста; Рекомендуется провести корректуру для устранения орфографических ошибок; Следует упорядочить структуру документа для лучшей читаемости

ТЕКСТ ДЛЯ АНАЛИЗА:
{text}

ОТВЕТ (только рекомендации через точку с запятой):"""

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
            improvements = result.get("response", "").strip()
            
            # Split by semicolon and return as array
            if not improvements:
                return ["Рекомендации по улучшению документа отсутствуют"]
            
            # Split by semicolon, strip each sentence, and filter empty ones
            sentences = [s.strip() for s in improvements.split(";") if s.strip()]
            
            # Ensure we have exactly 3 recommendations
            if len(sentences) < 3:
                sentences.extend(["Дополнительные рекомендации отсутствуют"] * (3 - len(sentences)))
            elif len(sentences) > 3:
                sentences = sentences[:3]
            
            return sentences
            
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

    async def _generate_summary(self, client: httpx.AsyncClient, text: str) -> str:
        """Generate a brief summary of the document in Russian."""
        prompt = f"""ИНСТРУКЦИЯ: Вы помощник, который создает краткие описания документов. Проанализируйте следующий текст документа и предоставьте краткое описание на русском языке, описывающее содержание и назначение этого документа. Описание должно быть максимум 2-3 предложения и отражать основную цель и содержание документа. Верните ТОЛЬКО текст описания на русском языке.

ДОКУМЕНТ:
{text}

ФОРМАТ ОТВЕТА: Краткое описание документа на русском языке (2-3 предложения)"""

        try:
            response = await client.post(
                f"{self.base_url}/chat",
                json={
                    "prompt": prompt,
                    "max_tokens": 1024,
                    "temperature": 0.5
                }
            )
            response.raise_for_status()
            
            result = response.json()
            summary = result.get("response", "").strip()
            
            return summary if summary else "Не удалось создать описание документа"
            
        except Exception as e:
            raise Exception(f"Summary generation failed: {str(e)}")


# Singleton instance
llm_service = LLMService()
