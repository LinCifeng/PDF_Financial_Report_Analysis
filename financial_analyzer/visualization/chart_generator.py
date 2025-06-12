#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
图表生成模块
专用于生成财务数据可视化图表
"""

import os
import logging
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
import matplotlib.font_manager as fm

# 设置日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ChartGenerator:
    """图表生成器类"""
    
    def __init__(self, analyzer=None):
        """初始化图表生成器
        
        Args:
            analyzer: 财务分析器对象
        """
        self.analyzer = analyzer
        
        # 字体设置在各个方法中根据需要进行配置
    
    def set_analyzer(self, analyzer):
        """设置财务分析器
        
        Args:
            analyzer: 财务分析器对象
        """
        self.analyzer = analyzer
    
    def ensure_font_support(self):
        """确保支持中文字体
        
        尝试查找系统中可用的中文字体并设置
        """
        # 检查常见中文字体是否可用
        chinese_fonts = ['Source Han Sans SC', 'SimHei', 'Microsoft YaHei', 
                         'STHeiti', 'Arial Unicode MS', 'PingFang SC', 
                         'Hiragino Sans GB', 'Noto Sans CJK SC']
        
        # 获取系统中所有可用字体
        system_fonts = set([f.name for f in fm.fontManager.ttflist])
        
        # 查找第一个可用的中文字体
        for font in chinese_fonts:
            if font in system_fonts:
                logger.info(f"使用中文字体: {font}")
                plt.rcParams['font.sans-serif'] = [font] + chinese_fonts
                plt.rcParams['axes.unicode_minus'] = False
                return font
        
        # 如果没有找到合适的中文字体，使用系统默认字体并记录警告
        logger.warning("未找到合适的中文字体，可能无法正确显示中文")
        return None
    
    def generate_multi_year_asset_trends(self, data_dir='./data', output_path='./output'):
        """生成多年资产趋势分析图表
        
        Args:
            data_dir (str): 数据目录路径
            output_path (str): 输出目录路径
            
        Returns:
            dict: 包含图表文件路径列表和合并JSON文件路径
        """
        import json
        from datetime import datetime
        from financial_analyzer.data_extraction.pdf_extractor import PDFDataExtractor
        
        # 确保输出目录存在
        os.makedirs(output_path, exist_ok=True)
        
        # 设置英文字体
        plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans', 'Liberation Sans']
        plt.rcParams['axes.unicode_minus'] = False
        
        years = ['2020', '2021', '2022', '2023', '2024']
        asset_data = {}
        merged_data = {
            'company_name': 'ZA Bank Limited',
            'analysis_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'data_period': '2020-2024',
            'yearly_data': {},
            'summary': {}
        }
        
        # 提取所有年份的数据
        logger.info("Extracting ZA Bank financial data for 2020-2024...")
        
        for year in years:
            pdf_file = os.path.join(data_dir, f'ZABank{year}.pdf')
            if os.path.exists(pdf_file):
                logger.info(f"Extracting {year} data...")
                try:
                    # 创建提取器并提取数据，但不保存单独的JSON文件
                    
                    extractor = PDFDataExtractor(pdf_file)
                    
                    # 临时重写save_extracted_data方法来禁用保存
                    original_save_method = extractor.save_extracted_data
                    extractor.save_extracted_data = lambda *args, **kwargs: True
                    
                    extractor.extract_pdf_content()
                    
                    # 恢复原始方法
                    extractor.save_extracted_data = original_save_method
                    
                    if extractor.is_za_bank and 'balance_sheet' in extractor.extracted_data:
                        balance_data = extractor.extracted_data['balance_sheet']['data']
                        processed_data = self._process_balance_sheet_data(balance_data, year)
                        asset_data[year] = processed_data
                        
                        # 添加到合并数据中
                        merged_data['yearly_data'][year] = {
                            'balance_sheet': processed_data,
                            'income_statement': extractor.extracted_data.get('income_statement', {}),
                            'extraction_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        }
                        
                        logger.info(f"Successfully extracted {year} data")
                    else:
                        logger.warning(f"Failed to extract balance sheet data for {year}")
                        
                except Exception as e:
                    logger.error(f"Error extracting {year} data: {e}")
            else:
                logger.warning(f"PDF file not found for {year}: {pdf_file}")
        
        if not asset_data:
            logger.error("No asset data available")
            return {'chart_files': [], 'json_file': None}
        
        # 计算汇总统计
        merged_data['summary'] = self._calculate_summary_statistics(asset_data)
        
        # 保存合并的JSON文件
        json_filename = f"ZA_Bank_Multi_Year_Analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        json_filepath = os.path.join(output_path, json_filename)
        
        try:
            with open(json_filepath, 'w', encoding='utf-8') as f:
                json.dump(merged_data, f, indent=2, ensure_ascii=False)
            logger.info(f"Merged data saved to: {json_filepath}")
        except Exception as e:
            logger.error(f"Failed to save merged JSON: {e}")
            json_filepath = None
        
        # 生成图表
        chart_files = []
        
        # 1. 总资产变化趋势图
        chart_file = self._create_total_assets_trend_en(asset_data, output_path)
        if chart_file:
            chart_files.append(chart_file)
        
        # 2. 资产结构变化图
        chart_file = self._create_asset_structure_chart_en(asset_data, output_path)
        if chart_file:
            chart_files.append(chart_file)
        
        # 3. 资产负债权益对比图
        chart_file = self._create_balance_comparison_chart_en(asset_data, output_path)
        if chart_file:
            chart_files.append(chart_file)
        
        # 4. 核心业务指标变化图
        chart_file = self._create_core_metrics_chart_en(asset_data, output_path)
        if chart_file:
            chart_files.append(chart_file)
        
        return {
            'chart_files': chart_files,
            'json_file': json_filepath,
            'data_summary': merged_data['summary']
        }
    
    def _process_balance_sheet_data(self, balance_data, year):
        """处理资产负债表数据"""
        processed_data = {}
        
        # 关键资产项目映射
        key_assets = {
            'Total assets': 'Total Assets',
            'Cash and balances': 'Cash and Bank Balances',
            'Investment securities measured at FVOCI': 'Investment Securities',
            'Loans and advances to customers': 'Customer Loans and Advances',
            'Deposits from customers': 'Customer Deposits',
            'Total liabilities': 'Total Liabilities',
            'Total equity': 'Total Equity'
        }
        
        for item_data in balance_data:
            item_name = item_data.get('Item', '')
            if item_name in key_assets:
                # 根据年份获取对应的数值
                if year == '2024':
                    value = item_data.get('2024', 0)
                elif year == '2023':
                    value = item_data.get('2023', 0)
                else:
                    # 对于2020-2022年，可能需要从不同字段获取
                    value = item_data.get(year, item_data.get('2024', 0))
                
                processed_data[key_assets[item_name]] = float(value) if value else 0
        
        return processed_data
    
    def _calculate_summary_statistics(self, asset_data):
        """计算汇总统计数据"""
        summary = {
            'total_years': len(asset_data),
            'year_range': f"{min(asset_data.keys())}-{max(asset_data.keys())}",
            'growth_analysis': {},
            'key_metrics': {}
        }
        
        # 计算增长分析
        years = sorted(asset_data.keys())
        if len(years) >= 2:
            first_year = years[0]
            last_year = years[-1]
            
            for metric in ['Total Assets', 'Total Liabilities', 'Total Equity', 'Customer Deposits', 'Customer Loans and Advances']:
                if metric in asset_data[first_year] and metric in asset_data[last_year]:
                    start_value = asset_data[first_year][metric]
                    end_value = asset_data[last_year][metric]
                    
                    if start_value > 0:
                        growth_rate = ((end_value - start_value) / start_value) * 100
                        summary['growth_analysis'][metric] = {
                            'start_value': start_value,
                            'end_value': end_value,
                            'growth_rate_percent': round(growth_rate, 2),
                            'absolute_change': end_value - start_value
                        }
        
        # 计算关键指标
        for year in years:
            data = asset_data[year]
            total_assets = data.get('Total Assets', 0)
            total_liabilities = data.get('Total Liabilities', 0)
            total_equity = data.get('Total Equity', 0)
            
            if total_assets > 0:
                summary['key_metrics'][year] = {
                    'asset_liability_ratio': round((total_liabilities / total_assets) * 100, 2),
                    'equity_ratio': round((total_equity / total_assets) * 100, 2),
                    'total_assets_billion_hkd': round(total_assets / 1000000, 2)
                }
        
        return summary
    
    def _create_total_assets_trend_en(self, asset_data, output_path):
        """创建总资产变化趋势图（英文版）"""
        plt.figure(figsize=(12, 8))
        
        years = []
        total_assets = []
        
        for year in sorted(asset_data.keys()):
            if 'Total Assets' in asset_data[year]:
                years.append(year)
                total_assets.append(asset_data[year]['Total Assets'] / 1000000)  # 转换为百万港元
        
        if len(years) >= 2:
            plt.plot(years, total_assets, marker='o', linewidth=3, markersize=8, color='#2E86AB')
            plt.fill_between(years, total_assets, alpha=0.3, color='#2E86AB')
            
            # 添加数值标签
            for i, (year, value) in enumerate(zip(years, total_assets)):
                plt.annotate(f'{value:.1f}B', (year, value), 
                           textcoords="offset points", xytext=(0,10), ha='center',
                           fontsize=10, fontweight='bold')
            
            plt.title('ZA Bank Total Assets Trend (2020-2024)', fontsize=16, fontweight='bold', pad=20)
            plt.xlabel('Year', fontsize=12)
            plt.ylabel('Total Assets (Billion HKD)', fontsize=12)
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            
            # 保存图表
            chart_file = os.path.join(output_path, 'ZA_Bank_Total_Assets_Trend.png')
            plt.savefig(chart_file, dpi=300, bbox_inches='tight')
            plt.close()
            logger.info(f"Total assets trend chart saved: {chart_file}")
            return chart_file
        else:
            logger.warning("Insufficient data to generate total assets trend chart")
            return None
    
    def _create_asset_structure_chart_en(self, asset_data, output_path):
        """创建资产结构变化图（英文版）"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
        
        # 准备数据
        asset_categories = ['Cash and Bank Balances', 'Investment Securities', 'Customer Loans and Advances']
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1']
        
        # 左图：堆叠面积图显示资产结构变化
        years_data = []
        asset_values = {cat: [] for cat in asset_categories}
        
        for year in sorted(asset_data.keys()):
            years_data.append(year)
            for cat in asset_categories:
                value = asset_data[year].get(cat, 0) / 1000000  # 转换为百万港元
                asset_values[cat].append(value)
        
        if len(years_data) >= 2:
            # 堆叠面积图
            ax1.stackplot(years_data, *[asset_values[cat] for cat in asset_categories], 
                         labels=asset_categories, colors=colors, alpha=0.8)
            ax1.set_title('Asset Structure Evolution', fontsize=14, fontweight='bold')
            ax1.set_xlabel('Year', fontsize=12)
            ax1.set_ylabel('Asset Scale (Billion HKD)', fontsize=12)
            ax1.legend(loc='upper left')
            ax1.grid(True, alpha=0.3)
            
            # 右图：最新年份资产结构饼图
            if years_data:
                latest_year = years_data[-1]
                latest_values = [asset_values[cat][-1] for cat in asset_categories]
                
                # 过滤掉零值
                non_zero_cats = []
                non_zero_values = []
                for cat, val in zip(asset_categories, latest_values):
                    if val > 0:
                        non_zero_cats.append(cat)
                        non_zero_values.append(val)
                
                if non_zero_values:
                    wedges, texts, autotexts = ax2.pie(non_zero_values, labels=non_zero_cats, 
                                                      colors=colors[:len(non_zero_values)],
                                                      autopct='%1.1f%%', startangle=90)
                    ax2.set_title(f'{latest_year} Asset Structure', fontsize=14, fontweight='bold')
                    
                    # 美化饼图文字
                    for autotext in autotexts:
                        autotext.set_color('white')
                        autotext.set_fontweight('bold')
        
        plt.tight_layout()
        chart_file = os.path.join(output_path, 'ZA_Bank_Asset_Structure_Evolution.png')
        plt.savefig(chart_file, dpi=300, bbox_inches='tight')
        plt.close()
        logger.info(f"Asset structure chart saved: {chart_file}")
        return chart_file
    
    def _create_balance_comparison_chart_en(self, asset_data, output_path):
        """创建资产负债权益对比图（英文版）"""
        plt.figure(figsize=(14, 8))
        
        categories = ['Total Assets', 'Total Liabilities', 'Total Equity']
        colors = ['#2E86AB', '#F18F01', '#C73E1D']
        
        years_data = []
        values_data = {cat: [] for cat in categories}
        
        for year in sorted(asset_data.keys()):
            years_data.append(year)
            for cat in categories:
                value = asset_data[year].get(cat, 0) / 1000000  # 转换为百万港元
                values_data[cat].append(value)
        
        if len(years_data) >= 2:
            x = np.arange(len(years_data))
            width = 0.25
            
            for i, (cat, color) in enumerate(zip(categories, colors)):
                plt.bar(x + i * width, values_data[cat], width, 
                       label=cat, color=color, alpha=0.8)
                
                # 添加数值标签
                for j, value in enumerate(values_data[cat]):
                    plt.text(x[j] + i * width, value + max(values_data[cat]) * 0.01, 
                           f'{value:.1f}B', ha='center', va='bottom', 
                           fontsize=9, fontweight='bold')
            
            plt.title('ZA Bank Assets, Liabilities & Equity Comparison (2020-2024)', fontsize=16, fontweight='bold', pad=20)
            plt.xlabel('Year', fontsize=12)
            plt.ylabel('Amount (Billion HKD)', fontsize=12)
            plt.xticks(x + width, years_data)
            plt.legend()
            plt.grid(True, alpha=0.3, axis='y')
            plt.tight_layout()
            
            chart_file = os.path.join(output_path, 'ZA_Bank_Balance_Comparison.png')
            plt.savefig(chart_file, dpi=300, bbox_inches='tight')
            plt.close()
            logger.info(f"Balance comparison chart saved: {chart_file}")
            return chart_file
        else:
            logger.warning("Insufficient data to generate balance comparison chart")
            return None
    
    def _create_core_metrics_chart_en(self, asset_data, output_path):
        """创建核心业务指标变化图（英文版）"""
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        
        # 准备数据
        years_data = []
        metrics_data = {
            'Customer Deposits': [],
            'Customer Loans and Advances': [],
            'Asset-Liability Ratio': [],
            'Equity Ratio': []
        }
        
        for year in sorted(asset_data.keys()):
            years_data.append(year)
            data = asset_data[year]
            
            # 客户存款和贷款（百万港元）
            metrics_data['Customer Deposits'].append(data.get('Customer Deposits', 0) / 1000000)
            metrics_data['Customer Loans and Advances'].append(data.get('Customer Loans and Advances', 0) / 1000000)
            
            # 计算比率
            total_assets = data.get('Total Assets', 0)
            total_liabilities = data.get('Total Liabilities', 0)
            total_equity = data.get('Total Equity', 0)
            
            if total_assets > 0:
                asset_liability_ratio = (total_liabilities / total_assets) * 100
                equity_ratio = (total_equity / total_assets) * 100
            else:
                asset_liability_ratio = 0
                equity_ratio = 0
            
            metrics_data['Asset-Liability Ratio'].append(asset_liability_ratio)
            metrics_data['Equity Ratio'].append(equity_ratio)
        
        if len(years_data) >= 2:
            # 1. 客户存款变化
            ax1.plot(years_data, metrics_data['Customer Deposits'], marker='o', linewidth=2, 
                    color='#4ECDC4', markersize=6)
            ax1.set_title('Customer Deposits Trend', fontweight='bold')
            ax1.set_ylabel('Billion HKD')
            ax1.grid(True, alpha=0.3)
            
            # 2. 客户贷款变化
            ax2.plot(years_data, metrics_data['Customer Loans and Advances'], marker='s', linewidth=2, 
                    color='#FF6B6B', markersize=6)
            ax2.set_title('Customer Loans & Advances Trend', fontweight='bold')
            ax2.set_ylabel('Billion HKD')
            ax2.grid(True, alpha=0.3)
            
            # 3. 资产负债率
            ax3.bar(years_data, metrics_data['Asset-Liability Ratio'], color='#F18F01', alpha=0.7)
            ax3.set_title('Asset-Liability Ratio Trend', fontweight='bold')
            ax3.set_ylabel('Percentage (%)')
            ax3.grid(True, alpha=0.3, axis='y')
            
            # 4. 权益比率
            ax4.bar(years_data, metrics_data['Equity Ratio'], color='#C73E1D', alpha=0.7)
            ax4.set_title('Equity Ratio Trend', fontweight='bold')
            ax4.set_ylabel('Percentage (%)')
            ax4.grid(True, alpha=0.3, axis='y')
            
            # 设置x轴标签
            for ax in [ax1, ax2, ax3, ax4]:
                ax.set_xlabel('Year')
        
        plt.suptitle('ZA Bank Core Business Metrics (2020-2024)', fontsize=16, fontweight='bold')
        plt.tight_layout()
        
        chart_file = os.path.join(output_path, 'ZA_Bank_Core_Metrics.png')
        plt.savefig(chart_file, dpi=300, bbox_inches='tight')
        plt.close()
        logger.info(f"Core metrics chart saved: {chart_file}")
        return chart_file

    def generate_income_structure_chart(self, output_path='./output'):
        """生成收入结构对比图
        
        Args:
            output_path (str): 输出目录路径
            
        Returns:
            str: 生成的图表文件路径
        """
        # 确保字体支持
        self.ensure_font_support()
        
        if not self.analyzer or not self.analyzer.financial_ratios:
            logger.warning("未设置分析器或财务比率尚未计算，无法生成图表")
            return None
        
        # 确保输出目录存在
        os.makedirs(output_path, exist_ok=True)
        
        # 获取公司信息
        company_info = self.analyzer.data.get('company_info', {})
        company_name = company_info.get('Company Name', '金融机构')
        
        # 获取年份信息
        current_year = self.analyzer.financial_ratios.get('current_year', '2024')
        previous_year = self.analyzer.financial_ratios.get('previous_year', '2023')
        
        # 获取财务比率数据
        ratios = self.analyzer.financial_ratios.get('ratios', {})
        
        try:
            # 检查是否存在必要的收入数据
            required_keys = ['Interest Income', 'Fee Income', 'Total Income']
            for year in [current_year, previous_year]:
                if year not in ratios:
                    logger.warning(f"缺少{year}年的财务比率数据")
                    return None
                    
                for key in required_keys:
                    if key not in ratios[year]:
                        logger.warning(f"缺少{year}年的{key}数据")
                        return None
            
            # 准备数据
            income_types = ['利息收入', '手续费收入', '其他收入']
            
            # 计算数值
            def get_income_values(year):
                interest = float(ratios[year].get('Interest Income', 0))
                fee = float(ratios[year].get('Fee Income', 0))
                total = float(ratios[year].get('Total Income', 0))
                other = total - interest - fee
                # 确保不是负数
                other = max(0, other)
                return [interest, fee, other]
            
            current_income = get_income_values(current_year)
            previous_income = get_income_values(previous_year)
            
            # 创建柱状图
            fig, ax = plt.subplots(figsize=(12, 7))
            x = np.arange(len(income_types))
            width = 0.35
            
            current_bars = ax.bar(x - width/2, current_income, width, label=f'{current_year}年', color='#3274A1')
            previous_bars = ax.bar(x + width/2, previous_income, width, label=f'{previous_year}年', color='#E1812C')
            
            # 设置图表标题和标签
            ax.set_title(f'{company_name} 收入结构对比', fontsize=16, pad=20)
            ax.set_ylabel('金额', fontsize=14)
            ax.set_xticks(x)
            ax.set_xticklabels(income_types, fontsize=12)
            
            # 添加数值标签
            def add_labels(bars):
                for bar in bars:
                    height = bar.get_height()
                    if height > 0:
                        # 根据数值大小调整标签位置和格式
                        if height > 1000:  # 大数值使用缩写形式
                            display_value = f'{height/1000:.1f}k'
                            va = 'bottom'
                        else:
                            display_value = f'{height:.1f}'
                            va = 'bottom'
                        ax.annotate(display_value,
                                   xy=(bar.get_x() + bar.get_width() / 2, height),
                                   xytext=(0, 3),  # 3点垂直偏移
                                   textcoords="offset points",
                                   ha='center', va=va, fontsize=10)
            
            add_labels(current_bars)
            add_labels(previous_bars)
            
            # 添加图例
            ax.legend(fontsize=12)
            
            # 添加网格线使图表更易读
            ax.grid(axis='y', linestyle='--', alpha=0.7)
            
            # 优化布局
            plt.tight_layout()
            
            # 保存图表
            income_chart_file = os.path.join(output_path, f"{company_name.replace(' ', '_')}_收入结构对比.png")
            plt.savefig(income_chart_file, dpi=300)
            plt.close()
            
            logger.info(f"收入结构对比图已保存至: {income_chart_file}")
            return income_chart_file
            
        except Exception as e:
            logger.error(f"生成收入结构对比图时出错: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def generate_financial_ratio_radar_chart(self, output_path='./output'):
        """生成财务比率雷达图
        
        Args:
            output_path (str): 输出目录路径
            
        Returns:
            str: 生成的图表文件路径
        """
        # 确保字体支持
        self.ensure_font_support()
        
        if not self.analyzer or not self.analyzer.financial_ratios:
            logger.warning("未设置分析器或财务比率尚未计算，无法生成图表")
            return None
        
        # 确保输出目录存在
        os.makedirs(output_path, exist_ok=True)
        
        # 获取公司信息
        company_info = self.analyzer.data.get('company_info', {})
        company_name = company_info.get('Company Name', '金融机构')
        
        # 获取年份信息
        current_year = self.analyzer.financial_ratios.get('current_year', '2024')
        previous_year = self.analyzer.financial_ratios.get('previous_year', '2023')
        
        # 获取财务比率数据
        ratios = self.analyzer.financial_ratios.get('ratios', {})
        
        try:
            # 选择关键财务比率
            ratio_names = [
                'Cost-to-Income Ratio', 'Debt-to-Assets Ratio', 'ROA', 'ROE', 
                'Loan-to-Deposit Ratio', 'Credit Cost Ratio'
            ]
            
            # 中文标签映射
            chinese_labels = {
                'Cost-to-Income Ratio': '成本收入比',
                'Debt-to-Assets Ratio': '资产负债率',
                'ROA': '资产收益率',
                'ROE': '权益收益率',
                'Loan-to-Deposit Ratio': '贷存比率',
                'Credit Cost Ratio': '信贷成本率'
            }
            
            # 准备数据
            ratio_values_current = []
            ratio_values_previous = []
            actual_ratio_names = []
            chinese_ratio_names = []
            
            for name in ratio_names:
                # 检查比率是否存在于当前和上一年数据中
                if name in ratios.get(current_year, {}) and name in ratios.get(previous_year, {}):
                    current_value = ratios[current_year][name]
                    previous_value = ratios[previous_year][name]
                    
                    # 将百分比转换为数值
                    if isinstance(current_value, str) and '%' in current_value:
                        current_value = float(current_value.strip('%')) / 100
                    if isinstance(previous_value, str) and '%' in previous_value:
                        previous_value = float(previous_value.strip('%')) / 100
                    
                    # 添加到值列表
                    ratio_values_current.append(float(current_value))
                    ratio_values_previous.append(float(previous_value))
                    actual_ratio_names.append(name)
                    chinese_ratio_names.append(chinese_labels.get(name, name))
            
            # 如果没有有效数据，返回None
            if not actual_ratio_names:
                logger.warning("没有足够的财务比率数据可用于生成雷达图")
                return None
            
            # 创建雷达图
            fig, ax = plt.subplots(figsize=(10, 8), subplot_kw=dict(polar=True))
            
            # 设置角度和标签
            angles = np.linspace(0, 2*np.pi, len(actual_ratio_names), endpoint=False).tolist()
            angles += angles[:1]  # 闭合图形
            
            # 修改标签位置
            ax.set_theta_offset(np.pi / 2)  # 偏移角度，使第一个标签位于顶部
            ax.set_theta_direction(-1)  # 逆时针方向
            
            # 添加标签
            plt.xticks(angles[:-1], chinese_ratio_names, fontsize=12)
            
            # 归一化数据以便显示
            max_values = [max(ratio_values_current[i], ratio_values_previous[i]) for i in range(len(actual_ratio_names))]
            min_values = [min(ratio_values_current[i], ratio_values_previous[i]) for i in range(len(actual_ratio_names))]
            
            # 计算每个指标的归一化系数
            scale_factors = []
            for i in range(len(actual_ratio_names)):
                if max_values[i] == 0:
                    scale_factors.append(1)  # 避免除以零
                else:
                    # 为了视觉效果，略微扩大范围
                    scale_factors.append(1.2 / max_values[i])
            
            # 归一化数据
            norm_current = [(ratio_values_current[i] * scale_factors[i]) for i in range(len(actual_ratio_names))]
            norm_previous = [(ratio_values_previous[i] * scale_factors[i]) for i in range(len(actual_ratio_names))]
            
            # 闭合数据
            norm_current += norm_current[:1]
            norm_previous += norm_previous[:1]
            
            # 绘制雷达图
            ax.plot(angles, norm_current, 'o-', linewidth=2, label=f'{current_year}年')
            ax.plot(angles, norm_previous, 's-', linewidth=2, label=f'{previous_year}年')
            ax.fill(angles, norm_current, alpha=0.25)
            ax.fill(angles, norm_previous, alpha=0.1)
            
            # 调整雷达图外观
            ax.set_ylim(0, 1.3)  # 适当设置y轴限制
            ax.set_title(f'{company_name} 财务比率对比', fontsize=16, pad=20)
            plt.legend(loc='upper right', bbox_to_anchor=(0.1, 0.1))
            
            plt.tight_layout()
            
            # 保存图片
            ratio_chart_file = os.path.join(output_path, f"{company_name.replace(' ', '_')}_财务比率雷达图.png")
            plt.savefig(ratio_chart_file, dpi=300)
            plt.close()
            
            logger.info(f"财务比率雷达图已保存至: {ratio_chart_file}")
            return ratio_chart_file
            
        except Exception as e:
            logger.error(f"生成财务比率雷达图时出错: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def generate_all_charts(self, output_path='./output'):
        """生成所有图表
        
        Args:
            output_path (str): 输出目录路径
            
        Returns:
            list: 生成的图表文件路径列表
        """
        chart_files = []
        
        # 生成收入结构对比图
        income_chart = self.generate_income_structure_chart(output_path)
        if income_chart:
            chart_files.append(income_chart)
        
        # 生成财务比率雷达图
        radar_chart = self.generate_financial_ratio_radar_chart(output_path)
        if radar_chart:
            chart_files.append(radar_chart)
        
        logger.info(f"已生成 {len(chart_files)} 个图表")
        return chart_files 