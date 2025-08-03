import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
import numpy as np
from PIL import Image
try:
    import fitz  # PyMuPDF
    HAS_FITZ = True
except ImportError:
    HAS_FITZ = False
try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False

from ..base import BaseExtractor
from ...core.models import FinancialReport, ExtractionResult, DataStatus

# OCR imports - with fallback options
try:
    from paddleocr import PaddleOCR
    HAS_PADDLE = True
except ImportError:
    HAS_PADDLE = False
    
try:
    import pytesseract
    HAS_TESSERACT = True
except ImportError:
    HAS_TESSERACT = False


class OCRExtractor(BaseExtractor):
    """Extract text from scanned PDFs using OCR."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize OCR extractor."""
        super().__init__(config)
        
        self.ocr_engine = config.get('ocr_engine', 'paddle') if config else 'paddle'
        self.languages = config.get('languages', ['ch', 'en']) if config else ['ch', 'en']
        
        # Initialize OCR engine
        if self.ocr_engine == 'paddle' and HAS_PADDLE:
            self.ocr = PaddleOCR(
                use_angle_cls=True,
                lang='ch' if 'ch' in self.languages else 'en',
                use_gpu=False,
                show_log=False
            )
        elif HAS_TESSERACT:
            self.ocr_engine = 'tesseract'
            self.logger.info("Using Tesseract as OCR engine")
        else:
            raise ImportError("No OCR engine available. Please install paddleocr or pytesseract.")
    
    def can_handle(self, file_path: Path) -> bool:
        """Check if this extractor can handle the given file."""
        return file_path.suffix.lower() == '.pdf'
    
    def extract_text_with_ocr(self, file_path: Path) -> str:
        """Extract text from PDF using OCR."""
        all_text = []
        
        try:
            # Open PDF and convert to images
            if not HAS_FITZ:
                self.logger.error("PyMuPDF (fitz) not installed")
                return ""
            
            pdf_document = fitz.open(str(file_path))
            
            for page_num in range(len(pdf_document)):
                page = pdf_document[page_num]
                
                # Convert page to image
                pix = page.get_pixmap(dpi=300)
                img_data = pix.tobytes("png")
                
                # Convert to numpy array
                if HAS_CV2:
                    nparr = np.frombuffer(img_data, np.uint8)
                    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                else:
                    # Use PIL as fallback
                    from io import BytesIO
                    img = Image.open(BytesIO(img_data))
                    img = np.array(img)
                
                # Perform OCR
                if self.ocr_engine == 'paddle' and HAS_PADDLE:
                    text = self._paddle_ocr(img)
                else:
                    text = self._tesseract_ocr(img)
                
                all_text.append(f"\n--- Page {page_num + 1} ---\n{text}")
                
            pdf_document.close()
            
        except Exception as e:
            self.logger.error(f"Error during OCR extraction: {str(e)}")
            return ""
        
        return "\n".join(all_text)
    
    def _paddle_ocr(self, image: np.ndarray) -> str:
        """Perform OCR using PaddleOCR."""
        result = self.ocr.ocr(image, cls=True)
        
        # Extract text from results
        lines = []
        if result and result[0]:
            for line in result[0]:
                if line[1]:
                    text = line[1][0]
                    confidence = line[1][1]
                    if confidence > 0.8:  # Only include high confidence text
                        lines.append(text)
        
        return "\n".join(lines)
    
    def _tesseract_ocr(self, image: np.ndarray) -> str:
        """Perform OCR using Tesseract."""
        # Convert to PIL Image
        if HAS_CV2:
            pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        else:
            # Assume image is already in RGB format
            pil_image = Image.fromarray(image)
        
        # Language mapping
        lang_map = {
            'ch': 'chi_sim+chi_tra',
            'en': 'eng'
        }
        
        langs = []
        for lang in self.languages:
            if lang in lang_map:
                langs.append(lang_map[lang])
        
        lang_str = '+'.join(langs) if langs else 'eng'
        
        # Perform OCR
        try:
            text = pytesseract.image_to_string(pil_image, lang=lang_str)
            return text
        except Exception as e:
            self.logger.error(f"Tesseract OCR error: {str(e)}")
            return ""
    
    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """Preprocess image for better OCR results."""
        if not HAS_CV2:
            # Return image as-is if cv2 not available
            return image
            
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply threshold to get binary image
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Denoise
        denoised = cv2.fastNlMeansDenoising(binary)
        
        # Deskew if needed
        coords = np.column_stack(np.where(denoised > 0))
        if len(coords) > 0:
            angle = cv2.minAreaRect(coords)[-1]
            if angle < -45:
                angle = -(90 + angle)
            else:
                angle = -angle
                
            if abs(angle) > 0.5:
                (h, w) = denoised.shape[:2]
                center = (w // 2, h // 2)
                M = cv2.getRotationMatrix2D(center, angle, 1.0)
                denoised = cv2.warpAffine(denoised, M, (w, h), 
                                         flags=cv2.INTER_CUBIC, 
                                         borderMode=cv2.BORDER_REPLICATE)
        
        return denoised
    
    def extract(self, file_path: Path, report: FinancialReport) -> ExtractionResult:
        """Extract financial data from PDF using OCR."""
        try:
            # Extract text using OCR
            ocr_text = self.extract_text_with_ocr(file_path)
            
            if not ocr_text:
                return ExtractionResult(
                    report=report,
                    error="Failed to extract text using OCR"
                )
            
            # Store OCR text for further processing
            return ExtractionResult(
                report=report,
                data=None,  # Will be processed by SmartFinancialExtractor
                warnings=["OCR extraction completed, awaiting further processing"],
                raw_text=ocr_text
            )
            
        except Exception as e:
            self.logger.error(f"Error in OCR extraction: {str(e)}")
            return ExtractionResult(
                report=report,
                error=str(e)
            )