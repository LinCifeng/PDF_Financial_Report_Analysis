import json
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import logging
from tqdm import tqdm

from ..core.config import Config
from ..core.models import FinancialReport, ExtractionResult, DataStatus
from ..data.report_manager import ReportManager
from ..extractors.extractor_factory import ExtractorFactory
from ..downloaders.report_downloader import ReportDownloader


class BatchProcessor:
    """Process financial reports in batch."""
    
    def __init__(self, config: Config):
        """Initialize batch processor.
        
        Args:
            config: Configuration object
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        csv_path = config.project_root / config.get('database.financial_reports_csv')
        self.report_manager = ReportManager(csv_path)
        self.extractor_factory = ExtractorFactory(config._config)
        self.downloader = ReportDownloader(config)
        
        # Setup directories
        self.raw_reports_dir = config.project_root / config.get('paths.raw_reports_dir')
        self.processed_data_dir = config.project_root / config.get('paths.processed_data_dir')
        self.output_dir = config.project_root / config.get('paths.output_dir')
        
        # Processing settings
        self.batch_size = config.get('processing.batch_size', 10)
        self.max_workers = config.get('processing.max_workers', 4)
    
    def process_all(self, 
                   download: bool = True,
                   company_filter: Optional[List[str]] = None,
                   year_filter: Optional[List[int]] = None) -> Dict[str, Any]:
        """Process all financial reports.
        
        Args:
            download: Whether to download missing reports
            company_filter: List of company names to process (None = all)
            year_filter: List of years to process (None = all)
        
        Returns:
            Processing summary
        """
        self.logger.info("Starting batch processing of financial reports")
        
        # Load all reports
        all_reports = self.report_manager.load_reports()
        
        # Apply filters
        reports = self._filter_reports(all_reports, company_filter, year_filter)
        
        self.logger.info(f"Found {len(reports)} reports to process")
        
        # Download reports if requested
        if download:
            download_results = self._download_reports(reports)
            self.logger.info(f"Downloaded {download_results['success']} reports")
        
        # Extract data from reports
        extraction_results = self._extract_data(reports)
        
        # Save results
        self._save_results(extraction_results)
        
        # Generate summary
        summary = self._generate_summary(extraction_results)
        
        return summary
    
    def _filter_reports(self, 
                       reports: List[FinancialReport],
                       company_filter: Optional[List[str]] = None,
                       year_filter: Optional[List[int]] = None) -> List[FinancialReport]:
        """Filter reports based on criteria."""
        filtered = reports
        
        if company_filter:
            company_filter_lower = [c.lower() for c in company_filter]
            filtered = [r for r in filtered 
                       if r.company.name.lower() in company_filter_lower]
        
        if year_filter:
            filtered = [r for r in filtered if r.fiscal_year in year_filter]
        
        return filtered
    
    def _download_reports(self, reports: List[FinancialReport]) -> Dict[str, int]:
        """Download missing reports."""
        pending = self.report_manager.get_pending_downloads(self.raw_reports_dir)
        
        if not pending:
            return {'success': 0, 'failed': 0, 'skipped': len(reports)}
        
        self.logger.info(f"Downloading {len(pending)} missing reports")
        
        results = {'success': 0, 'failed': 0, 'skipped': len(reports) - len(pending)}
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(self.downloader.download_report, report): report
                for report in pending
            }
            
            with tqdm(total=len(pending), desc="Downloading reports") as pbar:
                for future in as_completed(futures):
                    report = futures[future]
                    try:
                        success = future.result()
                        if success:
                            results['success'] += 1
                        else:
                            results['failed'] += 1
                    except Exception as e:
                        self.logger.error(f"Error downloading {report.company.name}: {str(e)}")
                        results['failed'] += 1
                    
                    pbar.update(1)
        
        return results
    
    def _extract_data(self, reports: List[FinancialReport]) -> List[ExtractionResult]:
        """Extract data from all reports."""
        results = []
        
        # Process in batches
        for i in range(0, len(reports), self.batch_size):
            batch = reports[i:i + self.batch_size]
            batch_results = self._process_batch(batch)
            results.extend(batch_results)
        
        return results
    
    def _process_batch(self, reports: List[FinancialReport]) -> List[ExtractionResult]:
        """Process a batch of reports."""
        results = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {}
            
            for report in reports:
                # Check if file exists
                filename = self.report_manager._generate_filename(report)
                file_path = self.raw_reports_dir / filename
                
                if file_path.exists():
                    future = executor.submit(self.extractor_factory.extract, file_path, report)
                    futures[future] = report
                else:
                    # File not found
                    results.append(ExtractionResult(
                        report=report,
                        error=f"File not found: {file_path}"
                    ))
            
            # Collect results
            for future in as_completed(futures):
                report = futures[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    self.logger.error(f"Error processing {report.company.name}: {str(e)}")
                    results.append(ExtractionResult(
                        report=report,
                        error=str(e)
                    ))
        
        return results
    
    def _save_results(self, results: List[ExtractionResult]):
        """Save extraction results to files."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Create subdirectories if they don't exist
        json_dir = self.output_dir / 'extraction_results' / 'json'
        csv_dir = self.output_dir / 'extraction_results' / 'csv'
        error_dir = self.output_dir / 'errors'
        
        json_dir.mkdir(parents=True, exist_ok=True)
        csv_dir.mkdir(parents=True, exist_ok=True)
        error_dir.mkdir(parents=True, exist_ok=True)
        
        # Save to JSON
        json_path = json_dir / f"extraction_results_{timestamp}.json"
        
        json_data = []
        for result in results:
            if result.data:
                json_data.append(result.data.to_dict())
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"Saved {len(json_data)} extracted records to {json_path}")
        
        # Save to CSV
        if json_data:
            csv_path = csv_dir / f"extraction_results_{timestamp}.csv"
            
            # Define all possible fieldnames
            fieldnames = [
                'company_name', 'fiscal_year', 'quarter', 'report_type', 'currency', 'unit',
                'total_assets', 'current_assets', 'non_current_assets',
                'total_liabilities', 'current_liabilities', 'non_current_liabilities',
                'total_equity', 'revenue', 'operating_income', 'operating_expenses',
                'net_interest_income', 'net_profit', 'net_profit_before_tax',
                'operating_cash_flow', 'investing_cash_flow', 'financing_cash_flow',
                'net_cash_flow', 'capital_adequacy_ratio', 'tier1_capital_ratio',
                'npl_ratio', 'provision_coverage_ratio', 'loan_to_deposit_ratio',
                'return_on_assets', 'return_on_equity', 'cost_to_income_ratio',
                'net_interest_margin', 'extraction_date', 'extraction_method',
                'extraction_status', 'extraction_notes', 'report_link', 'local_path'
            ]
            
            with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
                writer.writeheader()
                writer.writerows(json_data)
            
            self.logger.info(f"Saved results to {csv_path}")
        
        # Save error log
        errors = [(r.report.company.name, r.report.fiscal_year, r.error) 
                 for r in results if r.error]
        
        if errors:
            error_path = error_dir / f"extraction_errors_{timestamp}.json"
            with open(error_path, 'w', encoding='utf-8') as f:
                json.dump(errors, f, ensure_ascii=False, indent=2)
    
    def _generate_summary(self, results: List[ExtractionResult]) -> Dict[str, Any]:
        """Generate processing summary."""
        total = len(results)
        success = sum(1 for r in results if r.is_success)
        partial = sum(1 for r in results if r.is_partial)
        failed = sum(1 for r in results if r.error is not None)
        
        # Group by company
        by_company = {}
        for result in results:
            company = result.report.company.name
            if company not in by_company:
                by_company[company] = {'success': 0, 'partial': 0, 'failed': 0}
            
            if result.is_success:
                by_company[company]['success'] += 1
            elif result.is_partial:
                by_company[company]['partial'] += 1
            else:
                by_company[company]['failed'] += 1
        
        return {
            'total_reports': total,
            'successful': success,
            'partial': partial,
            'failed': failed,
            'success_rate': success / total if total > 0 else 0,
            'by_company': by_company,
            'timestamp': datetime.now().isoformat()
        }