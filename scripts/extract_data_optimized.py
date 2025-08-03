#!/usr/bin/env python3
"""
优化版数据提取脚本 - 提高提取准确率
Optimized data extraction script with improved accuracy
"""

import os
import re
import csv
from pathlib import Path
from datetime import datetime
import logging
import pdfplumber
from tqdm import tqdm

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class OptimizedExtractor:
    def __init__(self):
        self.pdf_dir = Path("data/raw_reports")
        self.output_dir = Path("output")
        self.output_dir.mkdir(exist_ok=True)
        
        # 优化的正则表达式模式
        self.patterns = {
            'total_assets': [
                # 英文模式
                r'total\s+assets?\s*[:：]?\s*([\d,]+)',
                r'assets\s+total\s*[:：]?\s*([\d,]+)',
                # 中文模式
                r'[总總]?[资資]产[总總][计計额額]?\s*[:：]?\s*([\d,]+)',
                r'[资資]产[总總][计計]?\s*[:：]?\s*([\d,]+)',
                # 表格模式
                r'[总總]?[资資]产\s*\n\s*([\d,]+)',
                r'Assets\s*\n\s*([\d,]+)',
            ],
            
            'total_liabilities': [
                # 英文模式
                r'total\s+liabilit(?:y|ies)\s*[:：]?\s*([\d,]+)',
                r'liabilities\s+total\s*[:：]?\s*([\d,]+)',
                # 中文模式
                r'[负負][债債][总總][计計额額]?\s*[:：]?\s*([\d,]+)',
                r'[总總][负負][债債]\s*[:：]?\s*([\d,]+)',
                # 表格模式
                r'[负負][债債]\s*\n\s*([\d,]+)',
                r'Liabilities\s*\n\s*([\d,]+)',
            ],
            
            'revenue': [
                # 英文模式
                r'(?:total\s+)?revenue\s*[:：]?\s*([\d,]+)',
                r'operating\s+income\s*[:：]?\s*([\d,]+)',
                r'total\s+income\s*[:：]?\s*([\d,]+)',
                r'net\s+interest\s+income\s*[:：]?\s*([\d,]+)',  # 银行特有
                # 中文模式
                r'[营營][业業]收入\s*[:：]?\s*([\d,]+)',
                r'收入[总總][计計额額]?\s*[:：]?\s*([\d,]+)',
                r'[营營]收\s*[:：]?\s*([\d,]+)',
                r'利息[净淨]收入\s*[:：]?\s*([\d,]+)',  # 银行特有
            ],
            
            'net_profit': [
                # 英文模式 - 利润
                r'net\s+(?:profit|income)\s*[:：]?\s*([\d,]+)',
                r'profit\s+for\s+the\s+(?:year|period)\s*[:：]?\s*([\d,]+)',
                r'profit\s+attributable\s+to\s+.*?\s*[:：]?\s*([\d,]+)',
                # 英文模式 - 亏损
                r'net\s+loss\s*[:：]?\s*\(?([\d,]+)\)?',
                r'loss\s+for\s+the\s+(?:year|period)\s*[:：]?\s*\(?([\d,]+)\)?',
                # 中文模式 - 利润
                r'[净淨][利][润潤]\s*[:：]?\s*([\-\d,]+)',
                r'本[年期][利][润潤]\s*[:：]?\s*([\-\d,]+)',
                r'[净淨]收[益]?\s*[:：]?\s*([\-\d,]+)',
                r'本公司[拥擁]有人[应應][占佔][利][润潤]\s*[:：]?\s*([\-\d,]+)',
                # 中文模式 - 亏损
                r'[净淨][损損]失\s*[:：]?\s*\(?([\d,]+)\)?',
                r'本[年期][损損]失\s*[:：]?\s*\(?([\d,]+)\)?',
                r'[亏虧][损損]\s*[:：]?\s*\(?([\d,]+)\)?',
                # 括号表示负数
                r'[净淨][利][润潤]\s*[:：]?\s*\(([\d,]+)\)',
                r'net\s+(?:profit|income)\s*[:：]?\s*\(([\d,]+)\)',
            ]
        }
    
    def extract_number(self, text):
        """从文本中提取数字，处理逗号和负数"""
        if not text:
            return None
        # 移除逗号和空格
        text = text.replace(',', '').replace(' ', '').strip()
        # 处理括号表示的负数
        if text.startswith('(') and text.endswith(')'):
            text = '-' + text[1:-1]
        try:
            return int(float(text))
        except:
            return None
    
    def is_loss_context(self, text, match_pos):
        """判断是否在亏损上下文中"""
        # 获取匹配位置前后的文本
        start = max(0, match_pos - 100)
        end = min(len(text), match_pos + 100)
        context = text[start:end].lower()
        
        # 亏损关键词
        loss_keywords = ['loss', '亏损', '損失', 'deficit', '赤字', 'negative']
        return any(keyword in context for keyword in loss_keywords)
    
    def extract_from_pdf(self, pdf_path):
        """优化的PDF数据提取"""
        result = {
            'total_assets': None,
            'total_liabilities': None,
            'revenue': None,
            'net_profit': None
        }
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                # 提取前20页文本（通常财务数据在前面）
                text = ''
                for i, page in enumerate(pdf.pages[:20]):
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + '\n'
                
                # 处理文本：移除多余空格，但保留换行
                text = re.sub(r'[ \t]+', ' ', text)
                
                # 提取各个字段
                for field, patterns in self.patterns.items():
                    for pattern in patterns:
                        matches = list(re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE))
                        if matches:
                            # 使用最后一个匹配（通常是最终值）
                            match = matches[-1]
                            value = self.extract_number(match.group(1))
                            
                            if value and field == 'net_profit':
                                # 检查是否应该是负数
                                if 'loss' in pattern.lower() or '损失' in pattern or '亏' in pattern:
                                    value = -abs(value)
                                elif self.is_loss_context(text, match.start()):
                                    value = -abs(value)
                            
                            if value:
                                result[field] = value
                                break
                
                # 特殊处理：如果找到了括号中的数字，可能是负数
                if result['net_profit'] and result['net_profit'] > 0:
                    # 再次检查是否有括号版本
                    bracket_patterns = [
                        r'[净淨][利][润潤]\s*[:：]?\s*\(([\d,]+)\)',
                        r'net\s+(?:profit|income)\s*[:：]?\s*\(([\d,]+)\)'
                    ]
                    for pattern in bracket_patterns:
                        match = re.search(pattern, text, re.IGNORECASE)
                        if match:
                            value = self.extract_number(match.group(1))
                            if value:
                                result['net_profit'] = -abs(value)
                                break
                
        except Exception as e:
            logger.error(f"Error extracting from {pdf_path}: {e}")
        
        return result
    
    def process_all_pdfs(self):
        """处理所有PDF文件"""
        pdf_files = list(self.pdf_dir.glob("*.pdf"))
        logger.info(f"Found {len(pdf_files)} PDF files")
        
        results = []
        stats = {
            'total': len(pdf_files),
            'success': 0,
            'fields': {field: 0 for field in self.patterns.keys()}
        }
        
        for pdf_path in tqdm(pdf_files, desc="Extracting"):
            company_name = pdf_path.stem.split('_')[0]
            year_match = re.search(r'20\d{2}', pdf_path.name)
            year = int(year_match.group()) if year_match else None
            
            data = self.extract_from_pdf(pdf_path)
            
            result = {
                'company_name': company_name,
                'year': year,
                'file_name': pdf_path.name,
                **data
            }
            
            results.append(result)
            
            # 统计
            if any(data.values()):
                stats['success'] += 1
            
            for field, value in data.items():
                if value is not None:
                    stats['fields'][field] += 1
        
        # 保存结果
        csv_path = self.output_dir / "optimized_extraction_results.csv"
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['company_name', 'year', 'file_name', 
                         'total_assets', 'total_liabilities', 'revenue', 'net_profit']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for result in sorted(results, key=lambda x: (x['company_name'], x['year'] or 0)):
                writer.writerow(result)
        
        # 打印统计
        print(f"\n✅ 提取完成!")
        print(f"CSV文件: {csv_path}")
        print(f"成功提取数据: {stats['success']}/{stats['total']} ({stats['success']/stats['total']*100:.1f}%)")
        print("\n字段提取情况:")
        for field, count in stats['fields'].items():
            print(f"  {field}: {count} ({count/stats['total']*100:.1f}%)")
        
        # 特别统计净利润
        profit_results = [r for r in results if r.get('net_profit') is not None]
        if profit_results:
            positive = sum(1 for r in profit_results if r['net_profit'] > 0)
            negative = sum(1 for r in profit_results if r['net_profit'] < 0)
            print(f"\n净利润分析:")
            print(f"  盈利: {positive} 家")
            print(f"  亏损: {negative} 家")

def main():
    print("🚀 启动优化版数据提取...")
    extractor = OptimizedExtractor()
    extractor.process_all_pdfs()

if __name__ == "__main__":
    main()