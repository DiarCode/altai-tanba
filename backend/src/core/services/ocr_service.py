import os
from typing import List

# Check if we should use Modal OCR service
USE_MODAL_OCR = os.getenv("USE_MODAL_OCR", "false").lower() == "true"

if USE_MODAL_OCR:
    import modal
else:
    import io
    from PIL import Image
    import numpy as np
    import easyocr


class OCRService:
    """Service for extracting text from images using OCR."""

    def __init__(self):
        # Initialize both to None regardless of mode
        self._modal_app = None
        self._modal_ocr = None
        self._reader = None
        
        if USE_MODAL_OCR:
            print("OCR Service configured to use Modal PaddleOCR")
        else:
            print("OCR Service configured to use local EasyOCR")
    
    def _ensure_modal_ocr(self):
        """Initialize Modal OCR client if not already initialized."""
        if self._modal_ocr is None:
            try:
                # Use modal.Cls.from_name to get the deployed class
                PaddleOCR = modal.Cls.from_name("paddleocr-service", "PaddleOCR")
                # Create an instance
                self._modal_ocr = PaddleOCR()
                print("Connected to Modal OCR service successfully.")
            except Exception as e:
                import traceback
                traceback.print_exc()
                raise Exception(f"Failed to connect to Modal OCR service: {str(e)}")
        return self._modal_ocr
    
    def _ensure_reader(self):
        """Initialize the EasyOCR reader if not already initialized."""
        if self._reader is None:
            print("Initializing EasyOCR reader (this may take a few minutes on first run)...")
            self._reader = easyocr.Reader(['ru', 'en'], gpu=False)
            print("EasyOCR reader initialized successfully.")
        return self._reader
    
    def pre_initialize(self):
        """Pre-initialize the OCR service based on the current mode."""
        if USE_MODAL_OCR:
            # For Modal OCR, just ensure connection is possible
            print("Modal OCR mode - skipping local model initialization")
            # We don't connect here to avoid cold start, connection happens on first use
        else:
            # For local OCR, initialize the reader
            self._ensure_reader()

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
            if USE_MODAL_OCR:
                # Use Modal OCR service
                ocr = self._ensure_modal_ocr()
                
                # Convert to Modal format
                images_data = [
                    {"filename": filename, "image_bytes": image_bytes}
                    for filename, image_bytes in images
                ]
                
                # Call Modal OCR - use exact same pattern as LLM client
                result = ocr.extract_text_combined.remote(images=images_data)
                
                if not result["combined_text"]:
                    raise Exception("No text could be extracted from any images")
                
                return result["combined_text"]
            else:
                # Use local EasyOCR
                reader = self._ensure_reader()
                all_text = []
                
                for filename, image_bytes in images:
                    # Convert bytes to PIL Image
                    image = Image.open(io.BytesIO(image_bytes))
                    
                    # Convert PIL Image to numpy array for EasyOCR
                    image_array = np.array(image)
                    
                    # Perform OCR
                    # readtext returns list of (bbox, text, confidence)
                    results = reader.readtext(image_array)
                    
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
            if USE_MODAL_OCR:
                # Use Modal OCR service
                ocr = self._ensure_modal_ocr()
                result = ocr.extract_text.remote(
                    image_bytes=image_bytes,
                    filename="image"
                )
                return result["text"]
            else:
                # Use local EasyOCR
                reader = self._ensure_reader()
                image = Image.open(io.BytesIO(image_bytes))
                image_array = np.array(image)
                results = reader.readtext(image_array)
                text = " ".join([result[1] for result in results])
                return text
        except Exception as e:
            raise Exception(f"OCR extraction failed: {str(e)}")


# Singleton instance
ocr_service = OCRService()
