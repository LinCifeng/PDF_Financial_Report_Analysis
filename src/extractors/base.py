from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
import logging
from pathlib import Path

from ..core.models import FinancialData, FinancialReport, ExtractionResult, DataStatus


class BaseExtractor(ABC):
    """Base class for financial report extractors."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize extractor.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    def can_handle(self, file_path: Path) -> bool:
        """Check if this extractor can handle the given file.
        
        Args:
            file_path: Path to the file
        
        Returns:
            True if can handle, False otherwise
        """
        pass
    
    @abstractmethod
    def extract(self, file_path: Path, report: FinancialReport) -> ExtractionResult:
        """Extract financial data from file.
        
        Args:
            file_path: Path to the file
            report: Report metadata
        
        Returns:
            ExtractionResult with extracted data or error
        """
        pass
    
    def validate_extraction(self, data: FinancialData) -> List[str]:
        """Validate extracted data and return warnings.
        
        Args:
            data: Extracted financial data
        
        Returns:
            List of warning messages
        """
        warnings = []
        
        # Check for basic data completeness
        if data.total_assets is None:
            warnings.append("Missing total assets")
        
        if data.total_equity is None:
            warnings.append("Missing total equity")
        
        if data.net_profit is None:
            warnings.append("Missing net profit")
        
        # Check data consistency
        if (data.total_assets is not None and 
            data.total_liabilities is not None and 
            data.total_equity is not None):
            
            # Assets = Liabilities + Equity
            expected_assets = data.total_liabilities + data.total_equity
            if abs(data.total_assets - expected_assets) > 1:  # Allow small rounding difference
                warnings.append(
                    f"Balance sheet doesn't balance: Assets={data.total_assets}, "
                    f"Liabilities+Equity={expected_assets}"
                )
        
        return warnings
    
    def standardize_number(self, value: Any, unit: str = "thousand") -> Optional[float]:
        """Standardize number to base unit (thousands by default).
        
        Args:
            value: Raw value (string or number)
            unit: Current unit of the value
        
        Returns:
            Standardized float value or None
        """
        if value is None or value == '' or value == '-':
            return None
        
        try:
            # Remove common formatting
            if isinstance(value, str):
                value = value.replace(',', '').replace(' ', '')
                value = value.replace('(', '-').replace(')', '')
                value = value.strip()
            
            # Convert to float
            num = float(value)
            
            # Convert to thousands if needed
            if unit.lower() == "million":
                num *= 1000
            elif unit.lower() == "billion":
                num *= 1000000
            elif unit.lower() == "actual":
                num /= 1000
            
            return num
            
        except (ValueError, TypeError):
            self.logger.warning(f"Failed to parse number: {value}")
            return None
    
    def extract_currency(self, text: str) -> str:
        """Extract currency from text.
        
        Args:
            text: Text containing currency information
        
        Returns:
            Currency code (default: HKD)
        """
        text_lower = text.lower()
        
        if 'hkd' in text_lower or 'hk$' in text_lower or '港幣' in text:
            return 'HKD'
        elif 'rmb' in text_lower or 'cny' in text_lower or '人民幣' in text:
            return 'CNY'
        elif 'usd' in text_lower or 'us$' in text_lower:
            return 'USD'
        else:
            return 'HKD'  # Default for Hong Kong banks