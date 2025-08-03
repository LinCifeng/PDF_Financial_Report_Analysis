from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum


class ReportType(Enum):
    """Types of financial reports."""
    ANNUAL = "annual"
    INTERIM = "interim"
    QUARTERLY = "quarterly"
    UNKNOWN = "unknown"


class DataStatus(Enum):
    """Status of data extraction."""
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
    PENDING = "pending"


@dataclass
class CompanyInfo:
    """Company information."""
    id: str
    name: str
    website: Optional[str] = None
    sector: Optional[str] = None
    country: str = "HK"


@dataclass
class FinancialReport:
    """Financial report metadata."""
    company: CompanyInfo
    fiscal_year: int
    quarter: Optional[str] = None
    report_type: ReportType = ReportType.ANNUAL
    report_link: str = ""
    local_path: Optional[str] = None
    download_date: Optional[datetime] = None
    status: DataStatus = DataStatus.PENDING


@dataclass
class FinancialData:
    """Standardized financial data extracted from reports."""
    # Metadata
    company_name: str
    fiscal_year: int
    quarter: Optional[str] = None
    report_type: str = ""
    currency: str = "HKD"
    unit: str = "thousand"
    
    # Balance Sheet
    total_assets: Optional[float] = None
    current_assets: Optional[float] = None
    non_current_assets: Optional[float] = None
    total_liabilities: Optional[float] = None
    current_liabilities: Optional[float] = None
    non_current_liabilities: Optional[float] = None
    total_equity: Optional[float] = None
    
    # Income Statement
    revenue: Optional[float] = None
    operating_income: Optional[float] = None
    operating_expenses: Optional[float] = None
    net_interest_income: Optional[float] = None
    net_profit: Optional[float] = None
    net_profit_before_tax: Optional[float] = None
    
    # Cash Flow
    operating_cash_flow: Optional[float] = None
    investing_cash_flow: Optional[float] = None
    financing_cash_flow: Optional[float] = None
    net_cash_flow: Optional[float] = None
    
    # Key Ratios
    roe: Optional[float] = None  # Return on Equity
    roa: Optional[float] = None  # Return on Assets
    capital_adequacy_ratio: Optional[float] = None
    cost_income_ratio: Optional[float] = None
    
    # Metadata
    extraction_date: datetime = field(default_factory=datetime.now)
    source_url: str = ""
    extraction_status: DataStatus = DataStatus.PENDING
    extraction_notes: List[str] = field(default_factory=list)
    raw_data: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = {
            'company_name': self.company_name,
            'fiscal_year': self.fiscal_year,
            'quarter': self.quarter,
            'report_type': self.report_type,
            'currency': self.currency,
            'unit': self.unit,
            
            # Balance Sheet
            'total_assets': self.total_assets,
            'current_assets': self.current_assets,
            'non_current_assets': self.non_current_assets,
            'total_liabilities': self.total_liabilities,
            'current_liabilities': self.current_liabilities,
            'non_current_liabilities': self.non_current_liabilities,
            'total_equity': self.total_equity,
            
            # Income Statement
            'revenue': self.revenue,
            'operating_income': self.operating_income,
            'operating_expenses': self.operating_expenses,
            'net_interest_income': self.net_interest_income,
            'net_profit': self.net_profit,
            'net_profit_before_tax': self.net_profit_before_tax,
            
            # Cash Flow
            'operating_cash_flow': self.operating_cash_flow,
            'investing_cash_flow': self.investing_cash_flow,
            'financing_cash_flow': self.financing_cash_flow,
            'net_cash_flow': self.net_cash_flow,
            
            # Ratios
            'roe': self.roe,
            'roa': self.roa,
            'capital_adequacy_ratio': self.capital_adequacy_ratio,
            'cost_income_ratio': self.cost_income_ratio,
            
            # Metadata
            'extraction_date': self.extraction_date.isoformat(),
            'source_url': self.source_url,
            'extraction_status': self.extraction_status.value,
            'extraction_notes': self.extraction_notes,
        }
        
        # Remove None values
        return {k: v for k, v in data.items() if v is not None}
    
    def calculate_ratios(self):
        """Calculate financial ratios if data available."""
        # ROE = Net Profit / Total Equity
        if self.net_profit and self.total_equity and self.total_equity > 0:
            self.roe = self.net_profit / self.total_equity
        
        # ROA = Net Profit / Total Assets
        if self.net_profit and self.total_assets and self.total_assets > 0:
            self.roa = self.net_profit / self.total_assets
        
        # Cost-Income Ratio = Operating Expenses / Operating Income
        if self.operating_expenses and self.operating_income and self.operating_income > 0:
            self.cost_income_ratio = self.operating_expenses / self.operating_income


@dataclass
class ExtractionResult:
    """Result of financial data extraction."""
    report: FinancialReport
    data: Optional[FinancialData] = None
    error: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    raw_text: Optional[str] = None  # For OCR text
    table_data: Optional[Dict[str, Any]] = None  # For table extraction
    raw_tables: Optional[List[Dict[str, Any]]] = None  # Raw table data
    
    @property
    def is_success(self) -> bool:
        return self.data is not None and self.error is None
    
    @property
    def is_partial(self) -> bool:
        return self.data is not None and len(self.warnings) > 0