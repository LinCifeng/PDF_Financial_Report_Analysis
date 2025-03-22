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
        
        # 字体设置已移至run_analysis.py中统一处理
    
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