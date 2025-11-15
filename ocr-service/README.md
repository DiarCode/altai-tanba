# OCR Service

This directory contains a Modal Labs-based OCR service using **PaddleOCR**, an open-source OCR engine.

## Features

- **Open Source**: Based on PaddleOCR (Apache License 2.0)
- **Multi-language**: Supports Russian and English
- **GPU Accelerated**: Runs on Modal's T4 GPUs for fast processing
- **Batch Processing**: Efficiently processes multiple images
- **High Accuracy**: State-of-the-art OCR models

## Files

- `modal_ocr.py` - Main Modal service implementation
- `modal_ocr_client.py` - Python client for testing and integration
- `requirements.txt` - Python dependencies
- `SETUP.md` - Detailed setup and usage guide

## Quick Start

1. Install Modal:
```bash
pip install -r requirements.txt
```

2. Authenticate with Modal:
```bash
modal token new
```

3. Deploy the service:
```bash
modal deploy modal_ocr.py
```

4. Test the service:
```bash
modal run modal_ocr.py
```

## Integration with Backend

The backend OCR service can use this Modal service by setting the environment variable:

```bash
USE_MODAL_OCR=true
```

When enabled, the backend will use the Modal OCR service instead of the local EasyOCR library, providing:
- Faster processing (GPU acceleration)
- Better resource management (no local model loading)
- Scalability (handles concurrent requests)

## Documentation

See [SETUP.md](./SETUP.md) for detailed setup instructions, API reference, and troubleshooting.

## Why PaddleOCR?

PaddleOCR was chosen because:
- **Open Source**: Fully transparent, MIT licensed
- **High Performance**: Optimized for both speed and accuracy
- **Multi-language**: Excellent support for Russian and English
- **Active Development**: Regular updates from PaddlePaddle team
- **Production Ready**: Used by thousands of companies worldwide

GitHub: https://github.com/PaddlePaddle/PaddleOCR
