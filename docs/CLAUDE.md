# CLAUDE.md - 项目配置与指南

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述 Project Overview

财务分析系统 v3.1 - 自动化财务数据提取和分析平台
Financial Analysis System v3.1 - Automated Financial Data Extraction and Analysis Platform

This is a financial report data extraction and analysis system focused on extracting key financial metrics from PDF/HTML financial reports, particularly for Hong Kong virtual banks and fintech companies. The system uses multiple extraction methods including regex, table extraction, OCR, and LLM-enhanced extraction.

## 关键命令 Key Commands

### 基础操作 Basic Operations

```bash
# 下载财报
python main.py download --limit 100

# 提取数据
python main.py extract --batch-size 200

# 分析结果
python main.py analyze --type extraction

# 清理损坏的PDF
python main.py utils --clean-pdfs

# 生成项目摘要
python main.py utils --summary
```

### 高级提取 Advanced Extraction

```bash
# 使用主提取器（推荐）
python scripts/extractors/master_extractor.py

# 批量处理
python scripts/utilities/batch_processor.py

# LLM增强提取（需要API密钥）
export DEEPSEEK_API_KEY="your-api-key"
python scripts/utilities/deepseek_client.py

# 交叉验证结果
python scripts/utilities/cross_validator.py
```

### 分析和可视化 Analysis and Visualization

```bash
# 生成性能报告
python scripts/visualizers/visualize_performance.py

# 分析提取失败案例
python scripts/analyzers/analyze_extraction_failures.py

# 生成综合分析报告
python scripts/analyzers/data_analyzer.py
```

### 测试和验证 Testing and Validation
```bash
# Python代码检查
python -m pylint financial_analysis/
python -m mypy financial_analysis/

# 快速测试提取功能
python scripts/fast_extraction_test.py

# 验证提取结果
ls -la output/extractions/
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
- Currently 1,224 reports downloaded (1,059 PDFs + 165 HTML) - 82.8% coverage
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

## 版本更新 Version Updates

### v3.1 (2024-08-07)
- 完善项目文档结构
- 优化脚本组织
- 增强错误处理机制
- 添加FAQ和故障排除指南

### v3.0 (2024-08-06)
- 重构项目结构
- 统一功能接口
- 添加LLM支持
- 优化批量处理性能

## 作者 Author
Lin Cifeng

---
最后更新 Last Updated: 2024-08-07