"""
财务数据提取模块
Financial Data Extraction Module
"""
import re
import csv
import os
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

try:
    import pdfplumber
except ImportError:
    print("Installing pdfplumber...")
    os.system("pip install pdfplumber")
    import pdfplumber

from ..models import FinancialData


class RegexExtractor:
    """正则表达式提取器"""
    
    def extract(self, pdf_path: Path) -> FinancialData:
        """提取财务数据"""
        return self.extract_from_pdf(pdf_path)


# 保留原名称以兼容
class FinancialExtractor(RegexExtractor):
    """财务数据提取器"""
    
    def __init__(self):
        # 定义提取模式
        self.patterns = {
            'total_assets': [
                r'(?:总资产|資產總[计計]|Total\s+Assets?)[:\s]*\$?\s*([0-9,，]+)',
                r'(?:资产总[计計]|Assets?\s+Total)[:\s]*\$?\s*([0-9,，]+)',
            ],
            'total_liabilities': [
                r'(?:总负债|負債總[计計]|Total\s+Liabilit(?:y|ies))[:\s]*\$?\s*([0-9,，]+)',
                r'(?:负债总[计計]|Liabilit(?:y|ies)\s+Total)[:\s]*\$?\s*([0-9,，]+)',
            ],
            'revenue': [
                r'(?:营业收入|營業收入|(?:Operating\s+)?Revenue)[:\s]*\$?\s*([0-9,，]+)',
                r'(?:收入总[额計]|Total\s+Revenue)[:\s]*\$?\s*([0-9,，]+)',
            ],
            'net_profit': [
                r'(?:净利润|淨利潤|Net\s+(?:Profit|Income))[:\s]*\$?\s*[\(（\-]?([0-9,，]+)[\)）]?',
                r'(?:净利|淨利|Net\s+(?:Loss|Profit))[:\s]*\$?\s*[\(（\-]?([0-9,，]+)[\)）]?',
            ]
        }
    
    def extract_number(self, text: str) -> Optional[float]:
        """从文本中提取数字"""
        if not text:
            return None
        # 移除逗号和其他字符
        text = text.replace(',', '').replace('，', '').replace(' ', '')
        try:
            return float(text)
        except:
            return None
    
    def extract_year(self, filename: str) -> Optional[int]:
        """从文件名提取年份"""
        match = re.search(r'20\d{2}', filename)
        return int(match.group()) if match else None
    
    def extract_from_pdf(self, pdf_path: Path) -> FinancialData:
        """从PDF提取数据"""
        filename = pdf_path.name
        company = filename.split('_')[0]
        year = self.extract_year(filename)
        
        result = FinancialData(
            company=company,
            year=year,
            file_name=filename
        )
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                # 读取前20页
                text = ''
                for i in range(min(20, len(pdf.pages))):
                    page = pdf.pages[i]
                    if page:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + '\n'
                
                # 应用正则表达式
                for field, pattern_list in self.patterns.items():
                    for pattern in pattern_list:
                        matches = re.findall(pattern, text, re.IGNORECASE)
                        if matches:
                            value = self.extract_number(matches[0])
                            if value:
                                setattr(result, field, value)
                                break
                
                # 更新状态
                if result.has_data:
                    result.status = "Success"
                    
        except Exception as e:
            result.status = f"Error: {str(e)[:50]}"
        
        return result


def extract_financial_data(
    input_dir: str = "data/raw_reports",
    output_dir: str = "output",
    limit: Optional[int] = None,
    batch_size: int = 100
) -> Tuple[str, float]:
    """
    提取财务数据主函数
    
    Args:
        input_dir: PDF文件目录
        output_dir: 输出目录
        limit: 限制处理文件数
        batch_size: 批处理大小
        
    Returns:
        (输出文件路径, 成功率)
    """
    # 确保输出目录存在
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # 获取PDF文件
    pdf_files = list(Path(input_dir).glob("*.pdf"))
    if limit:
        pdf_files = pdf_files[:limit]
    
    print(f"Found {len(pdf_files)} PDF files")
    
    # 创建提取器
    extractor = FinancialExtractor()
    results = []
    
    # 批量处理
    for i in range(0, len(pdf_files), batch_size):
        batch = pdf_files[i:i+batch_size]
        print(f"\nProcessing batch {i//batch_size + 1}/{(len(pdf_files) + batch_size - 1)//batch_size}")
        
        for pdf_path in batch:
            result = extractor.extract_from_pdf(pdf_path)
            results.append(result)
            
            if len(results) % 20 == 0:
                print(f"Processed: {len(results)}/{len(pdf_files)}")
    
    # 创建results和reports子目录
    results_dir = output_path / "results"
    reports_dir = output_path / "reports"
    results_dir.mkdir(exist_ok=True)
    reports_dir.mkdir(exist_ok=True)
    
    # 保存结果
    timestamp = datetime.now().strftime('%Y%m%d%H%M')
    output_file = results_dir / f"extraction_result_{timestamp}.csv"
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['Company', 'Year', 'Total Assets', 'Total Liabilities', 
                     'Revenue', 'Net Profit', 'File', 'Status']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for result in sorted(results, key=lambda x: (x.company, x.year or 0)):
            writer.writerow(result.to_dict())
    
    # 计算统计
    success_count = sum(1 for r in results if r.status == "Success")
    success_rate = success_count / len(results) * 100 if results else 0
    
    print(f"\n{'='*60}")
    print(f"Extraction completed!")
    print(f"Total files: {len(results)}")
    print(f"Successful: {success_count}")
    print(f"Success rate: {success_rate:.1f}%")
    print(f"Results saved to: {output_file}")
    
    return str(output_file), success_rate