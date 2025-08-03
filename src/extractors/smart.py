import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
import time
from datetime import datetime

from .base import BaseExtractor
from .pdf import PDFExtractor, OCRExtractor, TableExtractor
from .llm import ImprovedLLMExtractor as LLMExtractor
from ..core.models import FinancialData, FinancialReport, ExtractionResult, DataStatus


class SmartFinancialExtractor(BaseExtractor):
    """Smart financial data extractor that combines multiple extraction methods."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize smart extractor with all sub-extractors."""
        super().__init__(config)
        
        # Initialize sub-extractors
        self.pdf_extractor = PDFExtractor(config)
        self.ocr_extractor = OCRExtractor(config)
        self.table_extractor = TableExtractor(config)
        self.llm_extractor = LLMExtractor(config)
        
        # Extraction settings
        self.use_ocr = config.get('use_ocr', True) if config else True
        self.use_llm = config.get('use_llm', True) if config else True
        self.confidence_threshold = config.get('confidence_threshold', 0.7) if config else 0.7
    
    def can_handle(self, file_path: Path) -> bool:
        """Check if this extractor can handle the given file."""
        return file_path.suffix.lower() == '.pdf'
    
    def extract(self, file_path: Path, report: FinancialReport) -> ExtractionResult:
        """Extract financial data using multiple methods."""
        start_time = time.time()
        
        try:
            self.logger.info(f"Starting smart extraction for {report.company.name} {report.fiscal_year}")
            
            # Initialize result containers
            regex_data = {}
            table_data = {}
            ocr_text = ""
            llm_data = {}
            warnings = []
            
            # Step 1: Traditional PDF text extraction with regex
            self.logger.info("Step 1: PDF text extraction")
            pdf_result = self.pdf_extractor.extract(file_path, report)
            
            if pdf_result.data:
                # Convert FinancialData to dict for merging
                regex_data = {
                    'total_assets': pdf_result.data.total_assets,
                    'total_liabilities': pdf_result.data.total_liabilities,
                    'total_equity': pdf_result.data.total_equity,
                    'revenue': pdf_result.data.revenue,
                    'net_profit': pdf_result.data.net_profit,
                    'operating_cash_flow': pdf_result.data.operating_cash_flow,
                }
                warnings.extend(pdf_result.warnings)
            
            # Get the extracted text
            pdf_text = self.pdf_extractor._extract_text_from_pdf(file_path)
            
            # Step 2: Table extraction
            self.logger.info("Step 2: Table extraction")
            table_result = self.table_extractor.extract(file_path, report)
            
            if hasattr(table_result, 'table_data') and table_result.table_data:
                table_data = table_result.table_data
                warnings.extend(table_result.warnings)
            
            # Step 3: OCR extraction (if PDF text is insufficient)
            if self.use_ocr and self._should_use_ocr(regex_data, table_data):
                self.logger.info("Step 3: OCR extraction (text seems insufficient)")
                ocr_result = self.ocr_extractor.extract_text_with_ocr(file_path)
                
                if ocr_result:
                    ocr_text = ocr_result
                    # Try regex on OCR text
                    ocr_regex_data = self._apply_regex_to_text(ocr_text)
                    # Merge OCR results
                    for key, value in ocr_regex_data.items():
                        if key not in regex_data or regex_data[key] is None:
                            regex_data[key] = value
                    warnings.append("Used OCR extraction")
            
            # Step 4: LLM verification and extraction
            if self.use_llm:
                self.logger.info("Step 4: LLM verification and extraction")
                
                # Combine all text sources
                combined_text = pdf_text
                if ocr_text:
                    combined_text += "\n\n--- OCR Extracted Text ---\n" + ocr_text
                
                # Call LLM for extraction and verification
                llm_data = self.llm_extractor.extract_with_llm(
                    text_content=combined_text,
                    company_name=report.company.name,
                    fiscal_year=report.fiscal_year,
                    regex_results=regex_data,
                    table_results=table_data
                )
                
                if llm_data:
                    warnings.append(f"LLM confidence: {llm_data.get('confidence', 0):.2f}")
            
            # Step 5: Merge and verify results
            self.logger.info("Step 5: Merging results from all sources")
            final_data = self._merge_results(regex_data, table_data, llm_data)
            
            # Create FinancialData object
            financial_data = FinancialData(
                company_name=report.company.name,
                fiscal_year=report.fiscal_year,
                quarter=report.quarter,
                report_type=report.report_type.value,
                currency=llm_data.get('currency', 'HKD'),
                unit=llm_data.get('unit', 'thousand'),
                
                # Financial values
                total_assets=final_data.get('total_assets'),
                total_liabilities=final_data.get('total_liabilities'),
                total_equity=final_data.get('total_equity'),
                revenue=final_data.get('revenue'),
                net_profit=final_data.get('net_profit'),
                operating_cash_flow=final_data.get('operating_cash_flow'),
                
                # Metadata
                extraction_date=datetime.now(),
                source_url=report.report_link
            )
            
            # Calculate financial ratios
            financial_data.calculate_ratios()
            
            # Validate extraction
            validation_warnings = self.validate_extraction(financial_data)
            warnings.extend(validation_warnings)
            
            # Determine extraction status
            extracted_count = sum(1 for v in final_data.values() if v is not None)
            
            if extracted_count == 0:
                financial_data.extraction_status = DataStatus.FAILED
            elif extracted_count < 3 or validation_warnings:
                financial_data.extraction_status = DataStatus.PARTIAL
            else:
                financial_data.extraction_status = DataStatus.SUCCESS
            
            # Add extraction notes
            financial_data.extraction_notes = warnings
            if llm_data.get('llm_notes'):
                financial_data.extraction_notes.append(f"LLM notes: {llm_data['llm_notes']}")
            
            # Log extraction time
            extraction_time = time.time() - start_time
            self.logger.info(f"Extraction completed in {extraction_time:.2f} seconds")
            warnings.append(f"Extraction time: {extraction_time:.2f}s")
            
            return ExtractionResult(
                report=report,
                data=financial_data,
                warnings=warnings
            )
            
        except Exception as e:
            self.logger.error(f"Error in smart extraction: {str(e)}")
            return ExtractionResult(
                report=report,
                error=str(e)
            )
    
    def _should_use_ocr(self, regex_data: Dict, table_data: Dict) -> bool:
        """Determine if OCR extraction is needed."""
        # Count extracted fields
        extracted_count = 0
        
        for data_dict in [regex_data, table_data]:
            extracted_count += sum(1 for v in data_dict.values() if v is not None)
        
        # Use OCR if we have less than 3 fields extracted
        return extracted_count < 3
    
    def _apply_regex_to_text(self, text: str) -> Dict[str, Any]:
        """Apply regex patterns to extracted text."""
        results = {}
        
        # Use patterns from PDF extractor
        for field, patterns in self.pdf_extractor.patterns.items():
            value = self.pdf_extractor._extract_value(text, patterns)
            if value:
                results[field] = self.pdf_extractor.standardize_number(value)
        
        return results
    
    def _merge_results(self, 
                      regex_data: Dict[str, Any],
                      table_data: Dict[str, Any],
                      llm_data: Dict[str, Any]) -> Dict[str, Any]:
        """Merge results from different sources with intelligent priority."""
        
        final_data = {}
        fields = [
            'total_assets', 'total_liabilities', 'total_equity',
            'revenue', 'net_profit', 'operating_cash_flow'
        ]
        
        for field in fields:
            # Collect all available values for this field
            candidates = []
            
            if field in regex_data and regex_data[field] is not None:
                candidates.append(('regex', regex_data[field]))
            
            if field in table_data and table_data[field] is not None:
                candidates.append(('table', table_data[field]))
            
            if field in llm_data and llm_data[field] is not None:
                confidence = llm_data.get('confidence', 0.5)
                candidates.append(('llm', llm_data[field], confidence))
            
            # Select the best value
            if candidates:
                # If LLM has high confidence, prefer it
                llm_candidates = [c for c in candidates if c[0] == 'llm' and len(c) > 2 and c[2] >= self.confidence_threshold]
                if llm_candidates:
                    final_data[field] = llm_candidates[0][1]
                    self.logger.debug(f"{field}: Using LLM value with confidence {llm_candidates[0][2]}")
                # Otherwise, prefer table data over regex
                elif any(c[0] == 'table' for c in candidates):
                    final_data[field] = next(c[1] for c in candidates if c[0] == 'table')
                    self.logger.debug(f"{field}: Using table value")
                else:
                    final_data[field] = candidates[0][1]
                    self.logger.debug(f"{field}: Using {candidates[0][0]} value")
        
        return final_data