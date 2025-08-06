#!/usr/bin/env python3
"""
快速财务数据提取 - 并行处理版本
Fast Financial Data Extraction with Parallel Processing
"""
import re
import csv
from pathlib import Path
from datetime import datetime
import concurrent.futures
import os

# 尝试导入pdfplumber，如果失败则安装
try:
    import pdfplumber
except ImportError:
    print("正在安装pdfplumber...")
    os.system("pip3 install pdfplumber")
    import pdfplumber

# 配置
PDF_DIR = Path("data/raw_reports")
OUTPUT_DIR = Path("output/extractions")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
TIMESTAMP = datetime.now().strftime('%Y%m%d_%H%M%S')
OUTPUT_FILE = OUTPUT_DIR / f"extraction_results_{TIMESTAMP}.csv"

# 正则表达式模式（简化版，专注于关键指标）
PATTERNS = {
    'total_assets': r'(?:总资产|資產總[计計]|Total\s+Assets?)[:\s]*\$?\s*([0-9,，]+)',
    'total_liabilities': r'(?:总负债|負債總[计計]|Total\s+Liabilit(?:y|ies))[:\s]*\$?\s*([0-9,，]+)',
    'revenue': r'(?:营业收入|營業收入|Revenue)[:\s]*\$?\s*([0-9,，]+)',
    'net_profit': r'(?:净利润|淨利潤|Net\s+(?:Profit|Income))[:\s]*\$?\s*[\(（\-]?([0-9,，]+)[\)）]?',
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

def extract_year(filename):
    """从文件名提取年份"""
    match = re.search(r'20\d{2}', filename)
    return int(match.group()) if match else None

def process_single_pdf(pdf_path):
    """处理单个PDF"""
    result = {
        'Company': pdf_path.stem.split('_')[0],
        'Year': extract_year(pdf_path.name),
        'Total Assets': None,
        'Total Liabilities': None,
        'Revenue': None,
        'Net Profit': None,
        'File': pdf_path.name,
        'Status': 'Failed'
    }
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            # 只读取前20页（财务数据通常在前面）
            text = ''
            for i, page in enumerate(pdf.pages[:20]):
                if page:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + '\n'
            
            # 应用正则表达式
            for field, pattern in PATTERNS.items():
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    value = extract_number(match.group(1))
                    if value:
                        if field == 'total_assets':
                            result['Total Assets'] = value
                        elif field == 'total_liabilities':
                            result['Total Liabilities'] = value
                        elif field == 'revenue':
                            result['Revenue'] = value
                        elif field == 'net_profit':
                            result['Net Profit'] = value
            
            # 检查是否提取到任何数据
            if any([result['Total Assets'], result['Total Liabilities'], 
                   result['Revenue'], result['Net Profit']]):
                result['Status'] = 'Success'
                
    except Exception as e:
        result['Status'] = f'Error: {str(e)[:50]}'
    
    return result

def main():
    """主函数"""
    print("=" * 60)
    print("快速财务数据提取系统")
    print("=" * 60)
    
    # 获取所有PDF文件
    pdf_files = list(PDF_DIR.glob("*.pdf"))
    total_files = len(pdf_files)
    print(f"找到 {total_files} 个PDF文件")
    
    # 限制处理数量（可以调整）
    LIMIT = 200  # 先处理200个文件
    pdf_files = pdf_files[:LIMIT]
    print(f"本次处理: {len(pdf_files)} 个文件")
    
    # 并行处理
    results = []
    print("\n开始提取...")
    start_time = datetime.now()
    
    # 使用进程池进行并行处理
    with concurrent.futures.ProcessPoolExecutor(max_workers=4) as executor:
        # 提交所有任务
        future_to_pdf = {executor.submit(process_single_pdf, pdf): pdf 
                        for pdf in pdf_files}
        
        # 处理完成的任务
        completed = 0
        for future in concurrent.futures.as_completed(future_to_pdf):
            pdf = future_to_pdf[future]
            try:
                result = future.result()
                results.append(result)
                completed += 1
                if completed % 10 == 0:
                    print(f"已处理: {completed}/{len(pdf_files)}")
            except Exception as e:
                print(f"处理 {pdf.name} 时出错: {e}")
    
    # 保存结果
    with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['Company', 'Year', 'Total Assets', 'Total Liabilities', 
                     'Revenue', 'Net Profit', 'File', 'Status']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(sorted(results, key=lambda x: (x['Company'], x['Year'] or 0)))
    
    # 统计
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    success_count = sum(1 for r in results if r['Status'] == 'Success')
    success_rate = success_count / len(results) * 100 if results else 0
    
    print("\n" + "=" * 60)
    print(f"提取完成!")
    print(f"处理时间: {duration:.1f} 秒")
    print(f"处理文件: {len(results)} 个")
    print(f"成功提取: {success_count} 个")
    print(f"成功率: {success_rate:.1f}%")
    print(f"\n结果保存至: {OUTPUT_FILE}")
    
    # 打印各指标提取情况
    metrics = ['Total Assets', 'Total Liabilities', 'Revenue', 'Net Profit']
    print("\n各指标提取情况:")
    for metric in metrics:
        count = sum(1 for r in results if r[metric] is not None)
        rate = count / len(results) * 100 if results else 0
        print(f"  {metric}: {count}/{len(results)} ({rate:.1f}%)")

if __name__ == "__main__":
    main()