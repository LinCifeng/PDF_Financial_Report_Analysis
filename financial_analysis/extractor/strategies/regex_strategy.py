"""
正则表达式提取策略
Regex Extraction Strategy
"""

import re
from typing import Dict, Optional, Any, List
from .base_strategy import BaseStrategy, ExtractionResult


class RegexStrategy(BaseStrategy):
    """正则表达式提取策略"""
    
    def __init__(self):
        super().__init__(name="regex")
        self.patterns = self._get_all_patterns()
    
    def _get_all_patterns(self) -> Dict[str, List[str]]:
        """获取所有提取模式"""
        return {
            'total_assets': [
                # 英文 - 更多变体
                r'Total\s+Assets[\s:：]*[\$\s]*([0-9,]+(?:\.[0-9]+)?)',
                r'Assets[\s:：]*Total[\s:：]*[\$\s]*([0-9,]+(?:\.[0-9]+)?)',
                r'Total\s+assets[\s:：]*\(?in\s+millions?\)?[\s:：]*[\$\s]*([0-9,]+(?:\.[0-9]+)?)',
                r'TOTAL\s+ASSETS[\s:：]*([0-9,]+(?:\.[0-9]+)?)',
                r'Total\s+Assets\s*\n\s*([0-9,]+(?:\.[0-9]+)?)',
                r'Assets\s*\n\s*([0-9,]+(?:\.[0-9]+)?)',
                
                # 简体中文
                r'总资产[\s:：]*([0-9,]+(?:\.[0-9]+)?)',
                r'资产总计[\s:：]*([0-9,]+(?:\.[0-9]+)?)',
                r'资产总额[\s:：]*([0-9,]+(?:\.[0-9]+)?)',
                
                # 繁体中文
                r'總資產[\s:：]*([0-9,]+(?:\.[0-9]+)?)',
                r'資產總計[\s:：]*([0-9,]+(?:\.[0-9]+)?)',
                r'資產總值[\s:：]*([0-9,]+(?:\.[0-9]+)?)',
                r'資產總額[\s:：]*([0-9,]+(?:\.[0-9]+)?)',
                
                # 葡萄牙语/西班牙语
                r'Ativo\s+Total[\s:：]*R?\$?\s*([0-9.,]+(?:\.[0-9]+)?)',
                r'Total\s+do\s+Ativo[\s:：]*R?\$?\s*([0-9.,]+(?:\.[0-9]+)?)',
                r'Activos?\s+Totale?s?[\s:：]*\$?\s*([0-9.,]+(?:\.[0-9]+)?)',
                r'Total\s+de\s+Activos?[\s:：]*\$?\s*([0-9.,]+(?:\.[0-9]+)?)',
                
                # 表格模式 - 捕获换行后的数字
                r'(?:Total\s+)?Assets\s*\n+\s*([0-9,]+(?:\.[0-9]+)?)',
                r'Assets\s+Total\s*\n+\s*([0-9,]+(?:\.[0-9]+)?)',
            ],
            
            'total_liabilities': [
                # 英文 - 更多变体
                r'Total\s+Liabilities[\s:：]*[\$\s]*([0-9,]+(?:\.[0-9]+)?)',
                r'Liabilities[\s:：]*Total[\s:：]*[\$\s]*([0-9,]+(?:\.[0-9]+)?)',
                r'Total\s+liabilities\s+excluding[\s\S]{0,50}?([0-9,]+(?:\.[0-9]+)?)',
                r'TOTAL\s+LIABILITIES[\s:：]*([0-9,]+(?:\.[0-9]+)?)',
                r'Total\s+Liabilities\s*\n\s*([0-9,]+(?:\.[0-9]+)?)',
                r'Liabilities\s*\n\s*([0-9,]+(?:\.[0-9]+)?)',
                
                # 简体中文
                r'总负债[\s:：]*([0-9,]+(?:\.[0-9]+)?)',
                r'负债总计[\s:：]*([0-9,]+(?:\.[0-9]+)?)',
                
                # 繁体中文
                r'總負債[\s:：]*([0-9,]+(?:\.[0-9]+)?)',
                r'負債總計[\s:：]*([0-9,]+(?:\.[0-9]+)?)',
                r'負債總額[\s:：]*([0-9,]+(?:\.[0-9]+)?)',
                r'負債總值[\s:：]*([0-9,]+(?:\.[0-9]+)?)',
                
                # 葡萄牙语/西班牙语
                r'Passivo\s+Total[\s:：]*R?\$?\s*([0-9.,]+(?:\.[0-9]+)?)',
                r'Total\s+do\s+Passivo[\s:：]*R?\$?\s*([0-9.,]+(?:\.[0-9]+)?)',
                r'Pasivos?\s+Totale?s?[\s:：]*\$?\s*([0-9.,]+(?:\.[0-9]+)?)',
                r'Total\s+de\s+Pasivos?[\s:：]*\$?\s*([0-9.,]+(?:\.[0-9]+)?)',
                
                # 表格模式
                r'(?:Total\s+)?Liabilities\s*\n+\s*([0-9,]+(?:\.[0-9]+)?)',
            ],
            
            'revenue': [
                # 英文
                r'Total\s+Revenue[\s:：]*[\$\s]*([0-9,]+(?:\.[0-9]+)?)',
                r'Revenue[\s:：]*[\$\s]*([0-9,]+(?:\.[0-9]+)?)',
                r'Operating\s+revenue[\s:：]*[\$\s]*([0-9,]+(?:\.[0-9]+)?)',
                
                # 投资基金特有
                r'Total\s+investment\s+income[\s:：]*[\$\s]*([0-9,]+(?:\.[0-9]+)?)',
                r'Investment\s+income[\s\S]{0,50}?([0-9,]+(?:\.[0-9]+)?)',
                
                # 简体中文
                r'营业收入[\s:：]*([0-9,]+(?:\.[0-9]+)?)',
                r'总收入[\s:：]*([0-9,]+(?:\.[0-9]+)?)',
                
                # 繁体中文
                r'營業收入[\s:：]*([0-9,]+(?:\.[0-9]+)?)',
                r'總收入[\s:：]*([0-9,]+(?:\.[0-9]+)?)',
                
                # 葡萄牙语
                r'Receitas?\s+Totais?[\s:：]*R?\$?\s*([0-9.,]+(?:\.[0-9]+)?)',
                r'Receita\s+Líquida[\s:：]*R?\$?\s*([0-9.,]+(?:\.[0-9]+)?)',
            ],
            
            'net_profit': [
                # 英文 - 利润
                r'Net\s+Income[\s:：]*[\$\s]*([0-9,]+(?:\.[0-9]+)?)',
                r'Net\s+Profit[\s:：]*[\$\s]*([0-9,]+(?:\.[0-9]+)?)',
                r'Profit\s+for\s+the\s+(?:year|period)[\s:：]*[\$\s]*([0-9,]+(?:\.[0-9]+)?)',
                
                # 英文 - 亏损
                r'Net\s+Loss[\s:：]*[\$\s]*\(?([0-9,]+(?:\.[0-9]+)?)\)?',
                r'Loss\s+for\s+the\s+(?:year|period|quarter)[\s:：]*[\$\s]*\(?([0-9,]+(?:\.[0-9]+)?)\)?',
                
                # 简体中文
                r'净利润[\s:：]*([0-9,]+(?:\.[0-9]+)?)',
                r'净亏损[\s:：]*\(?([0-9,]+(?:\.[0-9]+)?)\)?',
                
                # 繁体中文
                r'淨利潤[\s:：]*([0-9,]+(?:\.[0-9]+)?)',
                r'本期淨利[\s:：]*([0-9,]+(?:\.[0-9]+)?)',
                r'稅後淨利[\s:：]*([0-9,]+(?:\.[0-9]+)?)',
                
                # 葡萄牙语
                r'Lucro\s+Líquido[\s:：]*R?\$?\s*([0-9.,]+(?:\.[0-9]+)?)',
                r'Prejuízo\s+Líquido[\s:：]*R?\$?\s*\(?([0-9.,]+(?:\.[0-9]+)?)\)?',
            ]
        }
    
    def can_handle(self, content: Any) -> bool:
        """判断是否能处理"""
        return isinstance(content, str) and len(content) > 0
    
    def extract(self, content: str, **kwargs) -> ExtractionResult:
        """使用正则表达式提取财务数据"""
        result = ExtractionResult(method="regex")
        unit_multiplier = kwargs.get('unit_multiplier', 1.0)
        
        if not content:
            return result
        
        # 应用所有正则模式
        for field, pattern_list in self.patterns.items():
            for pattern in pattern_list:
                matches = re.findall(pattern, content, re.IGNORECASE | re.MULTILINE)
                if matches:
                    value = self._extract_number(matches[0])
                    
                    if value is not None:
                        # 处理负数
                        if field == 'net_profit' and ('loss' in pattern.lower() or '亏损' in pattern):
                            value = -abs(value)
                        
                        # 应用单位乘数
                        value = value * unit_multiplier
                        
                        # 设置结果
                        setattr(result, field, value)
                        break
        
        result.update_confidence()
        return result
    
    def _extract_number(self, text: Any) -> Optional[float]:
        """从文本中提取数字"""
        if text is None:
            return None
        
        # 如果是元组，取最后一个非空元素
        if isinstance(text, tuple):
            for item in reversed(text):
                if item and item.strip():
                    text = item
                    break
        
        # 转换为字符串
        text = str(text)
        
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