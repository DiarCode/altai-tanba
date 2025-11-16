# OCR Service on Modal Labs - Setup Guide

This service deploys **PaddleOCR**, an open-source OCR engine that supports Russian and English text extraction from images.

## What It Can Do

✅ **Multi-language Support**: Extract text in Russian and English  
✅ **High Accuracy**: Uses PaddleOCR's state-of-the-art models  
✅ **Rotation Detection**: Automatically handles rotated text  
✅ **Batch Processing**: Process multiple images efficiently  
✅ **Fast Processing**: GPU-accelerated with Modal's T4 GPUs

## About PaddleOCR

PaddleOCR is an open-source OCR toolkit developed by PaddlePaddle. It provides:
- **Open Source**: MIT License, fully transparent
- **Pre-trained Models**: Ready to use for 80+ languages
- **High Performance**: Optimized for both speed and accuracy
- **Active Development**: Regular updates and improvements

GitHub: https://github.com/PaddlePaddle/PaddleOCR

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

### 3. Deploy the OCR Service

Navigate to the ocr-service directory and deploy:

```bash
cd ocr-service
modal deploy modal_ocr.py
```

This will:
- Build the container image with PaddleOCR
- Download the OCR models (~100MB)
- Deploy it to Modal's infrastructure with T4 GPU
- Provide you with deployment details

**First deployment takes 3-5 minutes** due to model download. Subsequent deployments are much faster.

### 4. Test the Deployment

Run the test script:

```bash
modal run modal_ocr.py
```

This will create test images and extract text from them.

## Usage

### Method 1: Using the Client Script

The `modal_ocr_client.py` provides easy-to-use functions:

```python
from modal_ocr_client import (
    extract_text_from_image,
    extract_text_from_images_batch,
    extract_text_combined
)

# Single image
with open("document.png", "rb") as f:
    image_bytes = f.read()

result = extract_text_from_image(image_bytes, "document.png")
print(f"Text: {result['text']}")
print(f"Confidence: {result['confidence']:.2%}")

# Multiple images (batch)
images = [
    ("page1.png", page1_bytes),
    ("page2.png", page2_bytes),
]

combined_text = extract_text_combined(images)
print(combined_text)
```

Run it:
```bash
python modal_ocr_client.py
```

### Method 2: Direct Modal Integration

In your own Python code:

```python
import modal

# Connect to deployed app
app = modal.App.lookup("paddleocr-service", create_if_missing=False)
PaddleOCR = app.cls["PaddleOCR"]
ocr = PaddleOCR()

# Extract text
result = ocr.extract_text.remote(
    image_bytes=image_bytes,
    filename="document.png"
)
```

## API Reference

### `extract_text(image_bytes, filename)`

Extract text from a single image.

**Parameters:**
- `image_bytes` (bytes): Image content as bytes
- `filename` (str): Optional filename for reference

**Returns:**
```python
{
    "filename": "image.png",
    "text": "extracted text content",
    "confidence": 0.95,  # Average confidence score
    "num_lines": 10      # Number of text lines detected
}
```

### `extract_text_batch(images)`

Extract text from multiple images.

**Parameters:**
- `images` (List[dict]): List of dicts with 'filename' and 'image_bytes'

**Returns:** List of result dicts (same format as `extract_text`)

### `extract_text_combined(images)`

Extract and combine text from multiple images.

**Parameters:**
- `images` (List[dict]): List of dicts with 'filename' and 'image_bytes'

**Returns:**
```python
{
    "combined_text": "all text combined",
    "total_pages": 3,
    "total_lines": 45,
    "average_confidence": 0.93,
    "errors": None  # or list of errors if any
}
```

## Performance

- **Cold Start**: ~10-15 seconds (first request after idle)
- **Warm Requests**: ~1-3 seconds per image
- **Batch Processing**: ~0.5-1 second per image in batch
- **Container Idle Timeout**: 5 minutes (configurable)

## Cost Optimization

Modal charges based on:
- **GPU time**: T4 GPU is ~$0.60/hour
- **CPU time**: Minimal cost for idle containers

Tips:
- Use batch processing for multiple images
- Container stays warm for 5 minutes (free during idle)
- Deploy only when needed, or keep for production use

## Troubleshooting

### "App not found" error
Make sure you've deployed the service:
```bash
modal deploy modal_ocr.py
```

### Poor OCR quality
- Ensure images are high resolution (300 DPI recommended)
- Images should be clear and well-lit
- Try preprocessing: grayscale conversion, noise reduction

### Slow performance
- Use batch processing for multiple images
- Check if container is warm (first request is slower)
- Consider upgrading to A10G GPU for better performance

## Integration with Backend

The backend OCR service has been updated to use this Modal service. See `backend/src/core/services/ocr_service.py` for integration details.

## Development

To modify the OCR model settings, edit `modal_ocr.py`:

```python
self.ocr_engine = POCREngine(
    use_angle_cls=True,      # Text rotation detection
    lang='en',               # Language model
    use_gpu=True,            # GPU acceleration
    det_db_thresh=0.3,       # Detection threshold
    det_db_box_thresh=0.5,   # Box threshold
    rec_batch_num=6,         # Batch size
)
```

## Additional Resources

- [PaddleOCR Documentation](https://github.com/PaddlePaddle/PaddleOCR/blob/release/2.7/README_en.md)
- [Modal Documentation](https://modal.com/docs)
- [Modal GPU Options](https://modal.com/docs/guide/gpu)

## License

This OCR service uses:
- **PaddleOCR**: Apache License 2.0
- **Modal**: Commercial service (see modal.com/pricing)
