"""
表格提取策略
Table Extraction Strategy
"""

import re
from typing import Any, Optional, List
from .base_strategy import BaseStrategy, ExtractionResult


class TableStrategy(BaseStrategy):
    """表格提取策略"""
    
    def __init__(self):
        super().__init__(name="table")
        
        # 定义要查找的关键词
        self.keywords = {
            'total_assets': [
                'total assets', 'assets', 'ativo total', '总资产', '資產總計'
            ],
            'total_liabilities': [
                'total liabilities', 'liabilities', 'passivo total', '总负债', '負債總計'
            ],
            'revenue': [
                'revenue', 'total revenue', 'receita', '营业收入', '營業收入', 
                'sales', 'turnover', 'income from operations'
            ],
            'net_profit': [
                'net income', 'net profit', 'net loss', 'loss for the year',
                'profit for the year', '净利润', '净亏损', '本期淨利', '淨利潤'
            ]
        }
    
    def can_handle(self, content: Any) -> bool:
        """判断是否能处理"""
        return hasattr(content, 'pages')
    
    def extract(self, content: Any, **kwargs) -> ExtractionResult:
        """从表格中提取财务数据"""
        result = ExtractionResult(method="table")
        
        if not hasattr(content, 'pages'):
            return result
        
        # 遍历前30页查找表格
        max_pages = min(30, len(content.pages))
        tables_found = 0
        
        for page_num in range(max_pages):
            page = content.pages[page_num]
            tables = page.extract_tables()
            
            if not tables:
                continue
            
            tables_found += len(tables)
            
            for table in tables:
                if not table:
                    continue
                
                # 遍历表格行
                for row in table:
                    if not row:
                        continue
                    
                    # 将行转换为字符串以便搜索
                    row_text = ' '.join(str(cell).lower() if cell else '' for cell in row)
                    
                    # 检查每个字段的关键词
                    for field, keywords in self.keywords.items():
                        # 如果已经找到了，跳过
                        if getattr(result, field) is not None:
                            continue
                        
                        for keyword in keywords:
                            if keyword.lower() in row_text:
                                # 从这一行提取数字
                                value = self._extract_value_from_row(row, field)
                                if value is not None:
                                    setattr(result, field, value)
                                    break
        
        if tables_found > 0:
            print(f"    📊 处理了 {tables_found} 个表格")
        
        result.update_confidence()
        return result
    
    def _extract_value_from_row(self, row: List, field: str) -> Optional[float]:
        """从表格行中提取数值"""
        numbers = []
        for cell in row:
            if cell:
                value = self._extract_number(str(cell))
                if value is not None:
                    numbers.append(value)
        
        if not numbers:
            return None
        
        # 过滤掉太小的数字
        valid_numbers = [n for n in numbers if abs(n) > 100]
        
        if not valid_numbers:
            return None
        
        # 对于净利润，可能是负数
        if field == 'net_profit':
            return valid_numbers[0]
        else:
            # 对于其他字段，选择最大的正数
            positive_nums = [n for n in valid_numbers if n > 0]
            if positive_nums:
                return max(positive_nums)
            else:
                return max(valid_numbers, key=abs)
    
    def _extract_number(self, text: str) -> Optional[float]:
        """从文本中提取数字"""
        if not text:
            return None
        
        # 清理文本
        text = text.replace(',', '').replace('，', '')
        text = text.replace('(', '-').replace(')', '')
        text = text.replace('（', '-').replace('）', '')
        
        # 提取数字
        pattern = r'-?\d+\.?\d*'
        match = re.search(pattern, text)
        
        if match:
            try:
                return float(match.group())
            except ValueError:
                pass
        
        return None