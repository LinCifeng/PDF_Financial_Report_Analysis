import re
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
import pdfplumber
import logging

from ..base import BaseExtractor
from ...core.models import FinancialData, FinancialReport, ExtractionResult, DataStatus


class PDFExtractor(BaseExtractor):
    """Extract financial data from PDF reports."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize PDF extractor."""
        super().__init__(config)
        
        # Common patterns for financial items
        self.patterns = {
            # Balance Sheet patterns
            'total_assets': [
                r'total\s+assets?\s*[:：]?\s*([\d,]+)',
                r'資產總[计計額]?\s*[:：]?\s*([\d,]+)',
                r'總資產\s*[:：]?\s*([\d,]+)'
            ],
            'total_liabilities': [
                r'total\s+liabilit(?:y|ies)\s*[:：]?\s*([\d,]+)',
                r'負債總[计計額]?\s*[:：]?\s*([\d,]+)',
                r'總負債\s*[:：]?\s*([\d,]+)'
            ],
            'total_equity': [
                r'total\s+(?:shareholder[s\']?|owner[s\']?)\s*equity\s*[:：]?\s*([\d,]+)',
                r'股東權益總[计計額]?\s*[:：]?\s*([\d,]+)',
                r'權益總[计計額]?\s*[:：]?\s*([\d,]+)'
            ],
            
            # Income Statement patterns
            'revenue': [
                r'(?:total\s+)?(?:operating\s+)?revenue\s*[:：]?\s*([\d,]+)',
                r'營業收入\s*[:：]?\s*([\d,]+)',
                r'收入總[计計額]?\s*[:：]?\s*([\d,]+)'
            ],
            'net_interest_income': [
                r'net\s+interest\s+income\s*[:：]?\s*([\d,]+)',
                r'淨利息收入\s*[:：]?\s*([\d,]+)',
                r'利息收入淨額\s*[:：]?\s*([\d,]+)'
            ],
            'net_profit': [
                r'net\s+(?:profit|income)\s*[:：]?\s*([\d,]+)',
                r'淨利潤\s*[:：]?\s*([\d,]+)',
                r'本[期年]淨利\s*[:：]?\s*([\d,]+)'
            ],
            
            # Cash Flow patterns
            'operating_cash_flow': [
                r'(?:net\s+)?cash\s+(?:from|used\s+in)\s+operating\s+activities?\s*[:：]?\s*([\d,\-\(\)]+)',
                r'經營活動.*現金流量\s*[:：]?\s*([\d,\-\(\)]+)'
            ]
        }
    
    def can_handle(self, file_path: Path) -> bool:
        """Check if this extractor can handle the given file."""
        return file_path.suffix.lower() == '.pdf'
    
    def extract(self, file_path: Path, report: FinancialReport) -> ExtractionResult:
        """Extract financial data from PDF file."""
        try:
            # Initialize financial data
            data = FinancialData(
                company_name=report.company.name,
                fiscal_year=report.fiscal_year,
                quarter=report.quarter,
                report_type=report.report_type.value,
                source_url=report.report_link
            )
            
            # Extract text from PDF
            all_text = self._extract_text_from_pdf(file_path)
            
            if not all_text:
                return ExtractionResult(
                    report=report,
                    error="Failed to extract text from PDF"
                )
            
            # Detect currency and unit
            data.currency = self._detect_currency(all_text)
            data.unit = self._detect_unit(all_text)
            
            # Extract financial items
            extraction_results = {}
            for field, patterns in self.patterns.items():
                value = self._extract_value(all_text, patterns)
                if value is not None:
                    setattr(data, field, self.standardize_number(value, data.unit))
                    extraction_results[field] = value
            
            # Try bank-specific extraction if general extraction is incomplete
            if len(extraction_results) < 3:  # Less than 3 fields extracted
                bank_data = self._extract_bank_specific(all_text, report.company.name)
                for field, value in bank_data.items():
                    if hasattr(data, field) and getattr(data, field) is None:
                        setattr(data, field, value)
            
            # Calculate ratios
            data.calculate_ratios()
            
            # Validate extraction
            warnings = self.validate_extraction(data)
            
            # Set status
            if len(extraction_results) == 0:
                data.extraction_status = DataStatus.FAILED
            elif warnings:
                data.extraction_status = DataStatus.PARTIAL
            else:
                data.extraction_status = DataStatus.SUCCESS
            
            return ExtractionResult(
                report=report,
                data=data,
                warnings=warnings
            )
            
        except Exception as e:
            self.logger.error(f"Error extracting from {file_path}: {str(e)}")
            return ExtractionResult(
                report=report,
                error=str(e)
            )
    
    def _extract_text_from_pdf(self, file_path: Path) -> str:
        """Extract all text from PDF file."""
        all_text = ""
        
        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        all_text += text + "\n"
        except Exception as e:
            self.logger.error(f"Error reading PDF {file_path}: {str(e)}")
        
        return all_text
    
    def _extract_value(self, text: str, patterns: List[str]) -> Optional[str]:
        """Extract value using multiple patterns."""
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
            if matches:
                # Return the last match (usually the most recent/total value)
                return matches[-1]
        return None
    
    def _detect_currency(self, text: str) -> str:
        """Detect currency from text."""
        text_sample = text[:5000].lower()  # Check first part of document
        
        if 'hk$' in text_sample or 'hkd' in text_sample or '港幣' in text_sample:
            return 'HKD'
        elif 'rmb' in text_sample or '人民幣' in text_sample:
            return 'CNY'
        elif 'us$' in text_sample or 'usd' in text_sample:
            return 'USD'
        
        return 'HKD'  # Default for Hong Kong banks
    
    def _detect_unit(self, text: str) -> str:
        """Detect unit from text."""
        text_sample = text[:5000].lower()
        
        if 'in thousands' in text_sample or '千元' in text_sample:
            return 'thousand'
        elif 'in millions' in text_sample or '百萬' in text_sample:
            return 'million'
        elif 'in billions' in text_sample or '十億' in text_sample:
            return 'billion'
        
        return 'thousand'  # Default
    
    def _extract_bank_specific(self, text: str, bank_name: str) -> Dict[str, float]:
        """Extract data using bank-specific patterns."""
        bank_name_lower = bank_name.lower()
        
        if 'za bank' in bank_name_lower:
            return self._extract_za_bank(text)
        elif 'welab' in bank_name_lower:
            return self._extract_welab_bank(text)
        elif 'ant bank' in bank_name_lower:
            return self._extract_ant_bank(text)
        
        return {}
    
    def _extract_za_bank(self, text: str) -> Dict[str, float]:
        """Extract ZA Bank specific data."""
        results = {}
        
        # ZA Bank specific patterns
        patterns = {
            'total_assets': r'總資產\s*Total assets\s*([\d,]+)',
            'total_equity': r'總權益\s*Total equity\s*([\d,]+)',
            'net_profit': r'年度利潤\s*Profit for the year\s*([\d,\-\(\)]+)'
        }
        
        for field, pattern in patterns.items():
            value = self._extract_value(text, [pattern])
            if value:
                results[field] = self.standardize_number(value, 'thousand')
        
        return results
    
    def _extract_welab_bank(self, text: str) -> Dict[str, float]:
        """Extract WeLab Bank specific data."""
        # Similar implementation for WeLab Bank
        return {}
    
    def _extract_ant_bank(self, text: str) -> Dict[str, float]:
        """Extract Ant Bank specific data."""
        # Similar implementation for Ant Bank
        return {}