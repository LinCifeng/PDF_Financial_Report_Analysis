"""
财务分析系统核心包
Financial Analysis System Core Package

作者: Lin Cifeng
"""

__version__ = "3.0.0"
__author__ = "Lin Cifeng"

# 新模块结构
from .download import Downloader, batch_download
from .extractor import SmartExtractor, smart_extract
from .analysis import Analyzer, analyze_extraction_results
from .visualization import Visualizer, create_charts
# 从 download/pdf_utils.py 文件导入工具函数
from .download.pdf_utils import clean_pdfs, generate_summary

# 为了向后兼容，保留旧接口
from .download.downloader import download_reports
from .analysis.analyzer import analyze_data

__all__ = [
    # 新模块
    'Downloader',
    'batch_download',
    'SmartExtractor',
    'smart_extract', 
    'Analyzer',
    'analyze_extraction_results',
    'Visualizer',
    'create_charts',
    # 旧接口（兼容）
    'download_reports',
    'analyze_data', 
    # 工具
    'clean_pdfs',
    'generate_summary'
]