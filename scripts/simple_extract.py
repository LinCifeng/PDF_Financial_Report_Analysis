#!/usr/bin/env python3
"""
简化版提取脚本 - 直接使用基本的PDF提取
"""

import os
import re
import csv
from pathlib import Path
import pdfplumber
import logging
from tqdm import tqdm
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_year(filename):
    """提取年份"""
    match = re.search(r'20\d{2}', filename)
    return int(match.group()) if match else None

def extract_number(text):
    """从文本中提取数字"""
    if not text:
        return None
    # 移除逗号和空格
    text = text.replace(',', '').replace(' ', '')
    match = re.search(r'[-]?\d+', text)
    return int(match.group()) if match else None

def extract_from_pdf(pdf_path):
    """从PDF提取财务数据"""
    result = {
        'total_assets': None,
        'total_liabilities': None,
        'revenue': None,
        'net_profit': None
    }
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = ''
            # 提取前10页文本
            for i, page in enumerate(pdf.pages[:10]):
                page_text = page.extract_text()
                if page_text:
                    text += page_text + '\n'
            
            # 转换为小写以便匹配
            text_lower = text.lower()
            
            # 提取总资产
            patterns = [
                r'total\s+assets?\s*[:：]?\s*([\d,]+)',
                r'資產總[计計額]?\s*[:：]?\s*([\d,]+)',
                r'總資產\s*[:：]?\s*([\d,]+)'
            ]
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    result['total_assets'] = extract_number(match.group(1))
                    break
            
            # 提取总负债
            patterns = [
                r'total\s+liabilit(?:y|ies)\s*[:：]?\s*([\d,]+)',
                r'負債總[计計額]?\s*[:：]?\s*([\d,]+)',
                r'總負債\s*[:：]?\s*([\d,]+)'
            ]
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    result['total_liabilities'] = extract_number(match.group(1))
                    break
            
            # 提取营业收入
            patterns = [
                r'(?:total\s+)?revenue\s*[:：]?\s*([\d,]+)',
                r'營業收入\s*[:：]?\s*([\d,]+)',
                r'收入總額\s*[:：]?\s*([\d,]+)',
                r'operating\s+income\s*[:：]?\s*([\d,]+)'
            ]
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    result['revenue'] = extract_number(match.group(1))
                    break
            
            # 提取净利润
            patterns = [
                r'net\s+(?:profit|income|loss)\s*[:：]?\s*([\-\d,]+)',
                r'淨利潤\s*[:：]?\s*([\-\d,]+)',
                r'净利润\s*[:：]?\s*([\-\d,]+)',
                r'profit\s+for\s+the\s+year\s*[:：]?\s*([\-\d,]+)',
                r'loss\s+for\s+the\s+year\s*[:：]?\s*([\-\d,]+)'
            ]
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    value = extract_number(match.group(1))
                    # 如果匹配到loss，确保是负数
                    if 'loss' in pattern and value and value > 0:
                        value = -value
                    result['net_profit'] = value
                    break
                    
    except Exception as e:
        logger.error(f"Error extracting from {pdf_path}: {e}")
    
    return result

def main():
    pdf_dir = Path("data/raw_reports")
    output_csv = "output/simple_extraction_results.csv"
    
    # 确保输出目录存在
    Path("output").mkdir(exist_ok=True)
    
    # 收集所有PDF
    pdf_files = list(pdf_dir.glob("*.pdf"))
    print(f"Found {len(pdf_files)} PDF files")
    
    results = []
    stats = {
        'total': len(pdf_files),
        'success': 0,
        'fields': {
            'total_assets': 0,
            'total_liabilities': 0,
            'revenue': 0,
            'net_profit': 0
        }
    }
    
    # 处理每个PDF
    for pdf_path in tqdm(pdf_files, desc="Extracting"):
        company_name = pdf_path.stem.split('_')[0]
        year = extract_year(pdf_path.name)
        
        data = extract_from_pdf(pdf_path)
        
        result = {
            'company_name': company_name,
            'year': year,
            'file_name': pdf_path.name,
            'total_assets': data['total_assets'],
            'total_liabilities': data['total_liabilities'],
            'revenue': data['revenue'],
            'net_profit': data['net_profit']
        }
        
        results.append(result)
        
        # 统计
        if any(data.values()):
            stats['success'] += 1
        
        for field in stats['fields']:
            if data.get(field):
                stats['fields'][field] += 1
    
    # 保存到CSV
    with open(output_csv, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['company_name', 'year', 'file_name', 'total_assets', 
                     'total_liabilities', 'revenue', 'net_profit']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for result in sorted(results, key=lambda x: (x['company_name'], x['year'] or 0)):
            writer.writerow(result)
    
    print(f"\n✅ 完成!")
    print(f"CSV文件: {output_csv}")
    print(f"成功提取数据的文件: {stats['success']}/{stats['total']} ({stats['success']/stats['total']*100:.1f}%)")
    print("\n字段提取情况:")
    for field, count in stats['fields'].items():
        print(f"- {field}: {count} ({count/stats['total']*100:.1f}%)")

if __name__ == "__main__":
    main()