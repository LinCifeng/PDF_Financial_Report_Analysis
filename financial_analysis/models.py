"""
数据模型定义
Data Model Definitions
"""
from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class FinancialData:
    """财务数据模型"""
    company: str
    year: Optional[int] = None
    total_assets: Optional[float] = None
    total_liabilities: Optional[float] = None
    revenue: Optional[float] = None
    net_profit: Optional[float] = None
    file_name: Optional[str] = None
    status: str = "Failed"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'Company': self.company,
            'Year': self.year,
            'Total Assets': self.total_assets,
            'Total Liabilities': self.total_liabilities,
            'Revenue': self.revenue,
            'Net Profit': self.net_profit,
            'File': self.file_name,
            'Status': self.status
        }
    
    @property
    def has_data(self) -> bool:
        """检查是否有有效数据"""
        return any([
            self.total_assets,
            self.total_liabilities,
            self.revenue,
            self.net_profit
        ])