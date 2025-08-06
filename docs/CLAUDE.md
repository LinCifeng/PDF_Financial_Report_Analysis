# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a financial report data extraction and analysis system focused on extracting key financial metrics from PDF financial reports, particularly for Hong Kong virtual banks and fintech companies. The system uses multiple extraction methods including regex, table extraction, OCR, and LLM-enhanced extraction.

## Key Commands

### Running Data Extraction

```bash
# Simple extraction (fast, regex-based)
python scripts/simple_extract.py

# Optimized extraction (recommended, better accuracy)
python scripts/extract_data_optimized.py

# LLM-enhanced extraction (requires DeepSeek API key)
export DEEPSEEK_API_KEY="your-api-key"
python scripts/extract_all_data.py
```

### Analysis and Utility Scripts

```bash
# Download all financial reports (supports PDF and HTML)
python scripts/download_all_reports.py

# Check and clean corrupted PDFs
python scripts/check_and_clean_pdfs.py

# Generate download summary statistics
python scripts/generate_download_summary.py

# Analyze company financial reports coverage
python scripts/analysis/analyze_companies.py

# Check download coverage against CSV database
python scripts/analysis/analyze_download_coverage.py
```

### Running Tests
```bash
# No test framework is currently set up
# Verify extraction by checking output CSVs in output/ directory
```

## Core Architecture

### Data Flow
1. **Input**: PDF reports in `data/raw_reports/`
2. **Processing**: Multi-layer extraction system
3. **Output**: CSV files in `output/` directory

### Extraction System Architecture

The extraction system follows a hierarchical design:

1. **BaseExtractor** (`src/extractors/base.py`)
   - Abstract base class defining the extractor interface
   - All extractors inherit from this class
   - Provides validation and common functionality

2. **PDF Extractors** (`src/extractors/pdf/`)
   - `basic.py`: Regex-based extraction for standard patterns
   - `table.py`: Table extraction using pdfplumber
   - `ocr.py`: OCR-based extraction for scanned documents

3. **LLM Extractor** (`src/extractors/llm/improved.py`)
   - Uses DeepSeek API for intelligent extraction
   - Handles complex layouts and non-standard formats

4. **Smart Extractor** (`src/extractors/smart.py`)
   - Orchestrates multiple extractors
   - Automatically selects best extraction strategy
   - Merges results from different extractors

### Data Models (`src/core/models.py`)
- `FinancialData`: Core data structure for extracted metrics
- `FinancialReport`: Metadata about the report
- `ExtractionResult`: Wrapper for extraction status and data

### Key Financial Metrics Extracted
- 总资产 (Total Assets)
- 总负债 (Total Liabilities)
- 营业收入 (Revenue)
- 净利润 (Net Profit/Loss) - includes negative value handling

## Important Context

### PDF Report Sources
- `data/Company_Financial_report.csv` contains 1,478 financial report links from 126 companies
- Currently 1,032 reports downloaded (910 PDFs + 122 HTML) - 69.8% coverage
- Corrupted files are moved to `data/raw_reports/corrupted_backup/`
- Duplicate files are moved to `data/duplicate_backup/`
- Download script supports both PDF and HTML formats with automatic detection
- Total data size: approximately 15GB

### Language Handling
- System handles both Chinese and English financial reports
- Regex patterns support both languages for key metrics
- Negative values (losses) are properly detected with parentheses or minus signs

### Virtual Environment Issues
- System Python may have package installation restrictions
- Consider using virtual environment for dependencies
- Main dependencies: pdfplumber, pandas, requests, tqdm

### Current Extraction Performance
- Total Assets: 30.6% success rate
- Total Liabilities: 47.2% success rate  
- Revenue: 34.3% success rate
- Net Profit: 41.7% success rate

## Development Notes

- When adding new extractors, inherit from `BaseExtractor`
- Output CSVs should maintain consistent column structure
- Check `data/raw_reports/corrupted_backup/` for problematic PDFs
- LLM extraction requires API key but provides best results for complex PDFs