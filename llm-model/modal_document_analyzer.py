"""
Russian Document Analysis LLM Service on Modal Labs
Model: Qwen2.5-7B-Instruct (optimized for legal/business documents)

Tasks:
1. Spell/grammar checking in Russian
2. Document classification (Договор, Соглашение, Акт, Спецификация)
3. Fraud detection in contracts
"""

import modal

# Define the Modal app
app = modal.App("russian-document-analyzer")

# Define the image with required dependencies
vllm_image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "vllm==0.6.3",
        "huggingface_hub==0.25.2",
        "fastapi[standard]",
    )
)


@app.cls(
    gpu="A10G",  # A10G is sufficient for 7B model
    image=vllm_image,
    scaledown_window=300,  # Keep container warm for 5 minutes
)
@modal.concurrent(max_inputs=10)
class QwenDocumentAnalyzer:
    """
    Qwen2.5-7B-Instruct for Russian document analysis
    Handles: spell-checking, classification, fraud detection
    """
    
    @modal.enter()
    def load_model(self):
        """Load the model when the container starts"""
        from vllm import LLM
        
        # Initialize vLLM with Qwen2.5-7B-Instruct
        self.llm = LLM(
            model="Qwen/Qwen2.5-7B-Instruct",
            trust_remote_code=True,
            max_model_len=4096,  # 4K context window
            gpu_memory_utilization=0.9,
        )
        print("Qwen2.5-7B model loaded successfully!")
    
    @modal.method()
    def generate(
        self,
        prompt: str,
        system_prompt: str = "Ты полезный ассистент, который отвечает на вопросы пользователей на русском и английском языках.",
        max_tokens: int = 2048,
        temperature: float = 0.7,
        top_p: float = 0.9,
    ) -> dict:
        """
        General-purpose text generation for answering questions
        
        Args:
            prompt: User's question or instruction
            system_prompt: System instructions for the model
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0-1.0)
            top_p: Nucleus sampling parameter
            
        Returns:
            dict with prompt and response
        """
        from vllm import SamplingParams
        
        # Format using ChatML format for Qwen
        formatted_prompt = f"<|im_start|>system\n{system_prompt}<|im_end|>\n<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant\n"
        
        sampling_params = SamplingParams(
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
        )
        
        outputs = self.llm.generate([formatted_prompt], sampling_params)
        response = outputs[0].outputs[0].text
        
        return {
            "prompt": prompt,
            "response": response,
            "model": "Qwen/Qwen2.5-7B-Instruct"
        }
    
    @modal.method()
    def check_spelling(self, text: str) -> dict:
        """
        Check Russian text for spelling and grammar errors
        Returns only the comma-separated list of incorrect words
        
        Args:
            text: Russian text to check
            
        Returns:
            dict with comma-separated incorrect words and corrected text
        """
        from vllm import SamplingParams
        
        prompt = f"""Проверь следующий русский текст на орфографические и грамматические ошибки.

Текст: {text}

ВАЖНО: Верни ТОЛЬКО неправильные слова через запятую, ничего больше. Не добавляй заголовки, пояснения или дополнительный текст.

Примеры:
Входной текст: "Прривет, как делла?"
Твой ответ: Прривет, делла

Входной текст: "Ппривет, меня зовут Алексей, а вас как завут?"
Твой ответ: Ппривет, завут

Входной текст: "Привет, как дела?"
Твой ответ: нет ошибок

Теперь проверь текст выше и верни ТОЛЬКО список неправильных слов через запятую или "нет ошибок"."""

        formatted_prompt = f"<|im_start|>system\nТы эксперт по русскому языку. Твоя задача - найти неправильные слова и вернуть их списком через запятую без дополнительного текста.<|im_end|>\n<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant\n"
        
        sampling_params = SamplingParams(
            max_tokens=512,
            temperature=0.2,  # Very low temperature for consistent output
            top_p=0.9,
        )
        
        outputs = self.llm.generate([formatted_prompt], sampling_params)
        response = outputs[0].outputs[0].text.strip()
        
        return {
            "original_text": text,
            "incorrect_words": response,
            "model": "Qwen/Qwen2.5-7B-Instruct"
        }
    
    @modal.method()
    def classify_document(self, document_text: str, classification_rules: str = "") -> dict:
        """
        Classify Russian business/legal document type
        
        Args:
            document_text: The document content
            classification_rules: Optional custom rules for classification
            
        Returns:
            dict with document type and confidence
        """
        from vllm import SamplingParams
        
        default_rules = """
Правила классификации:
- ДОГОВОР: документ, устанавливающий права и обязанности сторон, содержит условия сделки
- СОГЛАШЕНИЕ: документ о договоренности, менее формальный чем договор
- АКТ: документ, подтверждающий факт (приема-передачи, выполненных работ и т.д.)
- СПЕЦИФИКАЦИЯ: детальное описание товаров, услуг, технических характеристик
"""
        
        rules = classification_rules if classification_rules else default_rules
        
        # Truncate document if too long (keep first ~2500 words for 4K context)
        max_chars = 10000  # Rough estimate: 4 chars per token, 2.5K tokens for doc
        truncated_doc = document_text[:max_chars]
        if len(document_text) > max_chars:
            truncated_doc += "\n\n[...документ обрезан...]"
        
        prompt = f"""{rules}

ДОКУМЕНТ ДЛЯ АНАЛИЗА:
{truncated_doc}

Определи тип документа и объясни почему. Формат ответа:

ТИП ДОКУМЕНТА: [Договор/Соглашение/Акт/Спецификация]
УВЕРЕННОСТЬ: [Высокая/Средняя/Низкая]
ОБОСНОВАНИЕ: [краткое объяснение на основе содержания и признаков документа]
КЛЮЧЕВЫЕ ПРИЗНАКИ: [список найденных признаков]"""

        formatted_prompt = f"<|im_start|>system\nТы эксперт по юридическим и деловым документам. Ты точно классифицируешь типы документов.<|im_end|>\n<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant\n"
        
        sampling_params = SamplingParams(
            max_tokens=1024,
            temperature=0.2,  # Low temperature for consistent classification
            top_p=0.9,
        )
        
        outputs = self.llm.generate([formatted_prompt], sampling_params)
        response = outputs[0].outputs[0].text
        
        return {
            "document_preview": document_text[:200] + "...",
            "was_truncated": len(document_text) > max_chars,
            "classification": response,
            "model": "Qwen/Qwen2.5-7B-Instruct"
        }
    
    @modal.method()
    def detect_fraud(self, document_text: str, fraud_indicators: list[str] = None) -> dict:
        """
        Analyze document for potential fraudulent content
        
        Args:
            document_text: Document to analyze
            fraud_indicators: Optional list of specific fraud patterns to look for
            
        Returns:
            dict with fraud analysis and risk level
        """
        from vllm import SamplingParams
        
        default_indicators = [
            "Требования денег без встречных обязательств",
            "Нереалистичные суммы или условия",
            "Отсутствие права на возврат или гарантий",
            "Давление и срочность без причины",
            "Неясные или противоречивые условия",
            "Требование предоплаты без гарантий",
            "Отсутствие контактных данных или реквизитов",
        ]
        
        indicators = fraud_indicators if fraud_indicators else default_indicators
        indicators_text = "\n".join([f"- {ind}" for ind in indicators])
        
        # Truncate if needed
        max_chars = 10000
        truncated_doc = document_text[:max_chars]
        if len(document_text) > max_chars:
            truncated_doc += "\n\n[...документ обрезан...]"
        
        prompt = f"""Проанализируй документ на наличие признаков мошенничества или подозрительных условий.

ПРИЗНАКИ МОШЕННИЧЕСТВА:
{indicators_text}

ДОКУМЕНТ:
{truncated_doc}

Проведи анализ и предоставь:

УРОВЕНЬ РИСКА: [Высокий/Средний/Низкий/Отсутствует]
НАЙДЕННЫЕ ПОДОЗРИТЕЛЬНЫЕ ФРАЗЫ: [список с цитатами из документа]
КРАСНЫЕ ФЛАГИ: [конкретные проблемы]
РЕКОМЕНДАЦИИ: [что нужно проверить или изменить]

ВАЖНО: Будь объективным. Не все необычные условия - это мошенничество."""

        formatted_prompt = f"<|im_start|>system\nТы эксперт по выявлению мошенничества в юридических документах. Ты анализируешь документы на предмет подозрительных условий и потенциального обмана.<|im_end|>\n<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant\n"
        
        sampling_params = SamplingParams(
            max_tokens=2048,
            temperature=0.4,  # Slightly higher for nuanced analysis
            top_p=0.9,
        )
        
        outputs = self.llm.generate([formatted_prompt], sampling_params)
        response = outputs[0].outputs[0].text
        
        return {
            "document_preview": document_text[:200] + "...",
            "was_truncated": len(document_text) > max_chars,
            "fraud_analysis": response,
            "model": "Qwen/Qwen2.5-7B-Instruct",
            "warning": "⚠️ Это автоматический анализ. Окончательное решение должен принимать человек-эксперт."
        }
    
    @modal.method()
    def analyze_document_full(
        self,
        document_text: str,
        tasks: list[str] = None,
        classification_rules: str = "",
        fraud_indicators: list[str] = None
    ) -> dict:
        """
        Perform complete document analysis (all tasks at once)
        
        Args:
            document_text: Document to analyze
            tasks: List of tasks to perform: ["spell_check", "classify", "fraud_detect"]
            classification_rules: Custom classification rules
            fraud_indicators: Custom fraud indicators
            
        Returns:
            dict with all analysis results
        """
        if tasks is None:
            tasks = ["spell_check", "classify", "fraud_detect"]
        
        results = {
            "document_length": len(document_text),
            "tasks_performed": tasks
        }
        
        if "spell_check" in tasks:
            # Only check first 2000 chars for spelling (full doc would be too slow)
            preview = document_text[:2000]
            results["spelling"] = self.check_spelling(preview)
            results["spelling"]["note"] = "Проверены первые 2000 символов документа"
        
        if "classify" in tasks:
            results["classification"] = self.classify_document(document_text, classification_rules)
        
        if "fraud_detect" in tasks:
            results["fraud_detection"] = self.detect_fraud(document_text, fraud_indicators)
        
        return results


