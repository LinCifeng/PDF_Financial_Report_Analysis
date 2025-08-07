#!/usr/bin/env python3
"""
主提取器 - 整合所有提取逻辑
Master Extractor - Integrated All Extraction Logic

作者: Lin Cifeng
创建时间: 2025-08-06

整合了正则、LLM、表格、OCR等多种提取方法
支持20+财务指标的全面提取
"""
import re
import pandas as pd
from pathlib import Path
import pdfplumber
from typing import Dict, List, Optional, Tuple, Any
import json
import warnings
import sys
from datetime import datetime

warnings.filterwarnings('ignore')

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from scripts.deepseek_client import DeepSeekClient
except:
    DeepSeekClient = None


class MasterExtractor:
    """主提取器类"""
    
    def __init__(self, use_llm: bool = True, api_key: Optional[str] = None):
        self.use_llm = use_llm and DeepSeekClient is not None
        self.api_key = api_key
        
        # 初始化LLM客户端
        if self.use_llm:
            try:
                self.llm_client = DeepSeekClient(api_key)
            except:
                self.use_llm = False
                self.llm_client = None
        
        # 定义完整的财务指标集
        self.financial_metrics = self._define_metrics()
        
        # 单位检测模式
        self.unit_patterns = [
            (r"in\s+thousands", 1000),
            (r"in\s+millions", 1000000),
            (r"千元|千港元", 1000),
            (r"百万|百萬", 1000000),
            (r"'000", 1000),
            (r"HK\$'000", 1000),
        ]
        
        # 银行特殊模式
        self.bank_specific_patterns = {
            'interest_income': [
                r'Interest\s+income[\s\n]*[^\d]*?(\d{1,3}(?:,\d{3})*(?:\.\d+)?)',
                r'利息收入[\s：:]*(\d{1,3}(?:,\d{3})*(?:\.\d+)?)',
            ],
            'net_interest_income': [
                r'Net\s+interest\s+income[\s\n]*[^\d]*?(\d{1,3}(?:,\d{3})*(?:\.\d+)?)',
                r'净利息收入|淨利息收入[\s：:]*(\d{1,3}(?:,\d{3})*(?:\.\d+)?)',
            ],
            'fee_income': [
                r'Fee\s+(?:and\s+)?commission\s+income[\s\n]*[^\d]*?(\d{1,3}(?:,\d{3})*(?:\.\d+)?)',
                r'手续费(?:及佣金)?收入[\s：:]*(\d{1,3}(?:,\d{3})*(?:\.\d+)?)',
            ]
        }
    
    def _define_metrics(self) -> Dict:
        """定义20+财务指标"""
        return {
            # ========== 资产负债表 (Balance Sheet) ==========
            'total_assets': {
                'patterns': [
                    r'Total\s+Assets[\s\n]*[\$HK\$]*\s*([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]+)?)',
                    r'资产总计|總資產[\s：:]*([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]+)?)',
                ],
                'category': 'balance_sheet',
                'priority': 1
            },
            
            'total_liabilities': {
                'patterns': [
                    r'Total\s+Liabilities[\s\n]*[\$HK\$]*\s*([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]+)?)',
                    r'负债总计|總負債[\s：:]*([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]+)?)',
                ],
                'category': 'balance_sheet',
                'priority': 1
            },
            
            'total_equity': {
                'patterns': [
                    r'Total\s+Equity[\s\n]*[\$HK\$]*\s*([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]+)?)',
                    r'所有者权益|股東權益[\s：:]*([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]+)?)',
                ],
                'category': 'balance_sheet',
                'priority': 2
            },
            
            'cash_and_equivalents': {
                'patterns': [
                    r'Cash\s+and\s+(?:cash\s+)?equivalents[\s\n]*[\$HK\$]*\s*([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]+)?)',
                    r'现金及现金等价物[\s：:]*([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]+)?)',
                ],
                'category': 'balance_sheet',
                'priority': 2
            },
            
            'loans_and_advances': {
                'patterns': [
                    r'Loans\s+and\s+advances(?:\s+to\s+customers)?[\s\n]*[\$HK\$]*\s*([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]+)?)',
                    r'贷款及垫款|客戶貸款[\s：:]*([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]+)?)',
                ],
                'category': 'balance_sheet',
                'priority': 2
            },
            
            'customer_deposits': {
                'patterns': [
                    r'(?:Customer\s+)?Deposits(?:\s+from\s+customers)?[\s\n]*[\$HK\$]*\s*([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]+)?)',
                    r'客户存款[\s：:]*([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]+)?)',
                ],
                'category': 'balance_sheet',
                'priority': 2
            },
            
            # ========== 损益表 (Income Statement) ==========
            'revenue': {
                'patterns': [
                    r'(?:Total\s+)?(?:Operating\s+)?Revenue[\s\n]*[\$HK\$]*\s*([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]+)?)',
                    r'营业收入|總收入[\s：:]*([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]+)?)',
                ],
                'category': 'income_statement',
                'priority': 1
            },
            
            'net_profit': {
                'patterns': [
                    r'Net\s+(?:profit|income|loss)[\s\n]*[^\d]*?\(?(-?\d{1,3}(?:,\d{3})*(?:\.\d+)?)\)?',
                    r'净利润|淨利潤|净亏损[\s：:]*\(?(-?\d{1,3}(?:,\d{3})*(?:\.\d+)?)\)?',
                ],
                'category': 'income_statement',
                'priority': 1
            },
            
            'operating_expenses': {
                'patterns': [
                    r'(?:Total\s+)?Operating\s+expenses[\s\n]*[\$HK\$]*\s*([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]+)?)',
                    r'营业费用|營業費用[\s：:]*([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]+)?)',
                ],
                'category': 'income_statement',
                'priority': 2
            },
            
            'ebit': {
                'patterns': [
                    r'(?:Profit|Loss)\s+before\s+(?:income\s+)?tax[\s\n]*[^\d]*?\(?(-?\d{1,3}(?:,\d{3})*(?:\.\d+)?)\)?',
                    r'税前利润|稅前利潤[\s：:]*\(?(-?\d{1,3}(?:,\d{3})*(?:\.\d+)?)\)?',
                ],
                'category': 'income_statement',
                'priority': 2
            },
            
            # ========== 现金流量表 (Cash Flow) ==========
            'operating_cash_flow': {
                'patterns': [
                    r'(?:Net\s+)?Cash\s+(?:from|used\s+in)\s+operating\s+activities[\s\n]*[^\d]*?\(?(-?\d{1,3}(?:,\d{3})*(?:\.\d+)?)\)?',
                    r'经营活动现金流量净额[\s：:]*\(?(-?\d{1,3}(?:,\d{3})*(?:\.\d+)?)\)?',
                ],
                'category': 'cash_flow',
                'priority': 2
            },
            
            'investing_cash_flow': {
                'patterns': [
                    r'(?:Net\s+)?Cash\s+(?:from|used\s+in)\s+investing\s+activities[\s\n]*[^\d]*?\(?(-?\d{1,3}(?:,\d{3})*(?:\.\d+)?)\)?',
                    r'投资活动现金流量净额[\s：:]*\(?(-?\d{1,3}(?:,\d{3})*(?:\.\d+)?)\)?',
                ],
                'category': 'cash_flow',
                'priority': 3
            },
            
            'financing_cash_flow': {
                'patterns': [
                    r'(?:Net\s+)?Cash\s+(?:from|used\s+in)\s+financing\s+activities[\s\n]*[^\d]*?\(?(-?\d{1,3}(?:,\d{3})*(?:\.\d+)?)\)?',
                    r'筹资活动现金流量净额[\s：:]*\(?(-?\d{1,3}(?:,\d{3})*(?:\.\d+)?)\)?',
                ],
                'category': 'cash_flow',
                'priority': 3
            }
        }
    
    def extract(self, pdf_path: str) -> Dict[str, Any]:
        """
        主提取方法 - 自动选择最佳策略
        
        Returns:
            Dict containing:
            - status: 'success' or 'failed'
            - data: 提取的财务数据
            - method: 使用的提取方法
            - confidence: 置信度评分
            - unit_multiplier: 单位乘数
        """
        result = {
            'status': 'failed',
            'data': {},
            'method': 'none',
            'confidence': 0,
            'unit_multiplier': 1,
            'filename': Path(pdf_path).name
        }
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                if len(pdf.pages) == 0:
                    result['error'] = 'Empty PDF'
                    return result
                
                # 1. 尝试表格提取（最准确）
                table_data = self._extract_from_tables(pdf)
                if table_data['success']:
                    result.update(table_data)
                    result['method'] = 'table'
                    
                # 2. 尝试正则提取（最快）
                regex_data = self._extract_with_regex(pdf)
                if regex_data['success']:
                    # 合并数据
                    for key, value in regex_data['data'].items():
                        if key not in result['data']:
                            result['data'][key] = value
                    if not table_data['success']:
                        result['method'] = 'regex'
                    result['status'] = 'success'
                
                # 3. 如果启用LLM且前两种方法效果不好
                if self.use_llm and len(result['data']) < 4:
                    llm_data = self._extract_with_llm(pdf)
                    if llm_data['success']:
                        # 合并LLM数据
                        for key, value in llm_data['data'].items():
                            if key not in result['data']:
                                result['data'][key] = value
                        result['method'] = 'mixed' if result['status'] == 'success' else 'llm'
                        result['status'] = 'success'
                
                # 4. 计算置信度
                result['confidence'] = self._calculate_confidence(result['data'])
                
                # 5. 银行特殊处理
                if self._is_bank_report(pdf):
                    bank_data = self._extract_bank_specific(pdf)
                    result['data'].update(bank_data)
                
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def _extract_from_tables(self, pdf) -> Dict:
        """表格提取方法"""
        data = {}
        success = False
        unit_multiplier = 1
        
        try:
            # 扫描前30页查找财务表格
            for i in range(min(30, len(pdf.pages))):
                page = pdf.pages[i]
                
                # 检测单位
                page_text = page.extract_text() or ""
                unit_multiplier = self._detect_unit(page_text)
                
                tables = page.extract_tables()
                if not tables:
                    continue
                
                for table in tables:
                    if not table or len(table) < 2:
                        continue
                    
                    # 转换为DataFrame
                    df = pd.DataFrame(table)
                    
                    # 查找财务数据
                    for metric_name, metric_info in self.financial_metrics.items():
                        if metric_name in data:
                            continue
                        
                        # 在表格中查找
                        value = self._find_in_table(df, metric_name, metric_info['patterns'])
                        if value is not None:
                            data[metric_name] = value * unit_multiplier
                            success = True
        except:
            pass
        
        return {
            'success': success,
            'data': data,
            'unit_multiplier': unit_multiplier
        }
    
    def _extract_with_regex(self, pdf) -> Dict:
        """正则表达式提取方法"""
        data = {}
        success = False
        
        # 提取文本
        full_text = ""
        for i in range(min(50, len(pdf.pages))):
            try:
                page_text = pdf.pages[i].extract_text()
                if page_text:
                    full_text += page_text + "\n"
            except:
                continue
        
        if not full_text:
            return {'success': False, 'data': {}}
        
        # 检测单位
        unit_multiplier = self._detect_unit(full_text)
        
        # 提取各指标
        for metric_name, metric_info in self.financial_metrics.items():
            for pattern in metric_info['patterns']:
                matches = re.findall(pattern, full_text, re.IGNORECASE | re.MULTILINE)
                if matches:
                    try:
                        # 处理匹配结果
                        value_str = matches[0].replace(',', '').replace('(', '').replace(')', '')
                        value = float(value_str)
                        
                        # 处理负数
                        if metric_name in ['net_profit', 'ebit'] and ('loss' in pattern.lower() or '亏损' in pattern):
                            value = -abs(value)
                        
                        data[metric_name] = value * unit_multiplier
                        success = True
                        break
                    except:
                        continue
        
        return {
            'success': success,
            'data': data,
            'unit_multiplier': unit_multiplier
        }
    
    def _extract_with_llm(self, pdf) -> Dict:
        """LLM提取方法"""
        if not self.llm_client:
            return {'success': False, 'data': {}}
        
        try:
            # 准备文本
            text_pages = []
            for i in range(min(20, len(pdf.pages))):
                page_text = pdf.pages[i].extract_text()
                if page_text:
                    text_pages.append(f"Page {i+1}:\n{page_text}")
            
            full_text = "\n\n".join(text_pages[:10])  # 限制长度
            
            # 构建prompt
            prompt = self._build_llm_prompt(list(self.financial_metrics.keys()))
            
            # 调用LLM
            response = self.llm_client.extract_financial_data(full_text, prompt)
            
            if response and 'data' in response:
                return {
                    'success': True,
                    'data': response['data'],
                    'unit_multiplier': response.get('unit_multiplier', 1)
                }
        except:
            pass
        
        return {'success': False, 'data': {}}
    
    def _detect_unit(self, text: str) -> int:
        """检测单位"""
        text_sample = text[:3000].lower()
        
        for pattern, multiplier in self.unit_patterns:
            if re.search(pattern, text_sample, re.IGNORECASE):
                return multiplier
        
        return 1
    
    def _find_in_table(self, df: pd.DataFrame, metric_name: str, patterns: List[str]) -> Optional[float]:
        """在表格中查找数值"""
        for idx, row in df.iterrows():
            row_text = ' '.join(str(cell) for cell in row if cell).lower()
            
            # 检查是否匹配任何模式
            for pattern in patterns:
                if re.search(pattern.lower(), row_text):
                    # 从右往左查找数字
                    for i in range(len(row)-1, -1, -1):
                        cell = str(row.iloc[i])
                        if cell and cell.strip():
                            try:
                                # 清理并转换
                                cleaned = cell.strip().replace(',', '').replace('$', '').replace('HK', '')
                                if '(' in cleaned and ')' in cleaned:
                                    cleaned = '-' + cleaned.replace('(', '').replace(')', '')
                                
                                value = float(cleaned)
                                return value
                            except:
                                continue
        
        return None
    
    def _is_bank_report(self, pdf) -> bool:
        """判断是否为银行报告"""
        # 简单判断逻辑
        first_page_text = pdf.pages[0].extract_text() or ""
        bank_keywords = ['bank', '银行', 'banking', 'deposit', 'loan', '存款', '贷款']
        
        return any(keyword in first_page_text.lower() for keyword in bank_keywords)
    
    def _extract_bank_specific(self, pdf) -> Dict:
        """提取银行特有指标"""
        data = {}
        
        full_text = ""
        for i in range(min(20, len(pdf.pages))):
            try:
                page_text = pdf.pages[i].extract_text()
                if page_text:
                    full_text += page_text + "\n"
            except:
                continue
        
        unit_multiplier = self._detect_unit(full_text)
        
        # 提取银行特有指标
        for metric_name, patterns in self.bank_specific_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, full_text, re.IGNORECASE | re.MULTILINE)
                if matches:
                    try:
                        value = float(matches[0].replace(',', ''))
                        data[metric_name] = value * unit_multiplier
                        break
                    except:
                        continue
        
        # 如果有银行特有收入但没有总收入，计算总收入
        if 'revenue' not in data:
            if 'net_interest_income' in data:
                revenue = data['net_interest_income']
                if 'fee_income' in data:
                    revenue += data['fee_income']
                data['revenue'] = revenue
            elif 'interest_income' in data:
                data['revenue'] = data['interest_income']
        
        return data
    
    def _calculate_confidence(self, data: Dict) -> float:
        """计算置信度评分"""
        if not data:
            return 0
        
        # 基础分数
        score = len(data) * 10
        
        # 关键指标加分
        key_metrics = ['total_assets', 'total_liabilities', 'revenue', 'net_profit']
        for metric in key_metrics:
            if metric in data:
                score += 15
        
        # 数据完整性加分
        if all(metric in data for metric in key_metrics):
            score += 20
        
        # 归一化到0-100
        return min(score, 100)
    
    def _build_llm_prompt(self, metrics: List[str]) -> str:
        """构建LLM提示词"""
        return f"""请从财务报告中提取以下财务指标数据：

{', '.join(metrics)}

要求：
1. 返回具体数值，不要包含货币符号
2. 注意识别单位（如千元、百万等）
3. 负数用负号表示
4. 如果是亏损，返回负数
5. 返回JSON格式

示例格式：
{{
    "total_assets": 1234567890,
    "net_profit": -1234567,
    "unit": "千元"
}}
"""


def test_extractor():
    """测试提取器"""
    extractor = MasterExtractor(use_llm=False)  # 先不使用LLM测试
    
    # 测试文件
    test_file = Path("data/raw_reports/Airstarbank_2019_Annual.pdf")
    
    if test_file.exists():
        print(f"测试文件: {test_file.name}")
        result = extractor.extract(str(test_file))
        
        print(f"\n状态: {result['status']}")
        print(f"方法: {result['method']}")
        print(f"置信度: {result['confidence']}%")
        print(f"单位乘数: {result['unit_multiplier']}")
        
        print("\n提取的数据:")
        for key, value in result['data'].items():
            print(f"  {key}: {value:,.0f}")
    else:
        print("测试文件不存在")


if __name__ == "__main__":
    test_extractor()