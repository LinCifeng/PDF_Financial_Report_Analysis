import csv
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import logging

from ..core.models import CompanyInfo, FinancialReport, ReportType


class ReportManager:
    """Manage financial report database and metadata."""
    
    def __init__(self, csv_path: str):
        """Initialize report manager.
        
        Args:
            csv_path: Path to Company_Financial_report.csv
        """
        self.csv_path = Path(csv_path)
        self.logger = logging.getLogger(__name__)
        
        if not self.csv_path.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_path}")
        
        self._reports_cache = None
        self._companies_cache = None
    
    def load_reports(self, force_reload: bool = False) -> List[FinancialReport]:
        """Load all reports from CSV.
        
        Args:
            force_reload: Force reload from disk
        
        Returns:
            List of FinancialReport objects
        """
        if self._reports_cache is not None and not force_reload:
            return self._reports_cache
        
        reports = []
        companies = {}
        
        with open(self.csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                # Skip empty rows or rows without report
                if not row.get('Financial Report(Y/N)') or row['Financial Report(Y/N)'].upper() != 'Y':
                    continue
                
                # Get or create company
                company_id = row.get('new_id', '')
                if company_id not in companies:
                    companies[company_id] = CompanyInfo(
                        id=company_id,
                        name=row.get('name', ''),
                        website=row.get('website', '')
                    )
                
                # Create report
                report = FinancialReport(
                    company=companies[company_id],
                    fiscal_year=self._parse_year(row.get('Fiscal_year', '')),
                    quarter=row.get('Quarter', ''),
                    report_type=self._determine_report_type(row.get('Quarter', '')),
                    report_link=row.get('Report_link', '')
                )
                
                if report.fiscal_year > 0:  # Valid year
                    reports.append(report)
        
        self._reports_cache = reports
        self._companies_cache = companies
        
        self.logger.info(f"Loaded {len(reports)} reports from {len(companies)} companies")
        return reports
    
    def get_company_reports(self, company_name: str) -> List[FinancialReport]:
        """Get all reports for a specific company.
        
        Args:
            company_name: Name of the company
        
        Returns:
            List of reports for the company
        """
        reports = self.load_reports()
        return [r for r in reports if r.company.name.lower() == company_name.lower()]
    
    def get_reports_by_year(self, year: int) -> List[FinancialReport]:
        """Get all reports for a specific year.
        
        Args:
            year: Fiscal year
        
        Returns:
            List of reports for the year
        """
        reports = self.load_reports()
        return [r for r in reports if r.fiscal_year == year]
    
    def get_companies_with_reports(self) -> List[CompanyInfo]:
        """Get list of companies that have financial reports.
        
        Returns:
            List of CompanyInfo objects
        """
        self.load_reports()
        return list(self._companies_cache.values())
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the report database.
        
        Returns:
            Dictionary with statistics
        """
        reports = self.load_reports()
        companies = self._companies_cache
        
        # Calculate statistics
        years = [r.fiscal_year for r in reports]
        min_year = min(years) if years else 0
        max_year = max(years) if years else 0
        
        # Reports by type
        annual_reports = sum(1 for r in reports if r.report_type == ReportType.ANNUAL)
        interim_reports = sum(1 for r in reports if r.report_type == ReportType.INTERIM)
        
        # Reports by company
        reports_by_company = {}
        for report in reports:
            company_name = report.company.name
            if company_name not in reports_by_company:
                reports_by_company[company_name] = 0
            reports_by_company[company_name] += 1
        
        # Top companies
        top_companies = sorted(
            reports_by_company.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:10]
        
        return {
            'total_companies': len(companies),
            'total_reports': len(reports),
            'year_range': f"{min_year}-{max_year}",
            'annual_reports': annual_reports,
            'interim_reports': interim_reports,
            'avg_reports_per_company': len(reports) / len(companies) if companies else 0,
            'top_companies': top_companies
        }
    
    def _parse_year(self, year_str: str) -> int:
        """Parse year from string."""
        try:
            return int(year_str)
        except (ValueError, TypeError):
            return 0
    
    def _determine_report_type(self, quarter_str: str) -> ReportType:
        """Determine report type from quarter string."""
        if not quarter_str:
            return ReportType.ANNUAL
        
        quarter_lower = quarter_str.lower()
        if 'q1' in quarter_lower and 'q2' in quarter_lower:
            return ReportType.INTERIM
        elif 'q' in quarter_lower:
            return ReportType.QUARTERLY
        else:
            return ReportType.ANNUAL
    
    def get_pending_downloads(self, local_dir: Path) -> List[FinancialReport]:
        """Get reports that haven't been downloaded yet.
        
        Args:
            local_dir: Directory to check for downloaded files
        
        Returns:
            List of reports that need to be downloaded
        """
        reports = self.load_reports()
        pending = []
        
        for report in reports:
            # Generate expected filename
            filename = self._generate_filename(report)
            local_path = local_dir / filename
            
            if not local_path.exists():
                report.local_path = str(local_path)
                pending.append(report)
        
        return pending
    
    def _generate_filename(self, report: FinancialReport) -> str:
        """Generate standardized filename for report."""
        company_name = report.company.name.replace(' ', '_').replace('/', '_')
        year = report.fiscal_year
        
        if report.quarter:
            quarter = report.quarter.replace('、', '_').replace(' ', '')
            return f"{company_name}_{year}_{quarter}.pdf"
        else:
            return f"{company_name}_{year}_Annual.pdf"