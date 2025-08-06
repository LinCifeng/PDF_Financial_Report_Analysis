from pathlib import Path
from typing import Optional, List, Dict, Any
import logging

from .base import BaseExtractor
from .pdf import PDFExtractor
from .smart import SmartFinancialExtractor
from ..core.models import FinancialReport, ExtractionResult


class ExtractorFactory:
    """Factory for creating appropriate extractors."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize extractor factory.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Use smart extractor by default if available
        use_smart = config.get('use_smart_extractor', True) if config else True
        
        # Register available extractors
        if use_smart:
            try:
                self.extractors = [
                    SmartFinancialExtractor(config)
                ]
                self.logger.info("Using SmartFinancialExtractor")
            except Exception as e:
                self.logger.warning(f"Failed to initialize SmartFinancialExtractor: {str(e)}")
                self.logger.info("Falling back to PDFExtractor")
                self.extractors = [
                    PDFExtractor(config)
                ]
        else:
            self.extractors = [
                PDFExtractor(config)
            ]
    
    def get_extractor(self, file_path: Path) -> Optional[BaseExtractor]:
        """Get appropriate extractor for file.
        
        Args:
            file_path: Path to the file
        
        Returns:
            Appropriate extractor or None
        """
        for extractor in self.extractors:
            if extractor.can_handle(file_path):
                return extractor
        
        self.logger.warning(f"No extractor found for file: {file_path}")
        return None
    
    def extract(self, file_path: Path, report: FinancialReport) -> ExtractionResult:
        """Extract data from file using appropriate extractor.
        
        Args:
            file_path: Path to the file
            report: Report metadata
        
        Returns:
            ExtractionResult
        """
        extractor = self.get_extractor(file_path)
        
        if extractor is None:
            return ExtractionResult(
                report=report,
                error=f"No extractor available for file type: {file_path.suffix}"
            )
        
        return extractor.extract(file_path, report)