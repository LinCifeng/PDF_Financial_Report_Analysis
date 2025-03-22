#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
财务数据分析模块
专用于对提取的财务数据进行定性分析
将所有分析和报告生成逻辑集中在此模块
"""

import os
import sys
import logging
import pandas as pd
import numpy as np
from datetime import datetime
import time
import json
import matplotlib.pyplot as plt

# 设置日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FinancialAnalyzer:
    """财务数据分析器类"""
    
    def __init__(self, data=None):
        """初始化财务数据分析器
        
        Args:
            data (dict, optional): 提取的财务数据
        """
        self.data = data
        self.financial_ratios = {}
        self.financial_trends = {}
        self.analysis_results = {}
        
    def load_data(self, json_file):
        """从JSON文件加载提取的财务数据
        
        Args:
            json_file (str): JSON文件路径
            
        Returns:
            bool: 是否成功加载
        """
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
            
            # 转换JSON数据中的列表为DataFrame格式
            if 'income_statement' in self.data:
                income_data = self.data['income_statement']['data']
                self.data['income_statement']['data'] = pd.DataFrame(income_data)
            
            if 'balance_sheet' in self.data:
                balance_data = self.data['balance_sheet']['data']
                self.data['balance_sheet']['data'] = pd.DataFrame(balance_data)
                
            logger.info(f"已从 {json_file} 加载财务数据")
            return True
            
        except Exception as e:
            logger.error(f"加载数据时出错: {e}")
            return False
    
    def set_data(self, data):
        """设置财务数据
        
        Args:
            data (dict): 财务数据
        """
        self.data = data
    
    def calculate_financial_ratios(self):
        """计算各种财务比率和指标
        
        Returns:
            dict: 计算的财务比率
        """
        if not self.data:
            logger.error("未加载数据，无法计算财务比率")
            return None
        
        start_time = time.time()
        logger.info("计算财务比率...")
        
        # 初始化比率字典
        ratios = {}
        
        # 获取公司信息
        company_info = self.data.get('company_info', {})
        
        # 获取年份信息
        current_year = '2024'  # 默认值
        previous_year = '2023'  # 默认值
        
        # 从利润表或资产负债表元数据获取年份信息
        if 'income_statement' in self.data and 'metadata' in self.data['income_statement']:
            metadata = self.data['income_statement']['metadata']
            current_year = metadata.get('current_year', current_year)
            previous_year = metadata.get('previous_year', previous_year)
        
        # 初始化比率字典，包含当前年度和上一年度
        ratios = {
            current_year: {},
            previous_year: {}
        }
        
        # 如果有利润表数据
        if 'income_statement' in self.data and 'data' in self.data['income_statement']:
            income_df = self.data['income_statement']['data']
            
            # 提取关键财务项目并计算比率
            for year in [current_year, previous_year]:
                try:
                    # 利息收入
                    interest_income = self._get_item_value(income_df, 'Interest income', year)
                    ratios[year]['Interest Income'] = interest_income
                    
                    # 利息支出
                    interest_expense = self._get_item_value(income_df, 'Interest expense', year)
                    ratios[year]['Interest Expense'] = interest_expense
                    
                    # 净利息收入
                    net_interest = self._get_item_value(income_df, 'Net interest income', year)
                    if net_interest == 0 and interest_income != 0 and interest_expense != 0:
                        net_interest = interest_income - interest_expense
                    ratios[year]['Net Interest Income'] = net_interest
                    
                    # 手续费收入
                    fee_income = self._get_item_value(income_df, 'Fee and commission income', year)
                    ratios[year]['Fee Income'] = fee_income
                    
                    # 手续费支出
                    fee_expense = self._get_item_value(income_df, 'Fee and commission expense', year)
                    ratios[year]['Fee Expense'] = fee_expense
                    
                    # 净手续费收入
                    net_fee = self._get_item_value(income_df, 'Net fee and commission income', year)
                    if net_fee == 0 and fee_income != 0 and fee_expense != 0:
                        net_fee = fee_income - fee_expense
                    ratios[year]['Net Fee Income'] = net_fee
                    
                    # 总收入（净利息 + 净手续费）
                    total_income = net_interest + net_fee
                    ratios[year]['Total Income'] = total_income
                    
                    # 运营支出
                    operating_expenses = self._get_item_value(income_df, 'Operating expenses', year)
                    ratios[year]['Operating Expenses'] = operating_expenses
                    
                    # 信贷减值损失
                    credit_impairment = self._get_item_value(income_df, 'Credit impairment losses', year)
                    if credit_impairment == 0:
                        # 尝试查找其他可能的减值损失项目
                        credit_impairment += self._get_item_value(income_df, 'Credit impairment losses on loans and advances to customers', year)
                        credit_impairment += self._get_item_value(income_df, 'Credit impairment losses on other financial assets', year)
                    ratios[year]['Credit Impairment Losses'] = credit_impairment
                    
                    # 税前亏损
                    loss_before_tax = self._get_item_value(income_df, 'Loss before income tax', year)
                    ratios[year]['Loss Before Tax'] = loss_before_tax
                    
                    # 净亏损
                    net_loss = self._get_item_value(income_df, 'Net loss for the period', year)
                    ratios[year]['Net Loss'] = net_loss
                    
                except Exception as e:
                    logger.warning(f"计算利润表比率时出错: {e}")
        
        # 如果有资产负债表数据
        if 'balance_sheet' in self.data and 'data' in self.data['balance_sheet']:
            balance_df = self.data['balance_sheet']['data']
            
            # 提取关键财务项目并计算比率
            for year in [current_year, previous_year]:
                try:
                    # 总资产
                    total_assets = self._get_item_value(balance_df, 'Total assets', year)
                    ratios[year]['Total Assets'] = total_assets
                    
                    # 总负债
                    total_liabilities = self._get_item_value(balance_df, 'Total liabilities', year)
                    ratios[year]['Total Liabilities'] = total_liabilities
                    
                    # 总权益
                    total_equity = self._get_item_value(balance_df, 'Total equity', year)
                    # 如果没有直接找到，尝试计算
                    if total_equity == 0 and total_assets != 0 and total_liabilities != 0:
                        total_equity = total_assets - total_liabilities
                    ratios[year]['Total Equity'] = total_equity
                    
                    # 客户存款
                    deposits = self._get_item_value(balance_df, 'Deposits from customers', year)
                    ratios[year]['Customer Deposits'] = deposits
                    
                    # 贷款和垫款
                    loans = self._get_item_value(balance_df, 'Loans and advances to customers', year)
                    ratios[year]['Loans and Advances'] = loans
                    
                    # 计算资产负债率（总负债/总资产）
                    if total_assets != 0:
                        debt_to_assets = (total_liabilities / total_assets) * 100
                        ratios[year]['Debt-to-Assets Ratio'] = debt_to_assets
                    
                    # 计算负债权益比（总负债/总权益）
                    if total_equity != 0:
                        debt_to_equity = total_liabilities / total_equity
                        ratios[year]['Debt-to-Equity Ratio'] = debt_to_equity
                    
                    # 计算贷存比（贷款/存款）
                    if deposits != 0:
                        loan_to_deposit = (loans / deposits) * 100
                        ratios[year]['Loan-to-Deposit Ratio'] = loan_to_deposit
                    
                except Exception as e:
                    logger.warning(f"计算资产负债表比率时出错: {e}")
        
        # 计算综合比率
        for year in [current_year, previous_year]:
            try:
                # 净利润/总资产 = ROA
                if ratios[year].get('Total Assets', 0) != 0 and 'Net Loss' in ratios[year]:
                    ratios[year]['ROA'] = (ratios[year]['Net Loss'] / ratios[year]['Total Assets']) * 100
                
                # 净利润/总权益 = ROE
                if ratios[year].get('Total Equity', 0) != 0 and 'Net Loss' in ratios[year]:
                    ratios[year]['ROE'] = (ratios[year]['Net Loss'] / ratios[year]['Total Equity']) * 100
                
            except Exception as e:
                logger.warning(f"计算综合比率时出错: {e}")
        
        # 计算同比变化
        ratio_changes = {}
        for ratio_name in ratios[current_year].keys():
            if ratio_name in ratios[previous_year] and ratios[previous_year][ratio_name] != 0:
                # 计算绝对变化和百分比变化
                current_value = ratios[current_year][ratio_name]
                previous_value = ratios[previous_year][ratio_name]
                
                change = current_value - previous_value
                change_pct = (change / abs(previous_value)) * 100
                
                ratio_changes[ratio_name] = {
                    'Current': current_value,
                    'Previous': previous_value,
                    'Change': change,
                    'Change%': change_pct
                }
        
        # 保存财务比率到对象属性
        self.financial_ratios = {
            'current_year': current_year,
            'previous_year': previous_year,
            'ratios': ratios,
            'ratio_changes': ratio_changes
        }
        
        end_time = time.time()
        logger.info(f"财务比率计算完成，耗时 {end_time - start_time:.2f} 秒")
        
        return self.financial_ratios
    
    def _get_item_value(self, df, item_name, column_name, default=0):
        """安全地从DataFrame中获取某个项目的值
        
        Args:
            df (DataFrame): 数据框
            item_name (str): 项目名称
            column_name (str): 列名
            default (float): 默认值（如果项目不存在）
            
        Returns:
            float: 项目值
        """
        if df is None or df.empty:
            return default
        
        try:
            # 尝试精确匹配
            item_row = df[df['Item'] == item_name]
            if not item_row.empty and column_name in df.columns:
                value = item_row.iloc[0][column_name]
                return float(value) if pd.notna(value) else default
            
            # 如果精确匹配失败，尝试模糊匹配
            for idx, row in df.iterrows():
                if item_name.lower() in row['Item'].lower():
                    if column_name in df.columns:
                        value = row[column_name]
                        return float(value) if pd.notna(value) else default
            
            # 如果所有尝试都失败，返回默认值
            return default
            
        except Exception as e:
            logger.warning(f"获取项目 {item_name} 的 {column_name} 值时出错: {e}")
            return default
    
    def analyze_financial_trends(self):
        """分析财务数据趋势和健康状况
        
        Returns:
            dict: 趋势分析结果
        """
        if not self.financial_ratios:
            logger.warning("财务比率尚未计算，先计算财务比率")
            self.calculate_financial_ratios()
        
        start_time = time.time()
        logger.info("分析财务趋势和健康状况...")
        
        trends = {
            'growth': [],
            'profitability': [],
            'efficiency': [],
            'financial_health': [],
            'risk_factors': [],
            'strength_factors': []
        }
        
        ratio_changes = self.financial_ratios.get('ratio_changes', {})
        current_year = self.financial_ratios.get('current_year')
        previous_year = self.financial_ratios.get('previous_year')
        ratios = self.financial_ratios.get('ratios', {})
        
        # 分析资产增长情况
        if 'Total Assets' in ratio_changes:
            asset_change = ratio_changes['Total Assets']['Change%']
            if asset_change > 10:
                trends['growth'].append(f"总资产增长强劲，同比增长{asset_change:.2f}%")
            elif asset_change > 0:
                trends['growth'].append(f"总资产稳定增长，同比增长{asset_change:.2f}%")
            elif asset_change > -10:
                trends['growth'].append(f"总资产略有下降，同比下降{abs(asset_change):.2f}%")
            else:
                trends['growth'].append(f"总资产大幅减少，同比下降{abs(asset_change):.2f}%")
        
        # 分析贷款增长情况
        if 'Loans and Advances' in ratio_changes:
            loan_change = ratio_changes['Loans and Advances']['Change%']
            if loan_change > 15:
                trends['growth'].append(f"贷款业务增长强劲，同比增长{loan_change:.2f}%")
                trends['risk_factors'].append("贷款快速增长可能带来信贷质量问题，需关注风险控制")
            elif loan_change > 0:
                trends['growth'].append(f"贷款业务稳定增长，同比增长{loan_change:.2f}%")
            else:
                trends['growth'].append(f"贷款业务收缩，同比下降{abs(loan_change):.2f}%")
        
        # 分析存款增长情况
        if 'Customer Deposits' in ratio_changes:
            deposit_change = ratio_changes['Customer Deposits']['Change%']
            if deposit_change > 15:
                trends['growth'].append(f"客户存款增长强劲，同比增长{deposit_change:.2f}%")
                trends['strength_factors'].append("存款基础稳固，资金来源稳定")
            elif deposit_change > 0:
                trends['growth'].append(f"客户存款稳定增长，同比增长{deposit_change:.2f}%")
            else:
                trends['growth'].append(f"客户存款下降，同比减少{abs(deposit_change):.2f}%")
                trends['risk_factors'].append("存款减少可能影响资金稳定性")
        
        # 保存趋势分析结果
        self.financial_trends = trends
        
        end_time = time.time()
        logger.info(f"财务趋势分析完成，耗时 {end_time - start_time:.2f} 秒")
        
        return trends 