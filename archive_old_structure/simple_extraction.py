#!/usr/bin/env python3
"""简单财务数据提取"""
import os
import re
import csv
from datetime import datetime
import pdfplumber

# 配置
PDF_DIR = "data/raw_reports"
OUTPUT_FILE = f"output/extraction_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

# 正则模式
patterns = {
    'assets': r'(?:总资产|Total Assets)[:\s]*\$?([0-9,]+)',
    'liabilities': r'(?:总负债|Total Liabilities)[:\s]*\$?([0-9,]+)',
    'revenue': r'(?:营业收入|Revenue)[:\s]*\$?([0-9,]+)',
    'profit': r'(?:净利润|Net (?:Profit|Income))[:\s]*\$?[\(]?([0-9,]+)[\)]?'
}

results = []
pdf_files = [f for f in os.listdir(PDF_DIR) if f.endswith('.pdf')][:50]  # 先处理50个

print(f"处理 {len(pdf_files)} 个文件...")

for pdf_file in pdf_files:
    result = {
        'file': pdf_file,
        'assets': '',
        'liabilities': '',  
        'revenue': '',
        'profit': ''
    }
    
    try:
        with pdfplumber.open(os.path.join(PDF_DIR, pdf_file)) as pdf:
            text = ''
            # 只读前10页
            for page in pdf.pages[:10]:
                if page:
                    t = page.extract_text()
                    if t:
                        text += t
            
            # 提取数据
            for key, pattern in patterns.items():
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    result[key] = match.group(1).replace(',', '')
                    
    except Exception as e:
        print(f"错误 {pdf_file}: {e}")
    
    results.append(result)
    print(f"处理: {pdf_file}")

# 保存
with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=['file', 'assets', 'liabilities', 'revenue', 'profit'])
    writer.writeheader()
    writer.writerows(results)

print(f"\n完成! 结果保存至: {OUTPUT_FILE}")

# 统计
success = sum(1 for r in results if any([r['assets'], r['liabilities'], r['revenue'], r['profit']]))
print(f"成功提取: {success}/{len(results)} ({success/len(results)*100:.1f}%)")