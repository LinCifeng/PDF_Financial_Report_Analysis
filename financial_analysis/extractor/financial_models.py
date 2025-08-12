"""
财务数据模型 - Extractor模块专用
Financial Data Models for Extractor Module

包含基础和扩展的财务数据模型
作者: Lin Cifeng
更新: 2025-08-10
"""
from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class FinancialData:
    """
    基础财务数据模型
    Basic financial data model with core metrics
    """
    # 基本信息
    company: str
    year: Optional[int] = None
    file_name: Optional[str] = None
    file_path: Optional[str] = None  # 文件完整路径
    
    # 核心财务指标
    total_assets: Optional[float] = None        # 总资产
    total_liabilities: Optional[float] = None   # 总负债
    revenue: Optional[float] = None             # 营业收入
    net_profit: Optional[float] = None          # 净利润
    
    # 状态信息
    status: str = "Failed"
    extraction_method: Optional[str] = None     # 提取方法
    confidence: Optional[float] = None          # 置信度
    success_level: Optional[str] = None         # 成功级别：完全成功/部分成功
    
    # 额外信息
    currency: Optional[str] = None              # 货币单位（USD, HKD, CNY等）
    unit_scale: Optional[str] = None            # 数值单位（千、百万、十亿）
    language: Optional[str] = None              # 财报语言
    
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
            'Status': self.status,
            'Success Level': self.success_level,
            'Currency': self.currency,
            'Unit': self.unit_scale,
            'Language': self.language
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


@dataclass
class BalanceSheetData:
    """资产负债表数据"""
    total_assets: Optional[float] = None
    total_liabilities: Optional[float] = None
    total_equity: Optional[float] = None
    cash_and_equivalents: Optional[float] = None
    loans_and_advances: Optional[float] = None
    customer_deposits: Optional[float] = None
    share_capital: Optional[float] = None
    retained_earnings: Optional[float] = None


@dataclass
class IncomeStatementData:
    """损益表数据"""
    revenue: Optional[float] = None
    interest_income: Optional[float] = None
    interest_expense: Optional[float] = None
    net_interest_income: Optional[float] = None
    operating_expenses: Optional[float] = None
    net_profit: Optional[float] = None
    earnings_before_tax: Optional[float] = None


@dataclass
class CashFlowData:
    """现金流量表数据"""
    operating_cash_flow: Optional[float] = None
    investing_cash_flow: Optional[float] = None
    financing_cash_flow: Optional[float] = None


@dataclass
class FinancialRatios:
    """财务比率"""
    debt_to_asset_ratio: Optional[float] = None
    return_on_equity: Optional[float] = None
    return_on_assets: Optional[float] = None
    net_interest_margin: Optional[float] = None
    cost_to_income_ratio: Optional[float] = None


@dataclass
class ExtendedFinancialData:
    """扩展的财务数据模型"""
    company: str
    year: int
    report_type: str
    
    balance_sheet: BalanceSheetData
    income_statement: IncomeStatementData
    cash_flow: CashFlowData
    ratios: FinancialRatios
    
    currency: str = "HKD"
    unit_multiplier: int = 1
    
    def calculate_ratios(self):
        """计算财务比率"""
        # 资产负债率
        if self.balance_sheet.total_liabilities and self.balance_sheet.total_assets:
            self.ratios.debt_to_asset_ratio = (
                self.balance_sheet.total_liabilities / self.balance_sheet.total_assets
            )
        
        # ROE
        if self.income_statement.net_profit and self.balance_sheet.total_equity:
            self.ratios.return_on_equity = (
                self.income_statement.net_profit / self.balance_sheet.total_equity
            )
        
        # ROA
        if self.income_statement.net_profit and self.balance_sheet.total_assets:
            self.ratios.return_on_assets = (
                self.income_statement.net_profit / self.balance_sheet.total_assets
            )
        
        # 净利息收益率
        if self.income_statement.net_interest_income and self.balance_sheet.total_assets:
            self.ratios.net_interest_margin = (
                self.income_statement.net_interest_income / self.balance_sheet.total_assets
            )
        
        # 成本收入比
        if self.income_statement.operating_expenses and self.income_statement.revenue:
            self.ratios.cost_to_income_ratio = (
                self.income_statement.operating_expenses / self.income_statement.revenue
            )