# Web API Endpoints
@app.function(image=vllm_image)
@modal.asgi_app()
def fastapi_app():
    from fastapi import FastAPI, Request
    
    web_app = FastAPI(
        title="Russian Document Analyzer API",
        description="API for document analysis and general Q&A using Qwen2.5-7B-Instruct"
    )
    
    @web_app.post("/analyze")
    async def analyze_endpoint(request: Request):
        """Document analysis endpoint (spell_check, classify, fraud_detect, full_analysis)"""
        try:
            data = await request.json()
        except Exception as e:
            return {"error": f"Invalid JSON: {str(e)}"}
        return api_analyze_impl(data)
    
    @web_app.post("/chat")
    async def chat_endpoint(request: Request):
        """
        General-purpose chat endpoint for answering questions
        
        Request body:
        {
            "prompt": "Your question or instruction",
            "system_prompt": "Optional system instructions" (default: helpful assistant),
            "max_tokens": 2048 (optional),
            "temperature": 0.7 (optional),
            "top_p": 0.9 (optional)
        }
        """
        try:
            data = await request.json()
        except Exception as e:
            return {"error": f"Invalid JSON: {str(e)}"}
        return api_chat_impl(data)
    
    @web_app.get("/")
    async def root():
        """API information"""
        return {
            "service": "Russian Document Analyzer",
            "model": "Qwen/Qwen2.5-7B-Instruct",
            "endpoints": {
                "/analyze": "Document analysis tasks",
                "/chat": "General Q&A and custom instructions"
            }
        }
    
    return web_app


