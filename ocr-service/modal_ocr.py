"""
OCR Service on Modal Labs using PaddleOCR
PaddleOCR is an open-source OCR tool that supports Russian and English
"""

import modal
import io
from typing import List

# Define the Modal app
app = modal.App("paddleocr-service")

# Define the image with PaddleOCR dependencies
ocr_image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("libgl1", "libglib2.0-0", "libgomp1")  # Required for OpenCV
    .pip_install(
        "paddlepaddle==2.6.1",
        "paddleocr==2.7.3",
        "pillow==10.1.0",
        "numpy==1.24.3",
        "opencv-python-headless==4.8.1.78",
    )
)


@app.cls(
    gpu="T4",  # T4 GPU is cost-effective for OCR
    image=ocr_image,
    scaledown_window=300,  # Keep container warm for 5 minutes
)
@modal.concurrent(max_inputs=20)  # Handle multiple requests concurrently
class PaddleOCR:
    """
    PaddleOCR model for text extraction from images
    Supports Russian and English languages
    """
    
    @modal.enter()
    def load_model(self):
        """Load the OCR model when the container starts"""
        from paddleocr import PaddleOCR as POCREngine
        
        # Initialize PaddleOCR with Russian and English support
        # Using 'cyrillic' lang for Russian text recognition
        self.ocr_engine = POCREngine(
            use_angle_cls=True,  # Enable text rotation detection
            lang='cyrillic',  # Use Cyrillic (Russian) language model
            use_gpu=True,
            show_log=False,
            det_db_thresh=0.3,  # Detection threshold
            det_db_box_thresh=0.5,  # Box threshold
            rec_batch_num=6,  # Batch size for recognition
        )
        print("PaddleOCR model loaded successfully with Cyrillic (Russian) support!")
    
    @modal.method()
    def extract_text(self, image_bytes: bytes, filename: str = "image") -> dict:
        """
        Extract text from a single image
        
        Args:
            image_bytes: Image content as bytes
            filename: Optional filename for reference
            
        Returns:
            dict with 'filename', 'text', and 'confidence' keys
        """
        import numpy as np
        from PIL import Image
        
        try:
            # Convert bytes to PIL Image
            image = Image.open(io.BytesIO(image_bytes))
            
            # Convert to RGB if necessary (PaddleOCR works best with RGB)
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Convert PIL Image to numpy array
            image_array = np.array(image)
            
            # Perform OCR
            # Result format: [[[bbox], (text, confidence)], ...]
            results = self.ocr_engine.ocr(image_array, cls=True)
            
            if not results or not results[0]:
                return {
                    "filename": filename,
                    "text": "",
                    "confidence": 0.0,
                    "num_lines": 0
                }
            
            # Extract text and calculate average confidence
            texts = []
            confidences = []
            
            for line in results[0]:
                if line:
                    text = line[1][0]  # Text is at index [1][0]
                    confidence = line[1][1]  # Confidence is at index [1][1]
                    texts.append(text)
                    confidences.append(confidence)
            
            combined_text = " ".join(texts)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            return {
                "filename": filename,
                "text": combined_text,
                "confidence": avg_confidence,
                "num_lines": len(texts)
            }
            
        except Exception as e:
            return {
                "filename": filename,
                "text": "",
                "confidence": 0.0,
                "num_lines": 0,
                "error": str(e)
            }
    
    @modal.method()
    def extract_text_batch(
        self,
        images: List[dict]  # List of {"filename": str, "image_bytes": bytes}
    ) -> List[dict]:
        """
        Extract text from multiple images in batch
        
        Args:
            images: List of dicts with 'filename' and 'image_bytes' keys
            
        Returns:
            List of dicts with extraction results
        """
        import numpy as np
        from PIL import Image
        
        results = []
        
        for img_data in images:
            filename = img_data.get("filename", "unknown")
            image_bytes = img_data.get("image_bytes")
            
            if not image_bytes:
                results.append({
                    "filename": filename,
                    "text": "",
                    "confidence": 0.0,
                    "num_lines": 0,
                    "error": "No image bytes provided"
                })
                continue
            
            # Process image directly (same logic as extract_text)
            try:
                image = Image.open(io.BytesIO(image_bytes))
                if image.mode != 'RGB':
                    image = image.convert('RGB')
                image_array = np.array(image)
                
                ocr_results = self.ocr_engine.ocr(image_array, cls=True)
                
                if not ocr_results or not ocr_results[0]:
                    results.append({
                        "filename": filename,
                        "text": "",
                        "confidence": 0.0,
                        "num_lines": 0
                    })
                    continue
                
                texts = []
                confidences = []
                
                for line in ocr_results[0]:
                    if line:
                        text = line[1][0]
                        confidence = line[1][1]
                        texts.append(text)
                        confidences.append(confidence)
                
                combined_text = " ".join(texts)
                avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
                
                results.append({
                    "filename": filename,
                    "text": combined_text,
                    "confidence": avg_confidence,
                    "num_lines": len(texts)
                })
            except Exception as e:
                results.append({
                    "filename": filename,
                    "text": "",
                    "confidence": 0.0,
                    "num_lines": 0,
                    "error": str(e)
                })
        
        return results
    
    @modal.method()
    def extract_text_combined(
        self,
        images: List[dict]  # List of {"filename": str, "image_bytes": bytes}
    ) -> dict:
        """
        Extract text from multiple images and combine them
        
        Args:
            images: List of dicts with 'filename' and 'image_bytes' keys
            
        Returns:
            dict with combined text and overall statistics
        """
        import numpy as np
        from PIL import Image
        
        # Process all images
        all_texts = []
        all_confidences = []
        total_lines = 0
        errors = []
        
        for img_data in images:
            filename = img_data.get("filename", "unknown")
            image_bytes = img_data.get("image_bytes")
            
            if not image_bytes:
                errors.append(f"{filename}: No image bytes provided")
                continue
            
            try:
                # Process image
                image = Image.open(io.BytesIO(image_bytes))
                if image.mode != 'RGB':
                    image = image.convert('RGB')
                image_array = np.array(image)
                
                ocr_results = self.ocr_engine.ocr(image_array, cls=True)
                
                if not ocr_results or not ocr_results[0]:
                    continue
                
                texts = []
                confidences = []
                
                for line in ocr_results[0]:
                    if line:
                        text = line[1][0]
                        confidence = line[1][1]
                        texts.append(text)
                        confidences.append(confidence)
                
                if texts:
                    combined_text = " ".join(texts)
                    all_texts.append(f"--- Page: {filename} ---\n{combined_text}")
                    all_confidences.extend(confidences)
                    total_lines += len(texts)
                    
            except Exception as e:
                errors.append(f"{filename}: {str(e)}")
        
        combined_text = "\n\n".join(all_texts) if all_texts else ""
        avg_confidence = sum(all_confidences) / len(all_confidences) if all_confidences else 0.0
        
        return {
            "combined_text": combined_text,
            "total_pages": len(images),
            "total_lines": total_lines,
            "average_confidence": avg_confidence,
            "errors": errors if errors else None
        }


