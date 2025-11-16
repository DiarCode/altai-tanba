"""
Client for using the Modal OCR service
"""

import modal
from typing import List


def extract_text_from_image(image_bytes: bytes, filename: str = "image") -> dict:
    """
    Extract text from a single image using Modal OCR service
    
    Args:
        image_bytes: Image content as bytes
        filename: Optional filename for reference
    
    Returns:
        dict with extraction results
    """
    # Connect to the deployed Modal class
    PaddleOCR = modal.Cls.from_name("paddleocr-service", "PaddleOCR")
    ocr = PaddleOCR()
    
    # Extract text
    result = ocr.extract_text.remote(
        image_bytes=image_bytes,
        filename=filename
    )
    
    return result


def extract_text_from_images_batch(
    images: List[tuple[str, bytes]]  # List of (filename, image_bytes)
) -> List[dict]:
    """
    Extract text from multiple images in batch
    
    Args:
        images: List of tuples containing (filename, image_bytes)
    
    Returns:
        List of dicts with extraction results
    """
    PaddleOCR = modal.Cls.from_name("paddleocr-service", "PaddleOCR")
    ocr = PaddleOCR()
    
    # Convert to the format expected by the Modal method
    images_data = [
        {"filename": filename, "image_bytes": image_bytes}
        for filename, image_bytes in images
    ]
    
    results = ocr.extract_text_batch.remote(images=images_data)
    
    return results


def extract_text_combined(
    images: List[tuple[str, bytes]]  # List of (filename, image_bytes)
) -> str:
    """
    Extract text from multiple images and return combined text
    
    Args:
        images: List of tuples containing (filename, image_bytes)
    
    Returns:
        Combined text from all images
    """
    PaddleOCR = modal.Cls.from_name("paddleocr-service", "PaddleOCR")
    ocr = PaddleOCR()
    
    # Convert to the format expected by the Modal method
    images_data = [
        {"filename": filename, "image_bytes": image_bytes}
        for filename, image_bytes in images
    ]
    
    result = ocr.extract_text_combined.remote(images=images_data)
    
    return result["combined_text"]


if __name__ == "__main__":
    # Example usage
    from PIL import Image, ImageDraw
    import io
    
    print("Creating test image...")
    
    # Create a test image
    img = Image.new('RGB', (800, 400), color='white')
    draw = ImageDraw.Draw(img)
    
    test_text = """
    Sample Document Text
    Образец текста документа
    Invoice #12345
    Total: $1,000.00
    """
    
    draw.text((50, 50), test_text, fill='black')
    
    # Convert to bytes
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes = img_bytes.getvalue()
    
    # Test single image
    print("\nTesting single image extraction...")
    result = extract_text_from_image(img_bytes, "test.png")
    
    print(f"Filename: {result['filename']}")
    print(f"Text: {result['text']}")
    print(f"Confidence: {result['confidence']:.2%}")
    
    # Test batch processing
    print("\n" + "="*60)
    print("Testing batch extraction...")
    print("="*60)
    
    images = [
        ("page1.png", img_bytes),
        ("page2.png", img_bytes),
    ]
    
    combined_text = extract_text_combined(images)
    print(f"\nCombined Text:\n{combined_text}")
