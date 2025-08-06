#!/usr/bin/env python3
"""完整财务数据提取 - 处理所有PDF文件"""
import os
import re
import csv
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

try:
    import pdfplumber
except:
    os.system("/usr/bin/pip3 install pdfplumber")
    import pdfplumber

# 配置
PDF_DIR = "data/raw_reports"
OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)
TIMESTAMP = datetime.now().strftime('%Y%m%d_%H%M%S')
OUTPUT_FILE = f"{OUTPUT_DIR}/extraction_results_{TIMESTAMP}.csv"

# 改进的正则模式
patterns = {
    'total_assets': [
        r'(?:总资产|資產總[计計]|Total\s+Assets?)[:\s]*\$?\s*([0-9,]+)',
        r'(?:资产总[计計]|Assets?\s+Total)[:\s]*\$?\s*([0-9,]+)',
    ],
    'total_liabilities': [
        r'(?:总负债|負債總[计計]|Total\s+Liabilit(?:y|ies))[:\s]*\$?\s*([0-9,]+)',
        r'(?:负债总[计計]|Liabilit(?:y|ies)\s+Total)[:\s]*\$?\s*([0-9,]+)',
    ],
    'revenue': [
        r'(?:营业收入|營業收入|(?:Operating\s+)?Revenue)[:\s]*\$?\s*([0-9,]+)',
        r'(?:收入总[额計]|Total\s+Revenue)[:\s]*\$?\s*([0-9,]+)',
    ],
    'net_profit': [
        r'(?:净利润|淨利潤|Net\s+(?:Profit|Income))[:\s]*\$?\s*[\(（\-]?([0-9,]+)[\)）]?',
        r'(?:净利|淨利|Net\s+(?:Loss|Profit))[:\s]*\$?\s*[\(（\-]?([0-9,]+)[\)）]?',
    ]
}

def extract_from_pdf(pdf_path):
    """提取单个PDF的数据"""
    filename = os.path.basename(pdf_path)
    company = filename.split('_')[0]
    
    # 提取年份
    year_match = re.search(r'20\d{2}', filename)
    year = year_match.group() if year_match else ''
    
    result = {
        'Company': company,
        'Year': year,
        'Total Assets': '',
        'Total Liabilities': '',
        'Revenue': '',
        'Net Profit': '',
        'File': filename,
        'Status': 'Failed'
    }
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            # 读取前15页
            text = ''
            for i in range(min(15, len(pdf.pages))):
                page = pdf.pages[i]
                if page:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + '\n'
            
            # 应用正则表达式
            for field, pattern_list in patterns.items():
                for pattern in pattern_list:
                    matches = re.findall(pattern, text, re.IGNORECASE)
                    if matches:
                        # 取第一个匹配值
                        value = matches[0].replace(',', '').replace('，', '')
                        if field == 'total_assets':
                            result['Total Assets'] = value
                        elif field == 'total_liabilities':
                            result['Total Liabilities'] = value
                        elif field == 'revenue':
                            result['Revenue'] = value
                        elif field == 'net_profit':
                            result['Net Profit'] = value
                        break
            
            # 检查是否成功提取到数据
            if any([result['Total Assets'], result['Total Liabilities'], 
                   result['Revenue'], result['Net Profit']]):
                result['Status'] = 'Success'
                
    except Exception as e:
        result['Status'] = f'Error: {str(e)[:30]}'
    
    return result

# 主程序
print("=" * 60)
print("完整财务数据提取")
print("=" * 60)

# 获取所有PDF文件
pdf_files = [f for f in os.listdir(PDF_DIR) if f.endswith('.pdf')]
total_files = len(pdf_files)
print(f"找到 {total_files} 个PDF文件")

# 批量处理
BATCH_SIZE = 100
results = []
processed = 0

for i in range(0, total_files, BATCH_SIZE):
    batch = pdf_files[i:i+BATCH_SIZE]
    print(f"\n处理批次 {i//BATCH_SIZE + 1}/{(total_files + BATCH_SIZE - 1)//BATCH_SIZE}")
    
    for pdf_file in batch:
        pdf_path = os.path.join(PDF_DIR, pdf_file)
        result = extract_from_pdf(pdf_path)
        results.append(result)
        processed += 1
        
        if processed % 20 == 0:
            print(f"已处理: {processed}/{total_files}")

# 保存结果
with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=['Company', 'Year', 'Total Assets', 
                                          'Total Liabilities', 'Revenue', 'Net Profit', 
                                          'File', 'Status'])
    writer.writeheader()
    writer.writerows(sorted(results, key=lambda x: (x['Company'], x['Year'])))

# 统计
success_count = sum(1 for r in results if r['Status'] == 'Success')
success_rate = success_count / total_files * 100

print("\n" + "=" * 60)
print("提取完成!")
print(f"总文件数: {total_files}")
print(f"成功提取: {success_count}")
print(f"成功率: {success_rate:.1f}%")

# 各指标统计
print("\n各指标提取情况:")
for metric in ['Total Assets', 'Total Liabilities', 'Revenue', 'Net Profit']:
    count = sum(1 for r in results if r[metric])
    rate = count / total_files * 100
    print(f"  {metric}: {count} ({rate:.1f}%)")

print(f"\n结果已保存至: {OUTPUT_FILE}")