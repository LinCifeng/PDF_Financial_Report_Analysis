#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
金融报告分析工具
用于分析财务PDF报告并生成分析结果
"""

import os
import sys
import logging
import argparse
import matplotlib
from datetime import datetime
from financial_analyzer import PDFDataExtractor, FinancialAnalyzer, ReportGenerator, ChartGenerator, generate_report

def setup_logging(verbose):
    """设置日志级别
    
    Args:
        verbose (bool): 是否启用详细日志
    """
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def setup_font(font_name):
    """设置matplotlib字体
    
    Args:
        font_name (str): 字体名称
    """
    matplotlib.rcParams['font.sans-serif'] = [font_name, 'SimHei', 'DejaVu Sans']  # 设置中文字体，添加备选字体
    matplotlib.rcParams['axes.unicode_minus'] = False  # 正常显示负号

def main():
    """主程序入口"""
    parser = argparse.ArgumentParser(description='财务报告分析工具')
    parser.add_argument('--pdf', help='PDF报告文件路径')
    parser.add_argument('--output', default='./output', help='输出报告保存路径')
    parser.add_argument('--extract-only', action='store_true', help='仅提取数据不分析')
    parser.add_argument('--json', help='使用提取的JSON数据文件进行分析')
    parser.add_argument('--no-viz', action='store_true', help='不生成可视化图表')
    parser.add_argument('--verbose', action='store_true', help='输出详细日志')
    parser.add_argument('--font', default='Source Han Sans SC', help='设置图表中文字体（默认：Source Han Sans SC）')
    
    args = parser.parse_args()
    
    # 设置日志级别
    setup_logging(args.verbose)
    
    # 设置字体
    setup_font(args.font)
    
    # 检查输入参数
    if not args.pdf and not args.json:
        print("错误: 必须提供PDF文件或JSON数据文件")
        parser.print_help()
        sys.exit(1)
        
    # 创建输出目录（如果不存在）
    os.makedirs(args.output, exist_ok=True)
    
    # 根据参数生成报告
    generate_report(
        pdf_path=args.pdf, 
        output_path=args.output, 
        extract_only=args.extract_only,
        json_path=args.json,
        visualize=not args.no_viz,
        verbose=args.verbose
    )

if __name__ == "__main__":
    main() 