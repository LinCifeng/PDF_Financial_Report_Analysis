"""
基础策略接口
Base Strategy Interface
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional, Any
from dataclasses import dataclass


@dataclass
class ExtractionResult:
    """提取结果"""
    total_assets: Optional[float] = None
    total_liabilities: Optional[float] = None
    revenue: Optional[float] = None
    net_profit: Optional[float] = None
    confidence: float = 0.0
    method: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'total_assets': self.total_assets,
            'total_liabilities': self.total_liabilities,
            'revenue': self.revenue,
            'net_profit': self.net_profit,
            'confidence': self.confidence,
            'method': self.method
        }
    
    def merge(self, other: 'ExtractionResult') -> None:
        """合并另一个结果（填充空缺字段）"""
        if self.total_assets is None and other.total_assets is not None:
            self.total_assets = other.total_assets
        if self.total_liabilities is None and other.total_liabilities is not None:
            self.total_liabilities = other.total_liabilities
        if self.revenue is None and other.revenue is not None:
            self.revenue = other.revenue
        if self.net_profit is None and other.net_profit is not None:
            self.net_profit = other.net_profit
        self.update_confidence()
    
    def update_confidence(self) -> None:
        """更新置信度"""
        fields_found = sum([
            self.total_assets is not None,
            self.total_liabilities is not None,
            self.revenue is not None,
            self.net_profit is not None
        ])
        self.confidence = fields_found / 4.0
    
    @property
    def is_complete(self) -> bool:
        """是否所有字段都已提取"""
        return all([
            self.total_assets is not None,
            self.total_liabilities is not None,
            self.revenue is not None,
            self.net_profit is not None
        ])
    
    @property
    def fields_count(self) -> int:
        """已提取字段数"""
        return sum([
            self.total_assets is not None,
            self.total_liabilities is not None,
            self.revenue is not None,
            self.net_profit is not None
        ])


class BaseStrategy(ABC):
    """提取策略基类"""
    
    def __init__(self, name: str = "base"):
        self.name = name
        self.stats = {
            'attempts': 0,
            'successes': 0,
            'failures': 0
        }
    
    @abstractmethod
    def extract(self, content: Any, **kwargs) -> ExtractionResult:
        """执行提取"""
        pass
    
    @abstractmethod
    def can_handle(self, content: Any) -> bool:
        """判断策略是否能处理该内容"""
        pass
    
    def execute(self, content: Any, **kwargs) -> ExtractionResult:
        """执行完整的提取流程"""
        self.stats['attempts'] += 1
        
        try:
            result = self.extract(content, **kwargs)
            
            if result.fields_count > 0:
                self.stats['successes'] += 1
            else:
                self.stats['failures'] += 1
            
            return result
            
        except Exception as e:
            print(f"  ❌ {self.name}策略失败: {str(e)[:100]}")
            self.stats['failures'] += 1
            return ExtractionResult(method=f"{self.name}_failed")