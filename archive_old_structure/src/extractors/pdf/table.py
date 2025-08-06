import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
import pandas as pd
import re

from ..base import BaseExtractor
from ...core.models import FinancialReport, ExtractionResult

# Table extraction imports with fallback
try:
    import camelot
    HAS_CAMELOT = True
except ImportError:
    HAS_CAMELOT = False

try:
    import tabula
    HAS_TABULA = True
except ImportError:
    HAS_TABULA = False

import pdfplumber


class TableExtractor(BaseExtractor):
    """Extract tables from PDF financial reports."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize table extractor."""
        super().__init__(config)
        
        self.table_engine = config.get('table_engine', 'auto') if config else 'auto'
        
        # Financial keywords to identify relevant tables
        self.financial_keywords = [
            # English
            'assets', 'liabilities', 'equity', 'revenue', 'income', 'profit', 'loss',
            'cash flow', 'balance sheet', 'income statement', 'financial position',
            'comprehensive income', 'operating', 'net profit', 'total',
            # Chinese
            '资产', '负债', '权益', '收入', '利润', '损失', '现金流',
            '资产负债表', '利润表', '损益表', '财务状况', '综合收益',
            '營業', '淨利潤', '總計', '合計'
        ]
        
        # Key financial items to extract
        self.key_items = {
            'total_assets': ['total assets', '资产总计', '總資產', 'assets total'],
            'total_liabilities': ['total liabilities', '负债总计', '總負債', 'liabilities total'],
            'total_equity': ['total equity', '权益总计', '總權益', 'equity total', "shareholders' equity"],
            'revenue': ['revenue', 'total revenue', '营业收入', '營業收入', 'operating income'],
            'net_profit': ['net profit', 'net income', '净利润', '淨利潤', 'profit for the year'],
            'operating_cash_flow': ['operating cash flow', '经营活动现金流', '經營活動現金流']
        }
    
    def can_handle(self, file_path: Path) -> bool:
        """Check if this extractor can handle the given file."""
        return file_path.suffix.lower() == '.pdf'
    
    def extract_tables(self, file_path: Path) -> List[pd.DataFrame]:
        """Extract all tables from PDF."""
        tables = []
        
        # Try different extraction methods
        if self.table_engine == 'camelot' or (self.table_engine == 'auto' and HAS_CAMELOT):
            tables.extend(self._extract_with_camelot(file_path))
        
        if self.table_engine == 'tabula' or (self.table_engine == 'auto' and HAS_TABULA and len(tables) < 3):
            tables.extend(self._extract_with_tabula(file_path))
        
        if self.table_engine == 'pdfplumber' or (self.table_engine == 'auto' and len(tables) < 3):
            tables.extend(self._extract_with_pdfplumber(file_path))
        
        return tables
    
    def _extract_with_camelot(self, file_path: Path) -> List[pd.DataFrame]:
        """Extract tables using Camelot."""
        tables = []
        try:
            # Try both lattice and stream methods
            for flavor in ['lattice', 'stream']:
                try:
                    camelot_tables = camelot.read_pdf(
                        str(file_path),
                        pages='all',
                        flavor=flavor,
                        suppress_stdout=True
                    )
                    
                    for table in camelot_tables:
                        if table.shape[0] > 2 and table.shape[1] > 1:  # Filter small tables
                            tables.append(table.df)
                            
                except Exception as e:
                    self.logger.debug(f"Camelot {flavor} extraction failed: {str(e)}")
                    
        except Exception as e:
            self.logger.warning(f"Camelot extraction failed: {str(e)}")
            
        return tables
    
    def _extract_with_tabula(self, file_path: Path) -> List[pd.DataFrame]:
        """Extract tables using Tabula."""
        tables = []
        try:
            # Read all tables
            tabula_tables = tabula.read_pdf(
                str(file_path),
                pages='all',
                multiple_tables=True,
                pandas_options={'header': None}
            )
            
            for table in tabula_tables:
                if table.shape[0] > 2 and table.shape[1] > 1:
                    tables.append(table)
                    
        except Exception as e:
            self.logger.warning(f"Tabula extraction failed: {str(e)}")
            
        return tables
    
    def _extract_with_pdfplumber(self, file_path: Path) -> List[pd.DataFrame]:
        """Extract tables using pdfplumber."""
        tables = []
        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_tables = page.extract_tables()
                    
                    for table in page_tables:
                        if table and len(table) > 2 and len(table[0]) > 1:
                            # Convert to DataFrame
                            df = pd.DataFrame(table[1:], columns=table[0])
                            tables.append(df)
                            
        except Exception as e:
            self.logger.warning(f"PDFPlumber table extraction failed: {str(e)}")
            
        return tables
    
    def identify_financial_tables(self, tables: List[pd.DataFrame]) -> List[Dict[str, Any]]:
        """Identify and classify financial tables."""
        financial_tables = []
        
        for idx, table in enumerate(tables):
            # Convert table to string for keyword matching
            table_str = table.to_string().lower()
            
            # Check if table contains financial keywords
            keyword_count = sum(1 for keyword in self.financial_keywords 
                              if keyword.lower() in table_str)
            
            if keyword_count >= 2:  # At least 2 financial keywords
                table_type = self._classify_table(table)
                
                financial_tables.append({
                    'index': idx,
                    'table': table,
                    'type': table_type,
                    'keyword_count': keyword_count
                })
        
        return financial_tables
    
    def _classify_table(self, table: pd.DataFrame) -> str:
        """Classify the type of financial table."""
        table_str = table.to_string().lower()
        
        # Check for specific table types
        if any(keyword in table_str for keyword in ['balance sheet', '资产负债表', '財務狀況表']):
            return 'balance_sheet'
        elif any(keyword in table_str for keyword in ['income statement', '损益表', '利润表', '收益表']):
            return 'income_statement'
        elif any(keyword in table_str for keyword in ['cash flow', '现金流量表', '現金流量表']):
            return 'cash_flow'
        else:
            return 'other_financial'
    
    def extract_values_from_tables(self, tables: List[pd.DataFrame]) -> Dict[str, Any]:
        """Extract key financial values from tables."""
        extracted_values = {}
        
        for table in tables:
            # Try to find key items in the table
            for key, patterns in self.key_items.items():
                if key not in extracted_values:
                    value = self._find_value_in_table(table, patterns)
                    if value is not None:
                        extracted_values[key] = value
        
        return extracted_values
    
    def _find_value_in_table(self, table: pd.DataFrame, patterns: List[str]) -> Optional[float]:
        """Find a specific value in a table based on patterns."""
        # Convert table to string array for searching
        table_array = table.values.astype(str)
        
        for i, row in enumerate(table_array):
            row_str = ' '.join(row).lower()
            
            for pattern in patterns:
                if pattern.lower() in row_str:
                    # Look for numeric values in the same row
                    for j, cell in enumerate(row):
                        value = self._extract_number(cell)
                        if value is not None:
                            return value
                    
                    # Look in the next row if no value found
                    if i + 1 < len(table_array):
                        next_row = table_array[i + 1]
                        for cell in next_row:
                            value = self._extract_number(cell)
                            if value is not None:
                                return value
        
        return None
    
    def _extract_number(self, text: str) -> Optional[float]:
        """Extract number from text."""
        if not isinstance(text, str):
            text = str(text)
        
        # Remove common formatting
        text = text.replace(',', '').replace(' ', '')
        
        # Handle parentheses as negative
        if '(' in text and ')' in text:
            text = '-' + text.replace('(', '').replace(')', '')
        
        # Extract number
        number_pattern = r'-?\d+\.?\d*'
        match = re.search(number_pattern, text)
        
        if match:
            try:
                return float(match.group())
            except ValueError:
                return None
        
        return None
    
    def extract(self, file_path: Path, report: FinancialReport) -> ExtractionResult:
        """Extract financial data from tables in PDF."""
        try:
            # Extract all tables
            tables = self.extract_tables(file_path)
            
            if not tables:
                return ExtractionResult(
                    report=report,
                    error="No tables found in PDF"
                )
            
            # Identify financial tables
            financial_tables = self.identify_financial_tables(tables)
            
            # Extract values
            extracted_values = self.extract_values_from_tables(
                [ft['table'] for ft in financial_tables]
            )
            
            # Return results for further processing
            return ExtractionResult(
                report=report,
                data=None,  # Will be processed by SmartFinancialExtractor
                warnings=[f"Found {len(financial_tables)} financial tables"],
                table_data=extracted_values,
                raw_tables=financial_tables
            )
            
        except Exception as e:
            self.logger.error(f"Error in table extraction: {str(e)}")
            return ExtractionResult(
                report=report,
                error=str(e)
            )