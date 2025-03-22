#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
财务分析系统包
"""

# 导入主要模块，方便使用
from financial_analyzer.data_extraction.pdf_extractor import PDFDataExtractor
from financial_analyzer.analysis.financial_analyzer import FinancialAnalyzer
from financial_analyzer.analysis.report_generator import ReportGenerator
from financial_analyzer.visualization.chart_generator import ChartGenerator
from financial_analyzer.main import generate_report

__version__ = '1.0.0'
