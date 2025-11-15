import os
from typing import List
import io
import fitz  # PyMuPDF
from PIL import Image
import numpy as np
import easyocr
import httpx

# Check if we should use Modal OCR service
USE_MODAL_OCR = os.getenv("USE_MODAL_OCR", "false").lower() == "true"
MODAL_OCR_ENDPOINT = os.getenv("MODAL_OCR_ENDPOINT", "")


class OCRService:
    """Service for extracting text from images using OCR."""

    def __init__(self):
        self._reader = None
        
        if USE_MODAL_OCR:
            print("OCR Service configured to use Modal PaddleOCR HTTP endpoint")
        else:
            print("OCR Service configured to use local EasyOCR")
    
    def _ensure_reader(self):
        """Initialize the EasyOCR reader if not already initialized."""
        if self._reader is None:
            print("Initializing EasyOCR reader for Russian and English (this may take a few minutes on first run)...")
            self._reader = easyocr.Reader(['ru', 'en'], gpu=False)
            print("EasyOCR reader initialized successfully.")
        return self._reader
    
    async def extract_text_from_pdf(self, pdf_bytes: bytes) -> str:
        """
        Extract text from a PDF using OCR. Optimized for Russian scanned documents.
        
        Args:
            pdf_bytes: PDF file content as bytes
            
        Returns:
            Combined text from all pages, separated by newlines
            
        Raises:
            Exception: If OCR extraction fails
        """
        try:
            if USE_MODAL_OCR:
                # Use Modal OCR service HTTP endpoint
                if not MODAL_OCR_ENDPOINT:
                    raise Exception("MODAL_OCR_ENDPOINT not configured")
                
                async with httpx.AsyncClient(timeout=300.0) as client:
                    # Send PDF as multipart form data
                    files = {"file": ("document.pdf", pdf_bytes, "application/pdf")}
                    response = await client.post(
                        f"{MODAL_OCR_ENDPOINT}/extract-text-from-pdf",
                        files=files
                    )
                    response.raise_for_status()
                    result = response.json()
                
                # Check for errors
                if result.get("errors"):
                    error_msg = "; ".join(result["errors"])
                    print(f"[ERROR] OCR processing errors: {error_msg}")
                    raise Exception(f"OCR processing errors: {error_msg}")
                
                if not result.get("combined_text"):
                    raise Exception("No text could be extracted from PDF")
                
                print(f"[DEBUG] Extracted {len(result['combined_text'])} characters from {result.get('total_pages', 0)} pages")
                return result["combined_text"]
            else:
                # Use local EasyOCR with PyMuPDF
                reader = self._ensure_reader()
                all_text = []
                
                # Open PDF from bytes
                pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
                
                print(f"Processing PDF with {len(pdf_document)} pages...")
                
                for page_num in range(len(pdf_document)):
                    page = pdf_document[page_num]
                    
                    # Render page to image at higher resolution for better OCR
                    # zoom=2.0 gives 144 DPI (default is 72 DPI)
                    mat = fitz.Matrix(2.0, 2.0)
                    pix = page.get_pixmap(matrix=mat)
                    
                    # Convert pixmap to PIL Image
                    img_bytes = pix.tobytes("png")
                    image = Image.open(io.BytesIO(img_bytes))
                    
                    # Convert PIL Image to numpy array for EasyOCR
                    image_array = np.array(image)
                    
                    # Perform OCR
                    print(f"Processing page {page_num + 1}/{len(pdf_document)}...")
                    results = reader.readtext(image_array)
                    
                    # Extract text from results
                    page_text = " ".join([result[1] for result in results])
                    
                    if page_text.strip():
                        all_text.append(f"--- Page {page_num + 1} ---\n{page_text}")
                
                pdf_document.close()
                
                if not all_text:
                    raise Exception("No text could be extracted from PDF")
                
                # Combine all text with double newlines between pages
                combined_text = "\n\n".join(all_text)
                print(f"Successfully extracted {len(combined_text)} characters from PDF")
                return combined_text
            
        except Exception as e:
            raise Exception(f"OCR extraction from PDF failed: {str(e)}")
    
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
