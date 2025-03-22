#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
财务报告生成模块
负责生成财务分析报告和可视化图表
"""

import os
import logging
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np

# 设置日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ReportGenerator:
    """财务报告生成器类"""
    
    def __init__(self, analyzer=None):
        """初始化财务报告生成器
        
        Args:
            analyzer: 财务分析器对象
        """
        self.analyzer = analyzer
    
    def set_analyzer(self, analyzer):
        """设置财务分析器
        
        Args:
            analyzer: 财务分析器对象
        """
        self.analyzer = analyzer
    
    def generate_comprehensive_report(self, output_path='./output'):
        """生成全面财务分析报告
        
        Args:
            output_path (str): 输出报告保存路径
            
        Returns:
            str: 报告文件路径
        """
        if not self.analyzer or not self.analyzer.data:
            logger.error("未设置分析器或未加载数据，无法生成报告")
            return None
        
        # 如果尚未计算财务比率和趋势，先计算
        if not self.analyzer.financial_ratios:
            self.analyzer.calculate_financial_ratios()
        
        if not self.analyzer.financial_trends:
            self.analyzer.analyze_financial_trends()
        
        logger.info("生成全面财务分析报告...")
        
        # 确保输出目录存在
        os.makedirs(output_path, exist_ok=True)
        
        # 获取公司信息
        company_info = self.analyzer.data.get('company_info', {})
        company_name = company_info.get('Company Name', '金融机构')
        report_date = company_info.get('Report Date', datetime.now().strftime('%Y-%m-%d'))
        currency = company_info.get('Currency', 'HKD')
        unit = company_info.get('Unit', '千')
        
        # 获取年份信息
        current_year = self.analyzer.financial_ratios.get('current_year', '2024')
        previous_year = self.analyzer.financial_ratios.get('previous_year', '2023')
        
        # 获取财务比率数据
        ratios = self.analyzer.financial_ratios.get('ratios', {})
        ratio_changes = self.analyzer.financial_ratios.get('ratio_changes', {})
        
        # 获取财务趋势数据
        trends = self.analyzer.financial_trends
        
        # 创建报告内容
        report_content = []
        
        # 报告标题
        report_content.append(f"===================== {company_name} {current_year}年财务分析报告 =====================")
        report_content.append(f"报告生成日期: {datetime.now().strftime('%Y-%m-%d')}")
        report_content.append(f"财务数据截止日期: {report_date}")
        report_content.append(f"货币单位: {currency} {unit}")
        
        # 报告概览
        report_content.append("\n【报告概览】")
        report_content.append(f"本报告对{company_name}的财务状况进行全面分析，")
        report_content.append("揭示金融机构的财务表现、经营趋势和潜在风险。")
        
        # 财务表现概述
        report_content.append("\n【财务表现概述】")
        
        # 净亏损/利润情况
        net_loss_curr = ratios.get(current_year, {}).get('Net Loss', 0)
        net_loss_prev = ratios.get(previous_year, {}).get('Net Loss', 0)
        
        if 'Net Loss' in ratio_changes:
            net_loss_change = ratio_changes['Net Loss']['Change']
            net_loss_change_pct = ratio_changes['Net Loss']['Change%']
            
            if net_loss_change < 0:
                report_content.append(f"· {current_year}年净亏损为{abs(net_loss_curr):.2f}{unit}{currency}，较{previous_year}年减少{abs(net_loss_change):.2f}{unit}{currency}（{abs(net_loss_change_pct):.2f}%）。")
                report_content.append("· 亏损收窄表明经营状况有所改善。")
            else:
                report_content.append(f"· {current_year}年净亏损为{abs(net_loss_curr):.2f}{unit}{currency}，较{previous_year}年增加{net_loss_change:.2f}{unit}{currency}（{net_loss_change_pct:.2f}%）。")
                report_content.append("· 亏损扩大表明经营压力加大。")
        
        # 收入结构分析
        report_content.append("\n【收入结构分析】")
        
        total_income_curr = ratios.get(current_year, {}).get('Total Income', 0)
        total_income_prev = ratios.get(previous_year, {}).get('Total Income', 0)
        
        if 'Total Income' in ratio_changes:
            total_income_change = ratio_changes['Total Income']['Change']
            total_income_change_pct = ratio_changes['Total Income']['Change%']
            
            report_content.append(f"· 总收入：{current_year}年总收入为{total_income_curr:.2f}{unit}{currency}，")
            report_content.append(f"  较{previous_year}年{total_income_prev:.2f}{unit}{currency}{('增加' if total_income_change > 0 else '减少')}{abs(total_income_change):.2f}{unit}{currency}（{abs(total_income_change_pct):.2f}%）。")
        
        # 风险分析
        report_content.append("\n【风险分析】")
        
        # 主要财务趋势
        report_content.append("\n【主要财务趋势】")
        
        for category, items in trends.items():
            if items and category not in ['risk_factors', 'strength_factors']:
                category_name = {
                    'growth': '增长趋势',
                    'profitability': '盈利能力',
                    'efficiency': '运营效率',
                    'financial_health': '财务健康'
                }.get(category, category.replace('_', ' ').title())
                
                report_content.append(f"\n· {category_name}:")
                for item in items:
                    report_content.append(f"  - {item}")
        
        # 风险因素和优势因素
        report_content.append("\n【风险因素】")
        for item in trends.get('risk_factors', []):
            report_content.append(f"· {item}")
        
        report_content.append("\n【优势因素】")
        for item in trends.get('strength_factors', []):
            report_content.append(f"· {item}")
        
        # 建议与展望
        report_content.append("\n【建议与展望】")
        
        # 根据分析结果生成建议
        suggestions = []
        
        # 成本控制建议
        if ratios.get(current_year, {}).get('Cost-to-Income Ratio', 0) > 70:
            suggestions.append("· 成本控制：成本收入比较高，建议优化运营流程，控制成本支出，提高运营效率。")
        
        # 风险管理建议
        if 'Credit Impairment Losses' in ratio_changes and ratio_changes['Credit Impairment Losses'].get('Change%', 0) > 10:
            suggestions.append("· 风险管理：信贷减值损失增加，建议加强风险管理，优化信贷政策，提高资产质量。")
        
        # 如果没有生成建议，添加通用建议
        if not suggestions:
            suggestions.append("· 继续保持当前的经营策略，在控制风险的基础上稳步发展业务。")
            suggestions.append("· 密切关注市场环境变化，及时调整经营策略，把握市场机遇。")
        
        # 添加通用建议
        suggestions.append("· 加强数字化转型，提升客户体验，增强市场竞争力。")
        
        # 将建议添加到报告
        for suggestion in suggestions:
            report_content.append(suggestion)
        
        # 报告结语
        report_content.append("\n【结语】")
        report_content.append(f"{company_name}在{current_year}年展现了一定的经营韧性，")
        if 'Net Loss' in ratio_changes and ratio_changes['Net Loss']['Change%'] < 0:
            report_content.append("亏损有所收窄，表明经营状况正逐步改善。")
        elif 'Total Income' in ratio_changes and ratio_changes['Total Income']['Change%'] > 0:
            report_content.append("收入实现增长，展现了较好的业务发展势头。")
        else:
            report_content.append("但仍面临一定的经营挑战。")
        
        report_content.append("通过实施有效的战略调整，加强风险管理，优化资产负债结构，")
        report_content.append("有望在未来进一步改善经营状况，实现可持续发展。")
        
        # 报告署名
        report_content.append("\n======================================================================")
        report_content.append(f"报告生成系统：金融机构财务分析系统")
        report_content.append(f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 将报告保存到文件
        report_file = os.path.join(output_path, f"{company_name.replace(' ', '_')}_{current_year}_财务分析报告.txt")
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report_content))
        
        logger.info(f"报告已保存至: {report_file}")
        
        return report_file
    
    def create_data_visualization(self, output_path='./output'):
        """创建数据可视化图表
        
        Args:
            output_path (str): 输出图表保存路径
            
        Returns:
            list: 生成的图表文件路径列表
        """
        if not self.analyzer or not self.analyzer.financial_ratios:
            logger.warning("未设置分析器或财务比率尚未计算，无法创建可视化")
            return []
        
        logger.info("创建数据可视化图表...")
        
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
        
        # 创建图表
        chart_files = []
        
        try:
            # 设置中文字体
            plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
            plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号
            
            # 1. 收入结构对比图
            if 'Interest Income' in ratios.get(current_year, {}) and 'Fee Income' in ratios.get(current_year, {}):
                fig, ax = plt.subplots(figsize=(10, 6))
                
                # 准备数据
                income_types = ['利息收入', '手续费收入', '其他收入']
                current_income = [
                    ratios[current_year].get('Interest Income', 0),
                    ratios[current_year].get('Fee Income', 0),
                    ratios[current_year].get('Total Income', 0) - ratios[current_year].get('Interest Income', 0) - ratios[current_year].get('Fee Income', 0)
                ]
                previous_income = [
                    ratios[previous_year].get('Interest Income', 0),
                    ratios[previous_year].get('Fee Income', 0),
                    ratios[previous_year].get('Total Income', 0) - ratios[previous_year].get('Interest Income', 0) - ratios[previous_year].get('Fee Income', 0)
                ]
                
                # 创建柱状图
                x = np.arange(len(income_types))
                width = 0.35
                
                ax.bar(x - width/2, current_income, width, label=current_year)
                ax.bar(x + width/2, previous_income, width, label=previous_year)
                
                ax.set_title(f'{company_name} 收入结构对比')
                ax.set_ylabel('金额')
                ax.set_xticks(x)
                ax.set_xticklabels(income_types)
                ax.legend()
                
                # 保存图表
                income_chart_file = os.path.join(output_path, f"{company_name.replace(' ', '_')}_收入结构对比.png")
                plt.tight_layout()
                plt.savefig(income_chart_file, dpi=300)
                plt.close()
                
                chart_files.append(income_chart_file)
                logger.info(f"收入结构对比图已保存至: {income_chart_file}")
            
            # 2. 财务比率雷达图
            if ratios.get(current_year, {}) and ratios.get(previous_year, {}):
                # 选择关键财务比率
                ratio_names = [
                    'Cost-to-Income Ratio', 'Debt-to-Assets Ratio', 'ROA', 'ROE', 
                    'Loan-to-Deposit Ratio', 'Credit Cost Ratio'
                ]
                
                # 准备数据
                ratio_values_current = []
                ratio_values_previous = []
                actual_ratio_names = []
                
                for name in ratio_names:
                    if name in ratios[current_year] and name in ratios[previous_year]:
                        ratio_values_current.append(abs(ratios[current_year][name]))
                        ratio_values_previous.append(abs(ratios[previous_year][name]))
                        
                        # 转换比率名称为中文
                        chinese_name = {
                            'Cost-to-Income Ratio': '成本收入比',
                            'Debt-to-Assets Ratio': '资产负债率',
                            'ROA': '资产收益率',
                            'ROE': '权益收益率',
                            'Loan-to-Deposit Ratio': '贷存比',
                            'Credit Cost Ratio': '信贷成本率'
                        }.get(name, name)
                        
                        actual_ratio_names.append(chinese_name)
                
                if actual_ratio_names:
                    # 创建雷达图
                    fig = plt.figure(figsize=(10, 8))
                    ax = fig.add_subplot(111, polar=True)
                    
                    # 计算角度
                    angles = np.linspace(0, 2*np.pi, len(actual_ratio_names), endpoint=False).tolist()
                    angles += angles[:1]  # 闭合图形
                    
                    # 添加数据
                    ratio_values_current += ratio_values_current[:1]  # 闭合数据
                    ratio_values_previous += ratio_values_previous[:1]  # 闭合数据
                    
                    # 绘制雷达图
                    ax.plot(angles, ratio_values_current, 'o-', linewidth=2, label=current_year)
                    ax.plot(angles, ratio_values_previous, 'o-', linewidth=2, label=previous_year)
                    ax.fill(angles, ratio_values_current, alpha=0.25)
                    ax.fill(angles, ratio_values_previous, alpha=0.25)
                    
                    # 设置标签
                    ax.set_thetagrids(np.degrees(angles[:-1]), actual_ratio_names)
                    ax.set_title(f'{company_name} 财务比率对比')
                    ax.legend(loc='upper right')
                    
                    # 保存图表
                    ratio_chart_file = os.path.join(output_path, f"{company_name.replace(' ', '_')}_财务比率雷达图.png")
                    plt.tight_layout()
                    plt.savefig(ratio_chart_file, dpi=300)
                    plt.close()
                    
                    chart_files.append(ratio_chart_file)
                    logger.info(f"财务比率雷达图已保存至: {ratio_chart_file}")
            
        except Exception as e:
            logger.error(f"创建数据可视化图表时出错: {e}")
            import traceback
            traceback.print_exc()
        
        logger.info(f"数据可视化图表生成完成，共生成 {len(chart_files)} 个图表")
        
        return chart_files 