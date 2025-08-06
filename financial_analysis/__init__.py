"""
财务分析系统核心包
Financial Analysis System Core Package

作者: Lin Cifeng
"""

__version__ = "3.0.0"
__author__ = "Lin Cifeng"

from .extract import extract_financial_data
from .download import download_reports  
from .analyze import analyze_data
from .utils import clean_pdfs, generate_summary

__all__ = [
    'extract_financial_data',
    'download_reports',
    'analyze_data', 
    'clean_pdfs',
    'generate_summary'
]