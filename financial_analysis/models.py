"""
数据模型定义
Data Model Definitions

包含基础和扩展的财务数据模型
"""
from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class FinancialData:
    """基础财务数据模型"""
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