@app.local_entrypoint()
def test_ocr():
    """Test the OCR service with a sample text"""
    from PIL import Image, ImageDraw, ImageFont
    import io
    
    # Create a test image with Russian and English text
    img = Image.new('RGB', (800, 400), color='white')
    draw = ImageDraw.Draw(img)
    
    # Use default font
    test_text = """
    Test OCR Service
    Проверка OCR сервиса
    123-456-7890
    """
    
    draw.text((50, 50), test_text, fill='black')
    
    # Convert to bytes
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes = img_bytes.getvalue()
    
    # Test single image extraction
    print("Testing single image extraction...")
    ocr = PaddleOCR()
    result = ocr.extract_text.remote(img_bytes, "test_image.png")
    
    print(f"\nFilename: {result['filename']}")
    print(f"Extracted Text: {result['text']}")
    print(f"Confidence: {result['confidence']:.2%}")
    print(f"Number of Lines: {result['num_lines']}")
    
    # Test batch extraction
    print("\n" + "="*60)
    print("Testing batch extraction...")
    print("="*60)
    
    images = [
        {"filename": "page1.png", "image_bytes": img_bytes},
        {"filename": "page2.png", "image_bytes": img_bytes},
    ]
    
    combined_result = ocr.extract_text_combined.remote(images)
    
    print(f"\nTotal Pages: {combined_result['total_pages']}")
    print(f"Total Lines: {combined_result['total_lines']}")
    print(f"Average Confidence: {combined_result['average_confidence']:.2%}")
    print(f"\nCombined Text:\n{combined_result['combined_text'][:500]}...")
    
    if combined_result.get('errors'):
        print(f"\nErrors: {combined_result['errors']}")
