#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PDF财务数据提取模块
专用于从PDF文件中提取财务数据的原始信息
将正则表达式和数据提取逻辑集中在此模块
"""

import os
import re
import logging
import pandas as pd
import numpy as np
import PyPDF2
import pdfplumber
from datetime import datetime
import time
import json
import sys

# 设置日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PDFDataExtractor:
    """PDF财务数据提取器类"""
    
    def __init__(self, pdf_path=None):
        """初始化PDF财务数据提取器
        
        Args:
            pdf_path (str, optional): PDF文件路径
        """
        self.pdf_path = pdf_path
        self.extracted_data = {}
        self.raw_text = ""
        self.is_za_bank = False
        self.pdf_content_extracted = False
        self._pdf_pages = None
    
    def extract_pdf_content(self):
        """从PDF文件中提取全部内容
        
        Returns:
            bool: 是否成功提取内容
        """
        if not self.pdf_path or not os.path.exists(self.pdf_path):
            logger.error("PDF文件路径无效")
            return False
        
        # 如果已经提取过内容，避免重复处理    
        if self.pdf_content_extracted:
            logger.info("PDF内容已提取，跳过重复处理")
            return True
            
        start_time = time.time()
        logger.info(f"开始提取PDF内容...")
            
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                logger.info(f"PDF文件包含 {len(pdf.pages)} 页")
                
                # 缓存页面对象
                self._pdf_pages = pdf.pages
                
                # 检查是否为ZA Bank报告
                self._check_if_za_bank(pdf)
                
                # 提取所有页面的文本
                all_text = ""
                for page in pdf.pages:
                    page_text = page.extract_text() or ""
                    all_text += page_text + "\n\n"
                
                # 保存文本内容
                self.raw_text = all_text
                self.pdf_content_extracted = True
                
                # 如果是ZA Bank报告，使用专用方法
                if self.is_za_bank:
                    logger.info("使用ZA Bank专用方法提取财务数据")
                    self.extract_za_bank_data()
                else:
                    # 非ZA Bank报告使用通用方法
                    logger.info("使用通用方法提取财务数据")
                    self.extract_generic_financial_data(all_text)
                
                end_time = time.time()
                logger.info(f"PDF内容提取完成，耗时 {end_time - start_time:.2f} 秒")
                return True
                
        except Exception as e:
            logger.error(f"提取PDF内容失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _check_if_za_bank(self, pdf):
        """检查PDF是否为ZA Bank报告
        
        Args:
            pdf: pdfplumber PDF对象
        """
        for page in pdf.pages[:2]:  # 检查前两页
            text = page.extract_text() or ""
            if "ZA Bank" in text or "ZA BANK" in text:
                logger.info("检测到ZA Bank报告")
                self.is_za_bank = True
                return True
        return False
    
    def extract_za_bank_data(self):
        """提取ZA Bank报告中的所有财务数据"""
        # 确保已提取文本内容
        if not self.pdf_content_extracted:
            logger.warning("PDF内容尚未提取，无法进行ZA Bank数据提取")
            return
        
        logger.info("开始提取ZA Bank财务数据...")
        start_time = time.time()
        
        # 提取利润表
        income_statement = self.extract_za_bank_income_statement()
        if income_statement is not None:
            self.extracted_data['income_statement'] = income_statement
        
        # 提取资产负债表
        balance_sheet = self.extract_za_bank_balance_sheet()
        if balance_sheet is not None:
            self.extracted_data['balance_sheet'] = balance_sheet
            
        # 提取公司信息和报告日期
        company_info = self.extract_company_info()
        if company_info:
            self.extracted_data['company_info'] = company_info
        
        end_time = time.time()
        logger.info(f"ZA Bank财务数据提取完成，耗时 {end_time - start_time:.2f} 秒")
        
        # 保存提取的数据
        self.save_extracted_data()
        
        return self.extracted_data
    
    def extract_za_bank_income_statement(self):
        """提取ZA Bank报告中的利润表数据
        
        Returns:
            dict: 提取的利润表数据
        """
        if not self.is_za_bank:
            logger.warning("此报告不是ZA Bank格式，无法使用专用提取方法")
            return None
        
        start_time = time.time()
        logger.info("提取ZA Bank利润表...")
        
        try:
            # 关键字列表 - ZA Bank利润表特有项目
            income_keywords = [
                "Interest income",
                "Interest expense",
                "Net interest income",
                "Fee and commission income",
                "Fee and commission expense",
                "Net fee and commission income",
                "Net (loss)/gain from other financial instruments",
                "Other income",
                "Operating expenses",
                "Operating loss before impairment losses",
                "Credit impairment losses on loans and advances to customers",
                "Credit impairment losses on other financial assets",
                "Loss before income tax",
                "Income tax",
                "Net loss for the period",
                "Changes in the fair value of debt instruments",
                "Total comprehensive loss for the period"
            ]
            
            # 初始化结果集
            income_statement_data = []
            
            # 预编译正则表达式模式
            patterns = [
                re.compile(rf"({re.escape(item)})[^\n]*?(\(?\d[\d,]*\)?)\s+(\(?\d[\d,]*\)?)") for item in income_keywords
            ]
            patterns.extend([
                re.compile(rf"({re.escape(item)})[^\n]*?(\-?\d[\d,]*)\s+(\-?\d[\d,]*)") for item in income_keywords
            ])
            
            # 执行匹配
            successful_matches = set()
            for pattern in patterns:
                matches = pattern.findall(self.raw_text)
                for match in matches:
                    item = match[0]
                    if item not in successful_matches:
                        # 解析数值
                        current_value = self._parse_financial_value(match[1])
                        previous_value = self._parse_financial_value(match[2])
                        
                        # 计算变化
                        change = current_value - previous_value
                        change_percent = (change / previous_value * 100) if previous_value != 0 else 0
                        
                        # 添加到结果集
                        income_statement_data.append({
                            'Item': item,
                            '2024': current_value,  # 当前年
                            '2023': previous_value, # 前一年
                            'Change': change,
                            'Change%': change_percent
                        })
                        
                        # 记录成功匹配的项目
                        successful_matches.add(item)
                        logger.info(f"提取利润表项目: {item}, 当前值 {current_value}, 前一年值 {previous_value}")
            
            # 汇总提取结果
            if income_statement_data:
                income_statement = {
                    'data': income_statement_data,
                    'metadata': {
                        'current_year': '2024',
                        'previous_year': '2023',
                        'currency': 'HKD',
                        'unit': '千',
                        'extraction_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                }
                
                logger.info(f"成功提取ZA Bank利润表，共{len(income_statement_data)}个项目")
                end_time = time.time()
                logger.info(f"利润表提取完成，耗时 {end_time - start_time:.2f} 秒")
                return income_statement
            else:
                logger.warning("未能提取到任何利润表项目")
                return None
        
        except Exception as e:
            logger.error(f"提取ZA Bank利润表时出错: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def extract_za_bank_balance_sheet(self):
        """提取ZA Bank报告中的资产负债表数据
        
        Returns:
            dict: 提取的资产负债表数据
        """
        if not self.is_za_bank:
            logger.warning("此报告不是ZA Bank格式，无法使用专用提取方法")
            return None
        
        start_time = time.time()
        logger.info("提取ZA Bank资产负债表...")
        
        try:
            # 关键字列表 - ZA Bank资产负债表特有项目
            balance_keywords = [
                "ASSETS",
                "Cash and balances",
                "Balances with banks",
                "Investment securities measured at FVOCI",
                "Loans and advances to customers",
                "Property and equipment",
                "Right-of-use assets",
                "Intangible assets",
                "Deferred tax assets",
                "Other assets",
                "Total assets",
                "LIABILITIES",
                "Deposits from customers",
                "Lease liabilities",
                "Other liabilities",
                "Total liabilities",
                "EQUITY",
                "Share capital",
                "Reserves",
                "Accumulated losses",
                "Total equity",
                "Total equity and liabilities"
            ]
            
            # 初始化结果集
            balance_sheet_data = []
            
            # 预编译正则表达式模式
            patterns = [
                re.compile(rf"({re.escape(item)})[^\n]*?(\(?\d[\d,]*\)?)\s+(\(?\d[\d,]*\)?)") for item in balance_keywords
            ]
            patterns.extend([
                re.compile(rf"({re.escape(item)})[^\n]*?(\-?\d[\d,]*)\s+(\-?\d[\d,]*)") for item in balance_keywords
            ])
            patterns.extend([
                re.compile(rf"({re.escape(item)})[^\n]*?(\d[\d,]*)\s+(\d[\d,]*)") for item in balance_keywords
            ])
            
            # 执行匹配
            successful_matches = set()
            for pattern in patterns:
                matches = pattern.findall(self.raw_text)
                for match in matches:
                    item = match[0]
                    if item not in successful_matches:
                        # 解析数值
                        current_value = self._parse_financial_value(match[1])
                        previous_value = self._parse_financial_value(match[2])
                        
                        # 确定类别
                        category = self._determine_balance_sheet_category(item)
                        
                        # 计算变化
                        change = current_value - previous_value
                        change_percent = (change / previous_value * 100) if previous_value != 0 else 0
                        
                        # 添加到结果集
                        balance_sheet_data.append({
                            'Item': item,
                            'Category': category,
                            '2024': current_value,
                            '2023': previous_value,
                            'Change': change,
                            'Change%': change_percent
                        })
                        
                        # 记录成功匹配的项目
                        successful_matches.add(item)
                        logger.info(f"提取资产负债表项目: {item}, 类别: {category}, 当前值 {current_value}, 前一年值 {previous_value}")
            
            # 汇总提取结果
            if balance_sheet_data:
                balance_sheet = {
                    'data': balance_sheet_data,
                    'metadata': {
                        'current_year': '2024',
                        'previous_year': '2023',
                        'currency': 'HKD',
                        'unit': '千',
                        'extraction_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                }
                
                logger.info(f"成功提取ZA Bank资产负债表，共{len(balance_sheet_data)}个项目")
                end_time = time.time()
                logger.info(f"资产负债表提取完成，耗时 {end_time - start_time:.2f} 秒")
                return balance_sheet
            else:
                logger.warning("未能提取到任何资产负债表项目")
                return None
        
        except Exception as e:
            logger.error(f"提取ZA Bank资产负债表时出错: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _determine_balance_sheet_category(self, item):
        """确定资产负债表项目的类别
        
        Args:
            item (str): 项目名称
            
        Returns:
            str: 类别名称 ('Assets', 'Liabilities', 'Equity')
        """
        # 资产项目
        if item == "ASSETS" or "assets" in item.lower() or "Cash" in item or "Balances" in item or "Investment" in item or "Loans" in item or "Property" in item or "Right-of-use" in item or "Intangible" in item or "Deferred tax assets" in item or "Other assets" in item:
            return "Assets"
        
        # 负债项目
        elif item == "LIABILITIES" or "liabilities" in item.lower() or "Deposits" in item or "Lease liabilities" in item or "Other liabilities" in item:
            return "Liabilities"
        
        # 权益项目
        elif item == "EQUITY" or "equity" in item.lower() or "Share capital" in item or "Reserves" in item or "Accumulated" in item:
            return "Equity"
        
        # 未分类项目
        else:
            return "Uncategorized"
    
    def extract_company_info(self):
        """提取公司信息和报告日期
        
        Returns:
            dict: 公司信息
        """
        company_info = {}
        
        try:
            # 提取公司名称
            company_patterns = [
                re.compile(r'([\w\s]+)\s+Limited'),
                re.compile(r'(ZA\s+Bank\s+Limited)'),
                re.compile(r'([\w\s]+)\s+Corporation'),
                re.compile(r'([\w\s]+)\s+Inc\.'),
                re.compile(r'([\w\s]+)\s+Ltd\.'),
                re.compile(r'([\w\s]+)\s+Group')
            ]
            
            for pattern in company_patterns:
                match = pattern.search(self.raw_text)
                if match:
                    company_info['Company Name'] = match.group(1).strip()
                    break
            
            # 如果是ZA Bank但没有匹配到名称
            if self.is_za_bank and 'Company Name' not in company_info:
                company_info['Company Name'] = 'ZA Bank Limited'
                
            # 提取报告日期
            date_patterns = [
                re.compile(r'(?:as at|as of|dated|for the period ended|for the year ended|for the quarter ended)\s+(\d{1,2}\s+[a-zA-Z]+\s+\d{4})'),
                re.compile(r'(\d{1,2}\s+[a-zA-Z]+\s+\d{4})'),
                re.compile(r'(\d{4}-\d{2}-\d{2})'),
                re.compile(r'([a-zA-Z]+\s+\d{1,2},?\s+\d{4})')
            ]
            
            for pattern in date_patterns:
                match = pattern.search(self.raw_text)
                if match:
                    date_str = match.group(1).strip()
                    
                    # 标准化日期格式
                    try:
                        date_formats = ['%d %B %Y', '%B %d, %Y', '%B %d %Y', '%Y-%m-%d']
                        for fmt in date_formats:
                            try:
                                parsed_date = datetime.strptime(date_str, fmt)
                                company_info['Report Date'] = parsed_date.strftime('%Y-%m-%d')
                                break
                            except ValueError:
                                continue
                    except:
                        company_info['Report Date'] = date_str
                    
                    break
            
            # 如果没有匹配到日期，设置默认值
            if 'Report Date' not in company_info:
                company_info['Report Date'] = '2024-06-30'
            
            # 设置货币单位
            currency_patterns = [
                re.compile(r'(HK\$|HKD|USD|\$|EUR|CNY|RMB|JPY)'),
                re.compile(r'(Hong Kong dollars?)'),
                re.compile(r'(US dollars?)'),
                re.compile(r'(Chinese Yuan)'),
                re.compile(r'amounts? (?:are |is |in |expressed in )(HK\$|HKD|USD|\$|EUR|CNY|RMB|JPY)')
            ]
            
            currency = None
            for pattern in currency_patterns:
                match = pattern.search(self.raw_text)
                if match:
                    currency = match.group(1).strip()
                    break
            
            company_info['Currency'] = currency or 'HKD'
            
            # 对于ZA Bank，设置默认值
            if self.is_za_bank:
                company_info['Type'] = 'Virtual Bank'
                company_info['Region'] = 'Hong Kong'
            
            # 设置报告单位
            if 'thousands' in self.raw_text.lower() or 'HK$\'000' in self.raw_text:
                company_info['Unit'] = '千'
            elif 'millions' in self.raw_text.lower() or 'HK$\'m' in self.raw_text:
                company_info['Unit'] = '百万'
            else:
                company_info['Unit'] = '千'  # 默认单位
                
            return company_info
            
        except Exception as e:
            logger.error(f"提取公司信息时出错: {e}")
            return {'Company Name': 'Unknown', 'Report Date': '2024-06-30', 'Currency': 'HKD', 'Unit': '千'}
    
    def extract_generic_financial_data(self, text):
        """从文本中提取通用财务数据（非ZA Bank特定格式）
        
        Args:
            text (str): PDF文本内容
            
        Returns:
            dict: 提取的财务数据
        """
        logger.info("使用通用方法提取财务数据...")
        
        # 通用提取逻辑 - 简单实现
        # 实际实现应更复杂，这里仅作示例
        
        # 提取公司信息
        company_info = self.extract_company_info()
        if company_info:
            self.extracted_data['company_info'] = company_info
        
        # 保存提取的数据
        self.save_extracted_data()
        
        return self.extracted_data
    
    def _parse_financial_value(self, value_str):
        """解析财务数值，处理括号、逗号和负号
        
        Args:
            value_str (str): 财务数值字符串
            
        Returns:
            float: 解析后的数值
        """
        # 移除逗号和空格
        clean_str = value_str.replace(',', '').replace(' ', '')
        
        # 处理括号表示的负数
        if '(' in clean_str and ')' in clean_str:
            clean_str = clean_str.replace('(', '-').replace(')', '')
        
        # 将字符串转换为浮点数
        try:
            return float(clean_str)
        except ValueError:
            logger.warning(f"无法解析财务值: {value_str}, 使用0.0替代")
            return 0.0
    
    def save_extracted_data(self, output_path='./output'):
        """将提取的数据保存到文件
        
        Args:
            output_path (str): 输出目录路径
            
        Returns:
            bool: 是否成功保存
        """
        # 确保输出目录存在
        os.makedirs(output_path, exist_ok=True)
        
        try:
            # 生成输出文件名
            company_name = self.extracted_data.get('company_info', {}).get('Company Name', 'Unknown')
            report_date = self.extracted_data.get('company_info', {}).get('Report Date', datetime.now().strftime('%Y-%m-%d'))
            output_file = os.path.join(output_path, f"{company_name.replace(' ', '_')}_{report_date}_extracted_data.json")
            
            # 将数据转换为JSON并保存
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(self.extracted_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"数据已保存至: {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"保存数据时出错: {e}")
            return False
    
    def get_data_for_analysis(self):
        """获取用于分析的数据
        
        Returns:
            dict: 处理后的用于分析的数据
        """
        # 如果尚未提取数据，先进行提取
        if not self.pdf_content_extracted:
            self.extract_pdf_content()
        
        # 转换数据为分析所需的格式
        analysis_data = {}
        
        # 添加公司信息
        if 'company_info' in self.extracted_data:
            analysis_data['company_info'] = self.extracted_data['company_info']
        
        # 转换利润表为DataFrame格式
        if 'income_statement' in self.extracted_data:
            income_data = self.extracted_data['income_statement']['data']
            metadata = self.extracted_data['income_statement']['metadata']
            
            # 创建DataFrame
            income_df = pd.DataFrame(income_data)
            
            # 添加到分析数据
            analysis_data['income_statement'] = {
                'data': income_df,
                'metadata': metadata
            }
        
        # 转换资产负债表为DataFrame格式
        if 'balance_sheet' in self.extracted_data:
            balance_data = self.extracted_data['balance_sheet']['data']
            metadata = self.extracted_data['balance_sheet']['metadata']
            
            # 创建DataFrame
            balance_df = pd.DataFrame(balance_data)
            
            # 添加到分析数据
            analysis_data['balance_sheet'] = {
                'data': balance_df,
                'metadata': metadata
            }
        
        return analysis_data

# 如果单独运行此脚本
if __name__ == "__main__":
    # 使用示例
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
    else:
        pdf_path = "./data/1001925.pdf"  # 默认路径
    
    if os.path.exists(pdf_path):
        extractor = PDFDataExtractor(pdf_path)
        extractor.extract_pdf_content()
        data = extractor.get_data_for_analysis()
        
        # 输出提取结果概述
        print("\n==== 提取结果概述 ====")
        print(f"公司名称: {data.get('company_info', {}).get('Company Name', 'Unknown')}")
        print(f"报告日期: {data.get('company_info', {}).get('Report Date', 'Unknown')}")
        
        if 'income_statement' in data:
            print(f"\n利润表项目数: {len(data['income_statement']['data'])}")
        
        if 'balance_sheet' in data:
            print(f"资产负债表项目数: {len(data['balance_sheet']['data'])}")
    else:
        print(f"文件不存在: {pdf_path}") 