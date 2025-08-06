#!/usr/bin/env python3
import os
print("当前目录:", os.getcwd())
print("Python版本:", os.sys.version)

# 检查依赖
try:
    import pdfplumber
    print("✓ pdfplumber已安装")
except ImportError:
    print("✗ 需要安装pdfplumber: pip install pdfplumber")

try:
    import pandas
    print("✓ pandas已安装")
except ImportError:
    print("✗ 需要安装pandas: pip install pandas")

# 检查目录
from pathlib import Path
data_dir = Path("data/raw_reports")
if data_dir.exists():
    pdf_count = len(list(data_dir.glob("*.pdf")))
    print(f"✓ 找到{pdf_count}个PDF文件")
else:
    print("✗ data/raw_reports目录不存在")

# 简单测试
if data_dir.exists() and pdf_count > 0:
    print("\n尝试读取第一个PDF...")
    first_pdf = list(data_dir.glob("*.pdf"))[0]
    print(f"文件: {first_pdf.name}")
    try:
        import pdfplumber
        with pdfplumber.open(first_pdf) as pdf:
            print(f"页数: {len(pdf.pages)}")
            print("✓ PDF读取成功")
    except Exception as e:
        print(f"✗ 错误: {e}")