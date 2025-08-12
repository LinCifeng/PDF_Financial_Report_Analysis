"""
基础提取器类 - 包含所有提取器的公共功能
Base Extractor - Common functionality for all extractors

作者: Lin Cifeng
创建时间: 2025-08-10
"""
import re
from typing import Optional, List, Dict, Any
from pathlib import Path
from abc import ABC, abstractmethod
import pdfplumber

from .financial_models import FinancialData


class BaseExtractor(ABC):
    """所有提取器的基类"""
    
    def __init__(self):
        # 单位检测模式 - 所有提取器共享
        self.unit_patterns = [
            (r"in\s+thousands", 1000),
            (r"in\s+millions", 1000000),
            (r"千元|千港元", 1000),
            (r"百万|百萬", 1000000),
            (r"'000", 1000),
            (r"HK\$'000", 1000),
        ]
    
    def extract_number(self, text: str) -> Optional[float]:
        """
        从文本中提取数字 - 支持多语言格式
        """
        if not text:
            return None
        
        text = str(text)
        is_negative = '(' in text and ')' in text
        
        # 移除括号和货币符号
        text = text.replace('(', '').replace(')', '')
        text = text.replace('$', '').replace('¥', '').replace('R', '').replace('€', '')
        
        import re
        # 检测葡萄牙语格式 (1.234,56)
        if re.search(r'\d+\.\d{3}', text) and ',' in text:
            text = text.replace('.', '').replace(',', '.')
        else:
            # 英文格式 (1,234.56)
            text = text.replace(',', '').replace('，', '')
        
        # 提取数字
        match = re.search(r'-?[0-9]+\.?[0-9]*', text)
        if match:
            try:
                value = float(match.group())
                return -abs(value) if is_negative else value
            except:
                pass
        return None
    
    def extract_year(self, filename: str) -> Optional[int]:
        """
        从文件名提取年份
        支持多种年份格式
        """
        # 尝试不同的年份模式
        patterns = [
            r'20\d{2}',  # 标准4位年份
            r'FY20\d{2}',  # 财年格式
            r'Annual_20\d{2}',  # Annual Report格式
        ]
        
        for pattern in patterns:
            match = re.search(pattern, filename)
            if match:
                # 提取数字部分
                year_str = re.search(r'20\d{2}', match.group())
                if year_str:
                    return int(year_str.group())
        
        return None
    
    def detect_unit(self, text: str) -> int:
        """
        检测财务报表的单位
        返回单位乘数 (1, 1000, 1000000等)
        """
        if not text:
            return 1
        
        # 只检查前3000个字符以提高性能
        text_sample = text[:3000].lower()
        
        for pattern, multiplier in self.unit_patterns:
            if re.search(pattern, text_sample, re.IGNORECASE):
                return multiplier
        
        return 1
    
    def clean_company_name(self, filename: str) -> str:
        """
        从文件名中提取公司名称
        处理各种文件命名格式
        """
        # 移除文件扩展名
        name = Path(filename).stem
        
        # 分割并取第一部分（通常是公司名）
        parts = name.split('_')
        company = parts[0]
        
        # 清理公司名
        company = company.replace('-', ' ')
        company = re.sub(r'\d{4}', '', company)  # 移除年份
        company = company.strip()
        
        return company or "Unknown"
    
    def extract_from_pdf(self, pdf_path) -> FinancialData:
        """
        从PDF提取数据的主方法
        子类需要实现具体的提取逻辑
        """
        # 处理不同类型的输入
        if isinstance(pdf_path, str):
            from pathlib import Path
            pdf_path = Path(pdf_path)
        
        filename = pdf_path.name
        company = self.clean_company_name(filename)
        year = self.extract_year(filename)
        
        result = FinancialData(
            company=company,
            year=year,
            file_name=filename,
            file_path=str(pdf_path)  # 添加文件路径
        )
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                # 调用子类实现的具体提取方法
                self._extract_data(pdf, result)
                
                # 更新状态
                if result.has_data:
                    result.status = "Success"
                    
        except Exception as e:
            result.status = f"Error: {str(e)[:50]}"
        
        return result
    
    @abstractmethod
    def _extract_data(self, pdf: pdfplumber.PDF, result: FinancialData) -> None:
        """
        具体的数据提取逻辑
        子类必须实现此方法
        
        Args:
            pdf: pdfplumber PDF对象
            result: 要填充的FinancialData对象
        """
        pass
    
    def process_negative_numbers(self, value: str, context: str = "") -> float:
        """
        处理负数的各种表示方式
        
        Args:
            value: 数值字符串
            context: 上下文，用于判断是否应该是负数
        """
        # 提取基础数值
        num = self.extract_number(value)
        if num is None:
            return None
        
        # 检查上下文中的负数指示符
        negative_indicators = [
            'loss', '亏损', '虧損',
            'deficit', '赤字',
            'decrease', '减少',
            '(', ')'  # 括号通常表示负数
        ]
        
        context_lower = context.lower()
        if any(indicator in context_lower or indicator in value for indicator in negative_indicators):
            return -abs(num)
        
        return num
    
    def extract_text_from_pages(self, pdf: pdfplumber.PDF, max_pages: int = 20) -> str:
        """
        从PDF中提取文本
        
        Args:
            pdf: pdfplumber PDF对象
            max_pages: 最多读取的页数
        
        Returns:
            提取的文本内容
        """
        text = ""
        pages_to_read = min(max_pages, len(pdf.pages))
        
        for i in range(pages_to_read):
            try:
                page = pdf.pages[i]
                if page:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + '\n'
            except Exception:
                continue
        
        return text
    
    def find_value_near_keyword(self, text: str, keywords: List[str], 
                                search_window: int = 100) -> Optional[float]:
        """
        在关键词附近查找数值
        
        Args:
            text: 要搜索的文本
            keywords: 关键词列表
            search_window: 搜索窗口大小（字符数）
        
        Returns:
            找到的数值，如果没找到返回None
        """
        for keyword in keywords:
            # 查找关键词位置
            pattern = re.compile(re.escape(keyword), re.IGNORECASE)
            matches = pattern.finditer(text)
            
            for match in matches:
                start = match.end()
                end = min(start + search_window, len(text))
                
                # 在关键词后的窗口内查找数字
                window_text = text[start:end]
                
                # 查找数字模式
                number_pattern = r'[\$HK\$]*\s*([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]+)?)'
                number_matches = re.findall(number_pattern, window_text)
                
                if number_matches:
                    value = self.extract_number(number_matches[0])
                    if value is not None:
                        return value
        
        return None
    
    def validate_extraction_result(self, data: Dict[str, Any]) -> bool:
        """
        验证提取结果的合理性
        
        Args:
            data: 提取的数据字典
        
        Returns:
            True if data seems valid, False otherwise
        """
        # 基本验证规则
        if not data:
            return False
        
        # 检查是否有任何有效数据
        has_valid_data = any(
            value is not None and value != 0 
            for value in data.values() 
            if isinstance(value, (int, float))
        )
        
        if not has_valid_data:
            return False
        
        # 财务数据合理性检查
        if 'total_assets' in data and 'total_liabilities' in data:
            # 资产应该大于等于负债（在正常情况下）
            if data['total_assets'] < data['total_liabilities'] * 0.5:
                return False
        
        # 数值范围检查（避免明显错误的数据）
        for key, value in data.items():
            if isinstance(value, (int, float)):
                # 财务数据通常在合理范围内
                if abs(value) > 1e15:  # 超过1000万亿
                    return False
        
        return True