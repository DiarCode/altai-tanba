import io
from typing import List
from PIL import Image
import numpy as np
import easyocr


class OCRService:
    """Service for extracting text from images using OCR."""

    def __init__(self):
        # Initialize EasyOCR reader for Russian and English
        # This will download models on first use
        self.reader = easyocr.Reader(['ru', 'en'], gpu=False)

    async def extract_text_from_images(self, images: List[tuple[str, bytes]]) -> str:
        """
        Extract text from multiple images using OCR.
        
        Args:
            images: List of tuples containing (filename, image_bytes)
            
        Returns:
            Combined text from all images, separated by newlines
            
        Raises:
            Exception: If OCR extraction fails
        """
        try:
            all_text = []
            
            for filename, image_bytes in images:
                # Convert bytes to PIL Image
                image = Image.open(io.BytesIO(image_bytes))
                
                # Convert PIL Image to numpy array for EasyOCR
                image_array = np.array(image)
                
                # Perform OCR
                # readtext returns list of (bbox, text, confidence)
                results = self.reader.readtext(image_array)
                
                # Extract just the text from results
                page_text = " ".join([result[1] for result in results])
                
                if page_text.strip():
                    all_text.append(f"--- Page: {filename} ---\n{page_text}")
            
            if not all_text:
                raise Exception("No text could be extracted from any images")
            
            # Combine all text with double newlines between pages
            combined_text = "\n\n".join(all_text)
            return combined_text
            
        except Exception as e:
            raise Exception(f"OCR extraction failed: {str(e)}")

    async def extract_text_from_single_image(self, image_bytes: bytes) -> str:
        """
        Extract text from a single image.
        
        Args:
            image_bytes: Image content as bytes
            
        Returns:
            Extracted text
        """
        try:
            image = Image.open(io.BytesIO(image_bytes))
            image_array = np.array(image)
            results = self.reader.readtext(image_array)
            text = " ".join([result[1] for result in results])
            return text
        except Exception as e:
            raise Exception(f"OCR extraction failed: {str(e)}")


# Singleton instance
ocr_service = OCRService()
