#!/usr/bin/env python3
"""快速财务数据提取"""
import re
import csv
from pathlib import Path
from datetime import datetime
import pdfplumber
from tqdm import tqdm

# 配置
PDF_DIR = Path("data/raw_reports")
OUTPUT_FILE = Path("output") / f"extraction_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

# 确保输出目录存在
OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

# 正则表达式模式
PATTERNS = {
    'total_assets': [
        r'总资产[：:]\s*([0-9,，]+)',
        r'資產總[計计][：:]\s*([0-9,，]+)', 
        r'Total\s+Assets?[：:]\s*\$?\s*([0-9,，]+)',
    ],
    'total_liabilities': [
        r'总负债[：:]\s*([0-9,，]+)',
        r'負債總[計计][：:]\s*([0-9,，]+)',
        r'Total\s+Liabilities?[：:]\s*\$?\s*([0-9,，]+)',
    ],
    'revenue': [
        r'营业收入[：:]\s*([0-9,，]+)',
        r'營業收入[：:]\s*([0-9,，]+)',
        r'Revenue[：:]\s*\$?\s*([0-9,，]+)',
    ],
    'net_profit': [
        r'净利润[：:]\s*[\(（\-]?([0-9,，]+)[\)）]?',
        r'淨利潤[：:]\s*[\(（\-]?([0-9,，]+)[\)）]?',
        r'Net\s+(?:Profit|Income)[：:]\s*\$?\s*[\(（\-]?([0-9,，]+)[\)）]?',
    ]
}

def extract_number(text):
    """提取数字"""
    if not text:
        return None
    text = text.replace(',', '').replace('，', '')
    try:
        return float(text)
    except:
        return None

def extract_from_pdf(pdf_path):
    """从PDF提取数据"""
    results = {
        'file': pdf_path.name,
        'company': pdf_path.stem.split('_')[0],
        'total_assets': None,
        'total_liabilities': None,
        'revenue': None,
        'net_profit': None,
        'status': 'Failed'
    }
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            # 读取前30页
            text = ''
            for page in pdf.pages[:30]:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + '\n'
            
            # 应用正则表达式
            for field, patterns in PATTERNS.items():
                for pattern in patterns:
                    matches = re.findall(pattern, text, re.IGNORECASE)
                    if matches:
                        value = extract_number(matches[0])
                        if value:
                            results[field] = value
                            results['status'] = 'Success'
                            break
                            
    except Exception as e:
        results['error'] = str(e)
    
    return results

# 主程序
print(f"开始提取财务数据...")
pdf_files = list(PDF_DIR.glob("*.pdf"))
print(f"找到 {len(pdf_files)} 个PDF文件")

results = []
for pdf_file in tqdm(pdf_files[:100], desc="提取中"):  # 先处理100个文件测试
    result = extract_from_pdf(pdf_file)
    results.append(result)

# 保存结果
with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=['file', 'company', 'total_assets', 
                                          'total_liabilities', 'revenue', 'net_profit', 
                                          'status', 'error'])
    writer.writeheader()
    writer.writerows(results)

# 统计
success = sum(1 for r in results if r['status'] == 'Success')
print(f"\n完成! 成功率: {success}/{len(results)} ({success/len(results)*100:.1f}%)")
print(f"结果保存至: {OUTPUT_FILE}")