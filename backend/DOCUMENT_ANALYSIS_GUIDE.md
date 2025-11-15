# Document Fraud Compliance Analysis Service

Complete guide for the automated document analysis service that detects fraud, spelling mistakes, and classifies documents.

---

## 📋 Table of Contents

1. [What This Does](#what-this-does)
2. [Quick Setup (5 Minutes)](#quick-setup-5-minutes)
3. [Architecture](#architecture)
4. [API Reference](#api-reference)
5. [Configuration](#configuration)
6. [Testing](#testing)
7. [Troubleshooting](#troubleshooting)

---

## What This Does

This service analyzes document images to detect:

- **🚨 Fraud**: Identifies suspicious or fraudulent sentences
- **✍️ Spelling Mistakes**: Detects misspelled words in Russian text
- **📋 Document Type**: Classifies documents (Договор, Соглашение, Акт, etc.)

### Workflow

```
1. Client sends documentId
2. Service downloads images from MinIO ({documentId}/pages/*.png)
3. OCR extracts text from images (EasyOCR)
4. LLM analyzes text (Modal Labs):
   - Detects fraudulent sentences
   - Identifies spelling mistakes
   - Classifies document type
5. Results saved to database
6. Response returned to client
```

### Example

**Request:**
```json
{
  "documentId": "383ed92sjjjw199103jd"
}
```

**Response:**
```json
{
  "fraudSentences": ["отдай 50000 долларов", "ограбь банк"],
  "mistakeWords": ["ппривет", "добрео", "зилёный", "выгоранеи"],
  "documentType": "Договор"
}
```

---

## Quick Setup (5 Minutes)

### Prerequisites

- Python 3.11+
- PostgreSQL database
- MinIO/S3 storage
- Modal account (free tier works)

### Step 1: Deploy Modal Labs LLM (3-5 minutes)

```bash
cd llm-model
pip install modal
modal token new
modal deploy modal_document_analyzer.py
```

**Copy the endpoint URL** from deployment output:
```
https://your-username--russian-document-analyzer-fastapi-app.modal.run
```

### Step 2: Configure Environment

Add to `backend/.env`:
```env
MODAL_LLM_ENDPOINT=https://your-modal-endpoint-url.modal.run
```

### Step 3: Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

**New dependencies added:**
- `boto3` - AWS S3/MinIO client
- `easyocr` - OCR text extraction
- `pillow` - Image processing

### Step 4: Run Database Migration

```bash
prisma migrate dev --name add_document_analysis
```

This creates the `document_analyses` table:
```sql
CREATE TABLE document_analyses (
  id UUID PRIMARY KEY,
  document_id VARCHAR UNIQUE,
  status VARCHAR,  -- PROCESSING, COMPLETED, FAILED
  fraud_sentences TEXT[],
  mistake_words TEXT[],
  document_type VARCHAR,
  error_log TEXT,
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);
```

### Step 5: Start Server

```bash
python -m src.main
```

Server starts on `http://localhost:8000`

### Step 6: Test

```bash
# Quick test
curl http://localhost:8000/ping

# View API docs
open http://localhost:8000/docs
```

---

## Architecture

### File Structure

```
backend/src/
├── core/
│   ├── s3/
│   │   └── s3_service.py              # MinIO image download
│   ├── services/
│   │   ├── ocr_service.py             # Text extraction (EasyOCR)
│   │   └── llm_service.py             # Modal Labs LLM analysis
│   └── config/
│       └── settings.py                # MODAL_LLM_ENDPOINT added
└── modules/
    ├── document_analysis_service.py    # Main orchestrator
    ├── document_analysis_router.py     # FastAPI endpoints
    └── document_analysis_models.py     # Request/response models
```

### Flow Diagram

```
Client Request (documentId)
        ↓
   Create DB Record (PROCESSING)
        ↓
   Download Images from MinIO
        ↓
   Extract Text with OCR
        ↓
   Analyze with LLM
   ├─ Fraud Detection
   ├─ Spelling Check
   └─ Document Classification
        ↓
   Update DB (COMPLETED + results)
        ↓
   Return Results
```

### Status States

- **PROCESSING**: Analysis in progress
- **COMPLETED**: Success (results available)
- **FAILED**: Error (see errorLog field)

---

## API Reference

### Base URL
```
http://localhost:8000/api/v1/document-analysis
```

### Endpoints

#### 1. Analyze Document (Synchronous)

Waits for analysis to complete before returning.

```http
POST /analyze
Content-Type: application/json

{
  "documentId": "test-doc-123"
}
```

**Response (200 OK):**
```json
{
  "fraudSentences": ["отдай 50000 долларов"],
  "mistakeWords": ["ппривет", "добрео"],
  "documentType": "Договор"
}
```

**Response (500 Error):**
```json
{
  "detail": "Failed to download images: No images found for document test-doc-123"
}
```

#### 2. Analyze Document (Async)

Starts analysis in background, returns immediately.

```http
POST /analyze-async
Content-Type: application/json

{
  "documentId": "test-doc-123"
}
```

**Response (202 Accepted):**
```json
{
  "message": "Analysis started",
  "documentId": "test-doc-123",
  "status": "PROCESSING"
}
```

#### 3. Check Status

Get current analysis status.

```http
GET /status/{documentId}
```

**Response (PROCESSING):**
```json
{
  "status": "PROCESSING",
  "documentId": "test-doc-123"
}
```

**Response (COMPLETED):**
```json
{
  "status": "COMPLETED",
  "documentId": "test-doc-123",
  "fraudSentences": ["отдай 50000 долларов"],
  "mistakeWords": ["ппривет"],
  "documentType": "Договор"
}
```

**Response (FAILED):**
```json
{
  "status": "FAILED",
  "documentId": "test-doc-123",
  "errorLog": "OCR extraction failed: No text could be extracted"
}
```

---

## Configuration

### Environment Variables

Required in `.env`:

```env
# Modal Labs LLM (NEW - required)
MODAL_LLM_ENDPOINT=https://your-endpoint.modal.run

# Database (already configured)
DATABASE_URL=postgresql://user:pass@host:port/db

# MinIO/S3 (already configured)
S3_ACCESS_ENDPOINT=http://localhost:9000
S3_ACCESS_KEY=your-access-key
S3_SECRET_KEY=your-secret-key
S3_BUCKET=your-bucket
S3_REGION=us-east-1
S3_PATH_STYLE=true
```

### MinIO Storage Structure

Images must be stored at:
```
{bucket}/
  └── {documentId}/
      └── pages/
          ├── page_1.png
          ├── page_2.png
          └── page_3.png
```

**Supported formats:** PNG only (JPEG/PDF support coming)

### Modal Labs Configuration

The LLM service sends three requests to Modal:

1. **Fraud Detection** - Temperature: 0.3, Max tokens: 2048
2. **Spelling Mistakes** - Temperature: 0.3, Max tokens: 2048
3. **Document Classification** - Temperature: 0.3, Max tokens: 512

To modify prompts, edit `src/core/services/llm_service.py`

---

## Testing

### Option 1: Using Test Script

```bash
python test_document_analysis.py
```

Edit the file to uncomment your desired test case.

### Option 2: Using curl

```bash
# Synchronous analysis
curl -X POST http://localhost:8000/api/v1/document-analysis/analyze \
  -H "Content-Type: application/json" \
  -d '{"documentId": "test-doc-123"}'

# Async analysis
curl -X POST http://localhost:8000/api/v1/document-analysis/analyze-async \
  -H "Content-Type: application/json" \
  -d '{"documentId": "test-doc-123"}'

# Check status
curl http://localhost:8000/api/v1/document-analysis/status/test-doc-123
```

### Option 3: Upload Test Data

Use the utility script to create test documents:

```bash
python upload_test_images.py
```

First, edit the file to configure MinIO credentials:
```python
S3_ENDPOINT = "http://localhost:9000"
S3_ACCESS_KEY = "your-access-key"
S3_SECRET_KEY = "your-secret-key"
S3_BUCKET = "your-bucket"
```

This creates three test documents:
- `test-fraud-doc-001` - Contains fraudulent sentences
- `test-mistakes-doc-002` - Contains spelling mistakes
- `test-clean-doc-003` - Clean document

### Option 4: API Documentation

Open browser: `http://localhost:8000/docs`

Interactive API testing with Swagger UI.

---

## Troubleshooting

### Common Issues

#### "Import boto3 could not be resolved"

**Cause:** Dependencies not installed  
**Fix:**
```bash
pip install -r requirements.txt
```

#### "No images found for document {id}"

**Cause:** Images not in correct MinIO location  
**Fix:** Ensure images are at `{documentId}/pages/*.png`

```bash
# Use upload utility
python upload_test_images.py
```

#### "LLM analysis failed"

**Cause:** Modal endpoint not configured or unreachable  
**Fix:**
1. Check `.env` has `MODAL_LLM_ENDPOINT`
2. Verify Modal app is running:
   ```bash
   modal app list
   ```
3. Test endpoint:
   ```bash
   curl https://your-endpoint.modal.run/chat \
     -H "Content-Type: application/json" \
     -d '{"prompt": "Привет"}'
   ```

#### EasyOCR downloading models (first run)

**Expected behavior:** Downloads ~100MB of models (1-2 minutes)  
**Fix:** Wait for download to complete. Models are cached for future use.

#### Slow first request

**Expected:**
- Modal cold start: 30-60 seconds
- EasyOCR model load: 5-10 seconds
- Total: 35-70 seconds

**Fix:** Subsequent requests are fast (2-5 seconds). Modal stays warm for 10 minutes.

### Performance Tips

**For large documents (>5 pages):**
- Use async endpoint (`/analyze-async`)
- Poll status endpoint every 5 seconds

**For high volume:**
- Modal Labs auto-scales
- Consider increasing Modal GPU instances
- Add result caching (future enhancement)

### Database Issues

```bash
# Reset database (development only!)
prisma migrate reset

# Reapply migrations
prisma migrate dev --name add_document_analysis

# Generate Prisma client
prisma generate
```

### Debug Mode

Check logs for detailed error information:

```python
# In document_analysis_service.py
print(f"Downloaded {len(images)} images")
print(f"Extracted text length: {len(text)}")
```

---

## Advanced Usage

### Custom LLM Prompts

Edit `src/core/services/llm_service.py` to customize analysis:

```python
# Example: More strict fraud detection
prompt = f"""INSTRUCTIONS: You are a fraud detection expert. 
Flag ANY sentence that contains:
- Money transfers
- Urgent requests
- Threats or coercion
...
"""
```

### Batch Processing

Process multiple documents:

```python
import asyncio
from document_analysis_service import document_analysis_service

async def batch_analyze(document_ids):
    tasks = [
        document_analysis_service.analyze_document(doc_id)
        for doc_id in document_ids
    ]
    return await asyncio.gather(*tasks, return_exceptions=True)
```

### Custom OCR Settings

Modify `src/core/services/ocr_service.py`:

```python
# Enable GPU
self.reader = easyocr.Reader(['ru', 'en'], gpu=True)

# Adjust confidence threshold
results = self.reader.readtext(image, min_confidence=0.5)
```

---

## What's Next

### Immediate Next Steps

1. ✅ Deploy Modal Labs LLM
2. ✅ Configure environment variables
3. ✅ Run database migration
4. ✅ Upload test data
5. ✅ Test API endpoints

### Future Enhancements

- [ ] Support JPEG, TIFF, PDF formats
- [ ] Add confidence scores to results
- [ ] Implement result caching
- [ ] Batch document processing
- [ ] Retry logic for transient failures
- [ ] Metrics and monitoring
- [ ] Rate limiting

---

## Quick Reference

### Start Server
```bash
cd backend && python -m src.main
```

### Run Tests
```bash
python test_document_analysis.py
```

### Upload Test Data
```bash
python upload_test_images.py
```

### Check Logs
```bash
# Modal logs
modal app logs russian-document-analyzer

# Server logs
# Check terminal where server is running
```

### API Docs
```
http://localhost:8000/docs
```

---

## Support

**Files:**
- `test_document_analysis.py` - API testing examples
- `upload_test_images.py` - Test data uploader
- `llm-model/SETUP.md` - Modal Labs setup guide

**Key Services:**
- `src/core/s3/s3_service.py` - S3/MinIO operations
- `src/core/services/ocr_service.py` - OCR text extraction
- `src/core/services/llm_service.py` - LLM analysis
- `src/modules/document_analysis_service.py` - Main orchestrator

---

**Status:** ✅ Ready for Testing  
**Created:** November 15, 2025  
**Version:** 1.0.0
