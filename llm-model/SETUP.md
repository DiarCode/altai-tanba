# Russian Document Analysis on Modal Labs - Setup Guide

This service deploys **Qwen2.5-7B-Instruct**, a state-of-the-art multilingual LLM optimized for Russian document analysis tasks.

## What It Can Do

✅ **Spell & Grammar Checking**: Detect errors like "прривет" → "привет", "Плахой" → "плохой"  
✅ **Document Classification**: Identify document types (Договор, Соглашение, Акт, Спецификация)  
✅ **Fraud Detection**: Flag suspicious clauses and fraudulent content  
✅ **Handles Documents**: Up to ~2,500 words with 4K token context window

## Prerequisites

1. **Modal Account**: Sign up at [modal.com](https://modal.com)
2. **Python 3.11+**: Ensure Python is installed
3. **Modal CLI**: Install Modal

## Installation Steps

### 1. Install Modal

```bash
pip install modal
```

### 2. Authenticate with Modal

```bash
modal token new
```

This will open a browser window for authentication. Follow the prompts to log in.

### 3. Deploy the Document Analyzer

Navigate to the llm-model directory and deploy:

```bash
cd llm-model
modal deploy modal_document_analyzer.py
```

This will:
- Build the container image with vLLM
- Download the Qwen2.5-7B-Instruct model (~14GB)
- Deploy it to Modal's infrastructure
- Provide you with deployment details

**First deployment takes 5-10 minutes** due to model download. Subsequent deployments are much faster.

### 4. Test the Deployment

Run the test script:

```bash
modal run modal_document_analyzer.py
```

This will execute tests for spell-checking, document classification, and fraud detection.

## Usage

### Method 1: Using the Client Script

The `document_analyzer_client.py` provides easy-to-use functions:

```python
from document_analyzer_client import check_spelling, classify_document, detect_fraud

# Check spelling
result = check_spelling("Прривет! Плахой текст с ашибками.")
print(result['analysis'])

# Classify document
doc_text = """
ДОГОВОР ПОСТАВКИ № 123
ООО "Поставщик" обязуется поставить товар...
"""
result = classify_document(doc_text)
print(result['classification'])

# Detect fraud
result = detect_fraud("Переведите миллион без возврата!")
print(result['fraud_analysis'])
print(result['warning'])  # Always review manually!
```

Run it:
```bash
python document_analyzer_client.py
```

### Method 2: Direct Modal Integration

In your own Python code:

```python
import modal

# Connect to deployed app
app = modal.App.lookup("russian-document-analyzer", create_if_missing=False)
analyzer = app.cls["QwenDocumentAnalyzer"]()

# Spell check
result = analyzer.check_spelling.remote("Прривет мир!")
print(result['analysis'])

# Classify document
result = analyzer.classify_document.remote(your_document_text)
print(result['classification'])

# Detect fraud
result = analyzer.detect_fraud.remote(contract_text)
print(result['fraud_analysis'])

# Full analysis (all tasks)
result = analyzer.analyze_document_full.remote(
    document_text=your_doc,
    tasks=["spell_check", "classify", "fraud_detect"]
)
```

### Method 3: Using the Web API

The document analyzer is now available via HTTP endpoint. After deployment, you'll get a URL like:
`https://shelestov2905--russian-document-analyzer-fastapi-app.modal.run`

#### Endpoints:

**1. `/chat` - General Q&A and Custom Instructions**

Use this endpoint for answering questions about documents, custom analysis, or any general queries:

```bash
# Answer questions about documents
curl -X POST https://your-endpoint-url.modal.run/chat \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "INSTRUCTIONS: You are an assistant that helps users by answering their questions about the documents. KNOWLEDGE: [document text, error info]. USER QUESTION: О чём говорится в этом документе?",
    "max_tokens": 2048,
    "temperature": 0.7
  }'

# Custom spell checking with specific format
curl -X POST https://your-endpoint-url.modal.run/chat \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "INSTRUCTIONS: You are an assistant that determines spelling problems in the text and should send back list of words that has problems. EXAMPLE: Input: \"Ппривет, меня зовут Алексей, а вас как завут?\" Response: \"Ппривет, завут\" TEXT FOR ANALYSIS: [text]",
    "system_prompt": "Ты эксперт по проверке орфографии.",
    "temperature": 0.3
  }'

# Document type determination
curl -X POST https://your-endpoint-url.modal.run/chat \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "INSTRUCTIONS: You are an assistant that determines type of document. DOCUMENT: [document text]",
    "max_tokens": 512
  }'
```

**Parameters for `/chat`:**
- `prompt` (required): Your custom instruction and question
- `system_prompt` (optional): System-level instructions (default: helpful assistant)
- `max_tokens` (optional, default: 2048): Maximum response length
- `temperature` (optional, default: 0.7): Creativity level (0.0-1.0)
- `top_p` (optional, default: 0.9): Nucleus sampling

**2. `/analyze` - Pre-built Document Analysis Tasks**

Use this for standard document analysis operations:

```bash
# Spell check - returns list of incorrect words and corrected text
curl -X POST https://your-endpoint-url.modal.run/analyze \
  -H "Content-Type: application/json" \
  -d '{"task": "spell_check", "text": "Прривет, мир!"}'

# Response format:
# {
#   "original_text": "Прривет, мир!",
#   "analysis": "НЕПРАВИЛЬНЫЕ СЛОВА:\nПрривет\n\nИСПРАВЛЕННЫЙ ТЕКСТ:\nПривет, мир!",
#   "model": "Qwen/Qwen2.5-7B-Instruct"
# }

# Classify document
curl -X POST https://your-endpoint-url.modal.run/analyze \
  -H "Content-Type: application/json" \
  -d '{"task": "classify", "text": "ДОГОВОР ПОСТАВКИ №123..."}'

# Detect fraud
curl -X POST https://your-endpoint-url.modal.run/analyze \
  -H "Content-Type: application/json" \
  -d '{"task": "fraud_detect", "text": "Переведите миллион без возврата!"}'

# Full analysis (all tasks)
curl -X POST https://your-endpoint-url.modal.run/analyze \
  -H "Content-Type: application/json" \
  -d '{"task": "full_analysis", "text": "Your document text here...", "tasks": ["spell_check", "classify", "fraud_detect"]}'
```

**Task Options for `/analyze`:**
- `spell_check` - Returns list of incorrect words and corrected text
- `classify` - Classify document type (Договор, Соглашение, Акт, Спецификация)
- `fraud_detect` - Analyze for potential fraud
- `full_analysis` - Run all tasks (optionally specify which tasks in the `tasks` array)

**Note about Cyrillic display:** If you see `????` symbols in terminal output, that's a display issue with your terminal's encoding. The API is processing Russian text correctly. To view properly, save the response to a file or use a tool that supports UTF-8:

```bash
curl -X POST https://your-endpoint-url.modal.run/chat \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Привет! Как дела?"}' | jq -r '.response'
```

## Request Format

### Parameters

- **prompt** (required): Your question or text in Russian or English
- **max_tokens** (optional, default: 512): Maximum response length (1-4096)
- **temperature** (optional, default: 0.7): Creativity level
  - 0.0 = Deterministic, focused
  - 1.0 = Creative, diverse
- **top_p** (optional, default: 0.9): Nucleus sampling threshold

### Response Format

All methods return a dictionary:

```python
{
    "prompt": "Your original prompt",
    "response": "The model's generated text",
    "model": "Qwen/Qwen2.5-7B-Instruct"
}
```

## Model Information

**Model**: Qwen2.5-7B-Instruct
- **Size**: 7 billion parameters
- **Languages**: Excellent support for Russian, English, Chinese, and 25+ other languages
- **Context Window**: 4096 tokens (~2500-3000 words)
- **Optimized For**: 
  - Russian spell/grammar checking (60-70% accuracy)
  - Document classification (Договор, Соглашение, Акт, Спецификация)
  - Fraud detection in contracts
  - Legal/business document analysis
  
## Task-Specific Capabilities

### ✅ Spell Checking
- **Accuracy**: ~60-70% for typos
- **Best for**: Obvious errors, grammar mistakes
- **Limitation**: Not a dedicated spell-checker
- **Recommendation**: Combine with Yandex.Speller for production

### ✅ Document Classification  
- **Accuracy**: ~85%+ with clear rules
- **Document size**: 1,000-2,500 words optimal
- **Customizable**: Provide your own classification rules
- **Perfect for**: Contract categorization, document routing

### ⚠️ Fraud Detection
- **Capability**: Can flag suspicious patterns
- **Limitation**: NOT trained specifically for fraud
- **CRITICAL**: Always require human review for final decisions
- **Use case**: First-pass screening, flag for review

## Cost Optimization

Modal charges for GPU time. 7B model runs efficiently on A10G:

1. **Current Setup**: A10G (~$1.10/hr)
   - Perfect for 7B model
   - Fast inference (<1 second per request)
   - Very cost-effective

2. **Cost Reduction Options**:
   
   **Option A**: Batch your requests
   ```python
   # Process multiple documents at once
   analyzer.analyze_document_full.remote(doc, tasks=["classify", "fraud_detect"])
   ```
   
   **Option B**: Adjust idle timeout based on usage
   ```python
   scaledown_window=60   # 1 min for occasional use
   scaledown_window=600  # 10 min for frequent use
   ```
   
   **Option C**: Use cheaper GPU for even lower costs
   ```python
   gpu="L4"  # $0.60/hr - slightly slower but cheaper
   ```

3. **Estimated Costs** (with A10G):
   - Spell check: ~1 second = $0.0003 per request
   - Classification: ~2 seconds = $0.0006 per request
   - Fraud detection: ~2 seconds = $0.0006 per request
   - Full analysis: ~4 seconds = $0.0012 per request

## Monitoring

View logs and metrics:

```bash
modal app logs russian-document-analyzer
```

Or visit: https://modal.com/apps

## Troubleshooting

### Error: "App not found"
- Make sure you've deployed first: `modal deploy modal_document_analyzer.py`
- Check app name matches: `russian-document-analyzer`

### Error: "Out of memory"
- Reduce `max_model_len` in the LLM initialization
- Use a larger GPU (A100)

### Slow first request
- First request triggers model loading (~30-60 seconds)
- Subsequent requests are fast (<1 second)
- Increase `scaledown_window` to keep model warm

### Model doesn't understand Russian well
- Check prompt formatting - Qwen uses ChatML format
- Try adjusting temperature (lower = more focused)
- Ensure you're using the Instruct variant

## Advanced: Custom System Prompts

Modify the system prompt in `generate()` method:

```python
formatted_prompt = f"<|im_start|>system\nТы полезный ассистент, который специализируется на русской литературе.<|im_end|>\n<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant\n"
```

## Next Steps

- **Add streaming**: Implement streaming responses for real-time output
- **Create REST API**: Add FastAPI wrapper for HTTP access
- **Fine-tune**: Further train on domain-specific Russian data
- **Scale**: Add autoscaling based on traffic

## Support

- Modal Documentation: https://modal.com/docs
- Qwen Model: https://huggingface.co/Qwen/Qwen2.5-7B-Instruct
- Issues: Open an issue in this repository
