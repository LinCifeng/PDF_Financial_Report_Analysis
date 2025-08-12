"""
OCR提取策略
OCR Extraction Strategy
"""

from typing import Any
from .base_strategy import BaseStrategy, ExtractionResult

# 尝试导入OCR依赖
try:
    import pytesseract
    from PIL import Image
    import fitz  # PyMuPDF
    HAS_OCR = True
except ImportError:
    HAS_OCR = False


class OCRStrategy(BaseStrategy):
    """OCR提取策略（用于扫描版PDF）"""
    
    def __init__(self):
        super().__init__(name="ocr")
        self.has_ocr = HAS_OCR
    
    def can_handle(self, content: Any) -> bool:
        """判断是否需要OCR处理"""
        if not self.has_ocr:
            return False
        
        # 如果是字符串路径
        if isinstance(content, str):
            return content.endswith('.pdf')
        
        # 如果是pdfplumber对象，检查是否为扫描版
        if hasattr(content, 'pages'):
            return self._is_scanned_pdf(content)
        
        return False
    
    def _is_scanned_pdf(self, pdf) -> bool:
        """判断PDF是否为扫描版"""
        if not hasattr(pdf, 'pages') or not pdf.pages:
            return False
        
        # 检查前3页
        pages_to_check = min(3, len(pdf.pages))
        total_chars = 0
        
        for i in range(pages_to_check):
            text = pdf.pages[i].extract_text() or ""
            total_chars += len(text.strip())
        
        avg_chars = total_chars / pages_to_check
        
        # 如果平均每页少于50个字符，认为是扫描版
        is_scanned = avg_chars < 50
        
        if is_scanned:
            print(f"  ⚠️ 检测到扫描版PDF (平均{avg_chars:.0f}字符/页)")
        
        return is_scanned
    
    def extract(self, content: Any, **kwargs) -> ExtractionResult:
        """使用OCR提取文本"""
        result = ExtractionResult(method="ocr")
        
        if not self.has_ocr:
            return result
        
        # 获取PDF路径
        if isinstance(content, str) and content.endswith('.pdf'):
            pdf_path = content
        else:
            pdf_path = kwargs.get('pdf_path')
        
        if not pdf_path:
            return result
        
        print(f"  🔍 开始OCR处理...")
        
        try:
            import fitz
            import io
            
            # 打开PDF
            pdf_doc = fitz.open(pdf_path)
            ocr_texts = []
            
            # 处理前20页
            pages_to_process = min(20, len(pdf_doc))
            
            for page_num in range(pages_to_process):
                page = pdf_doc[page_num]
                
                # 将页面转换为图像
                mat = fitz.Matrix(2, 2)  # 放大2倍
                pix = page.get_pixmap(matrix=mat)
                img_data = pix.pil_tobytes(format="PNG")
                
                # 使用PIL打开图像
                img = Image.open(io.BytesIO(img_data))
                
                # OCR识别
                try:
                    text = pytesseract.image_to_string(img, lang='chi_sim+eng')
                except:
                    text = pytesseract.image_to_string(img, lang='eng')
                
                ocr_texts.append(text)
                
                # 显示进度
                if (page_num + 1) % 5 == 0:
                    print(f"    已处理 {page_num + 1}/{pages_to_process} 页")
            
            pdf_doc.close()
            
            # 合并所有文本
            full_text = "\n".join(ocr_texts)
            print(f"  ✅ OCR完成，提取了 {len(full_text)} 个字符")
            
            # OCR策略只返回文本，不进行数据提取
            result.ocr_text = full_text
            
        except Exception as e:
            print(f"  ❌ OCR失败: {str(e)[:100]}")
        
        return result