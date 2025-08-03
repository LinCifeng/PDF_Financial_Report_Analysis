import requests
import time
from pathlib import Path
from typing import Optional, Dict, Any
import logging
from urllib.parse import urlparse

from ..core.config import Config
from ..core.models import FinancialReport


class ReportDownloader:
    """Download financial reports from URLs."""
    
    def __init__(self, config: Config):
        """Initialize downloader.
        
        Args:
            config: Configuration object
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Download settings
        self.retry_attempts = config.get('processing.retry_attempts', 3)
        self.retry_delay = config.get('processing.retry_delay', 5)
        self.timeout = 30
        
        # Setup session
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # Output directory
        self.output_dir = config.project_root / config.get('paths.raw_reports_dir')
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def download_report(self, report: FinancialReport) -> bool:
        """Download a single report.
        
        Args:
            report: Report to download
        
        Returns:
            True if successful, False otherwise
        """
        if not report.report_link:
            self.logger.warning(f"No URL for {report.company.name} {report.fiscal_year}")
            return False
        
        # Generate filename
        filename = self._generate_filename(report)
        output_path = self.output_dir / filename
        
        # Skip if already exists
        if output_path.exists():
            self.logger.debug(f"Already exists: {filename}")
            report.local_path = str(output_path)
            return True
        
        # Download with retries
        for attempt in range(self.retry_attempts):
            try:
                self.logger.info(f"Downloading {report.company.name} {report.fiscal_year} (attempt {attempt + 1})")
                
                response = self.session.get(
                    report.report_link,
                    timeout=self.timeout,
                    stream=True
                )
                
                if response.status_code == 200:
                    # Save file
                    with open(output_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    
                    report.local_path = str(output_path)
                    self.logger.info(f"Downloaded: {filename}")
                    return True
                else:
                    self.logger.warning(
                        f"HTTP {response.status_code} for {report.company.name} {report.fiscal_year}"
                    )
                    
            except requests.exceptions.RequestException as e:
                self.logger.error(f"Download error: {str(e)}")
                
            # Wait before retry
            if attempt < self.retry_attempts - 1:
                time.sleep(self.retry_delay)
        
        return False
    
    def _generate_filename(self, report: FinancialReport) -> str:
        """Generate standardized filename for report."""
        # Clean company name
        company_name = report.company.name.replace(' ', '_').replace('/', '_')
        company_name = ''.join(c for c in company_name if c.isalnum() or c in '_-')
        
        # Build filename
        parts = [company_name, str(report.fiscal_year)]
        
        if report.quarter:
            quarter = report.quarter.replace('、', '_').replace(' ', '')
            parts.append(quarter)
        else:
            parts.append('Annual')
        
        # Add extension
        ext = self._get_file_extension(report.report_link)
        filename = '_'.join(parts) + ext
        
        return filename
    
    def _get_file_extension(self, url: str) -> str:
        """Get file extension from URL."""
        # Parse URL
        parsed = urlparse(url)
        path = parsed.path.lower()
        
        # Check common extensions
        if path.endswith('.pdf'):
            return '.pdf'
        elif path.endswith('.xlsx'):
            return '.xlsx'
        elif path.endswith('.xls'):
            return '.xls'
        elif path.endswith('.html') or path.endswith('.htm'):
            return '.html'
        else:
            # Default to PDF
            return '.pdf'