def api_chat_impl(data: dict):
    """
    General-purpose chat endpoint implementation
    """
    prompt = data.get("prompt", "")
    
    if not prompt:
        return {"error": "Missing 'prompt' parameter"}
    
    system_prompt = data.get("system_prompt", "Ты полезный ассистент, который отвечает на вопросы пользователей на русском и английском языках.")
    max_tokens = data.get("max_tokens", 2048)
    temperature = data.get("temperature", 0.7)
    top_p = data.get("top_p", 0.9)
    
    analyzer = QwenDocumentAnalyzer()
    
    return analyzer.generate.remote(
        prompt=prompt,
        system_prompt=system_prompt,
        max_tokens=max_tokens,
        temperature=temperature,
        top_p=top_p
    )


def api_analyze_impl(data: dict):
    """
    Web API endpoint for document analysis
    
    POST body:
    {
        "task": "spell_check" | "classify" | "fraud_detect" | "full_analysis",
        "text": "document text here",
        "max_tokens": 512 (optional),
        "temperature": 0.7 (optional)
    }
    """
    task = data.get("task", "spell_check")
    text = data.get("text", "")
    
    if not text:
        return {"error": "Missing 'text' parameter"}
    
    analyzer = QwenDocumentAnalyzer()
    
    if task == "spell_check":
        return analyzer.check_spelling.remote(text)
    elif task == "classify":
        return analyzer.classify_document.remote(text)
    elif task == "fraud_detect":
        return analyzer.detect_fraud.remote(text)
    elif task == "full_analysis":
        tasks = data.get("tasks", ["spell_check", "classify", "fraud_detect"])
        return analyzer.analyze_document_full.remote(text, tasks=tasks)
    else:
        return {"error": f"Unknown task: {task}. Use: spell_check, classify, fraud_detect, or full_analysis"}


