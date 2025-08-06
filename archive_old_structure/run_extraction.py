#!/usr/bin/env python3
"""
运行财务数据提取
Run financial data extraction
"""
import subprocess
import sys
from datetime import datetime

print("=" * 60)
print("财务数据提取系统")
print("Financial Data Extraction System")
print("=" * 60)
print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# 统计文件数量
print("正在统计财报文件...")
pdf_count = len(list(Path("data/raw_reports").glob("*.pdf")))
html_count = len(list(Path("data/raw_reports").glob("*.html")))
print(f"PDF文件: {pdf_count}")
print(f"HTML文件: {html_count}")
print(f"总计: {pdf_count + html_count}")
print()

# 运行提取
print("开始提取财务数据...")
print("使用优化版提取器...")
print("-" * 60)

from pathlib import Path
import os
os.chdir(Path(__file__).parent)

# 直接导入并运行
from scripts.extract_data_optimized import main

if __name__ == "__main__":
    main()