@app.local_entrypoint()
def main():
    """
    Test all document analysis capabilities
    """
    analyzer = QwenDocumentAnalyzer()
    
    # Test 1: Spell checking
    print("\n" + "="*60)
    print("TEST 1: Spell Checking")
    print("="*60)
    
    test_text = "Прривет! Плахой текст с ашибками. Корова был большой."
    result = analyzer.check_spelling.remote(test_text)
    print(f"Original: {result['original_text']}")
    print(f"Analysis:\n{result['analysis']}\n")
    
    # Test 2: Document Classification
    print("\n" + "="*60)
    print("TEST 2: Document Classification")
    print("="*60)
    
    contract_sample = """
ДОГОВОР ПОСТАВКИ № 123

г. Москва                                                    15 ноября 2025 г.

ООО "Поставщик", именуемое в дальнейшем "Поставщик", в лице генерального директора
Иванова И.И., действующего на основании Устава, с одной стороны, и ООО "Покупатель",
именуемое в дальнейшем "Покупатель", в лице директора Петрова П.П., действующего
на основании Устава, с другой стороны, заключили настоящий Договор о нижеследующем:

1. ПРЕДМЕТ ДОГОВОРА
1.1. Поставщик обязуется поставить, а Покупатель принять и оплатить товар согласно
спецификации, являющейся неотъемлемой частью настоящего Договора.
"""
    
    result = analyzer.classify_document.remote(contract_sample)
    print(f"Document preview: {result['document_preview']}")
    print(f"Classification:\n{result['classification']}\n")
    
    # Test 3: Fraud Detection
    print("\n" + "="*60)
    print("TEST 3: Fraud Detection")
    print("="*60)
    
    suspicious_text = """
СОГЛАШЕНИЕ

Вы должны будете перечислить мне пять миллионов долларов в течение 24 часов
без возврата и без каких-либо гарантий с моей стороны. Деньги отправляются на
счет в офшоре. Никаких документов о получении не предоставляется.

Если не перечислите - будут последствия. Это срочно!
"""
    
    result = analyzer.detect_fraud.remote(suspicious_text)
    print(f"Document preview: {result['document_preview']}")
    print(f"Fraud Analysis:\n{result['fraud_analysis']}")
    print(f"\n{result['warning']}\n")
    
    # Test 4: Full Analysis
    print("\n" + "="*60)
    print("TEST 4: Full Document Analysis")
    print("="*60)
    
    result = analyzer.analyze_document_full.remote(
        contract_sample,
        tasks=["classify", "fraud_detect"]
    )
    print(f"Tasks performed: {result['tasks_performed']}")
    print(f"Document length: {result['document_length']} characters")
    print(f"\nClassification: {result['classification']['classification'][:200]}...")
    print(f"\nFraud Detection: {result['fraud_detection']['fraud_analysis'][:200]}...")
