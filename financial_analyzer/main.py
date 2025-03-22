#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
财务分析系统主模块
整合PDF数据提取、财务分析和报告生成功能
提供命令行接口
"""

import os
import sys
import time
import logging
import argparse
from datetime import datetime

# 导入项目模块
from financial_analyzer.data_extraction.pdf_extractor import PDFDataExtractor
from financial_analyzer.analysis.financial_analyzer import FinancialAnalyzer
from financial_analyzer.analysis.report_generator import ReportGenerator
from financial_analyzer.visualization.chart_generator import ChartGenerator

# 设置日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='金融财务报告分析工具')
    parser.add_argument('--pdf', type=str, default=None, help='PDF报告文件路径')
    parser.add_argument('--output', type=str, default='./output', help='输出报告保存路径')
    parser.add_argument('--extract-only', action='store_true', help='仅提取数据，不进行分析')
    parser.add_argument('--json', type=str, default=None, help='使用已提取的JSON数据文件进行分析')
    parser.add_argument('--no-viz', action='store_true', help='不生成可视化图表')
    parser.add_argument('--verbose', action='store_true', help='输出详细日志')
    return parser.parse_args()

def generate_report(pdf_path=None, json_path=None, output_path='./output', extract_only=False, visualize=True, verbose=False):
    """生成财务分析报告
    
    Args:
        pdf_path (str): PDF报告文件路径
        json_path (str): 已提取的JSON数据文件路径
        output_path (str): 输出报告保存路径
        extract_only (bool): 是否仅提取数据，不进行分析
        visualize (bool): 是否生成可视化图表
        verbose (bool): 是否输出详细日志
    
    Returns:
        dict: 包含执行结果和生成的文件路径
    """
    # 设置日志级别
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # 确保输出目录存在
    os.makedirs(output_path, exist_ok=True)
    
    # 记录开始时间
    start_time = time.time()
    result = {'success': False, 'files': []}
    
    try:
        # 步骤1: 数据提取
        extracted_data = None
        
        if pdf_path:
            logger.info(f"开始从PDF提取数据: {pdf_path}")
            
            # 检查文件是否存在
            if not os.path.exists(pdf_path):
                logger.error(f"文件不存在: {pdf_path}")
                return {'success': False, 'error': f"文件不存在: {pdf_path}"}
            
            # 创建数据提取器
            extractor = PDFDataExtractor(pdf_path)
            
            # 提取数据
            extract_start = time.time()
            extractor.extract_pdf_content()
            extracted_data = extractor.get_data_for_analysis()
            extract_end = time.time()
            
            logger.info(f"数据提取完成，耗时 {extract_end - extract_start:.2f} 秒")
            
            # 获取提取的JSON文件路径
            company_info = extracted_data.get('company_info', {})
            company_name = company_info.get('Company Name', 'Unknown')
            report_date = company_info.get('Report Date', datetime.now().strftime('%Y-%m-%d'))
            
            # 保存json文件路径
            json_path = os.path.join(output_path, f"{company_name.replace(' ', '_')}_{report_date}_extracted_data.json")
            result['files'].append(json_path)
            
            # 如果只需要提取数据，到此结束
            if extract_only:
                end_time = time.time()
                logger.info(f"仅数据提取模式，总耗时 {end_time - start_time:.2f} 秒")
                
                result['success'] = True
                result['message'] = "数据提取成功"
                
                return result
        
        # 步骤2: 财务分析
        # 如果提供了JSON数据文件但没有提取数据，则从JSON加载数据
        elif json_path:
            logger.info(f"使用已提取的数据进行分析: {json_path}")
            
            # 检查文件是否存在
            if not os.path.exists(json_path):
                logger.error(f"数据文件不存在: {json_path}")
                return {'success': False, 'error': f"数据文件不存在: {json_path}"}
            
            # 创建分析器并加载数据
            analyzer = FinancialAnalyzer()
            if not analyzer.load_data(json_path):
                logger.error(f"无法加载数据文件: {json_path}")
                return {'success': False, 'error': f"无法加载数据文件: {json_path}"}
            
            extracted_data = analyzer.data
        else:
            logger.error("未提供PDF文件或JSON数据文件")
            return {'success': False, 'error': "未提供PDF文件或JSON数据文件"}
        
        # 步骤3: 执行分析并生成报告
        analysis_start = time.time()
        
        # 创建分析器（如果尚未创建）
        if 'analyzer' not in locals():
            analyzer = FinancialAnalyzer(extracted_data)
        
        # 计算财务比率
        analyzer.calculate_financial_ratios()
        
        # 分析财务趋势
        analyzer.analyze_financial_trends()
        
        # 创建报告生成器
        report_generator = ReportGenerator(analyzer)
        
        # 生成报告
        report_file = report_generator.generate_comprehensive_report(output_path)
        if report_file:
            result['files'].append(report_file)
        
        # 生成可视化图表
        if visualize:
            chart_generator = ChartGenerator(analyzer)
            chart_files = chart_generator.generate_all_charts(output_path)
            if chart_files:
                result['files'].extend(chart_files)
                logger.info(f"生成了 {len(chart_files)} 个可视化图表")
        
        analysis_end = time.time()
        logger.info(f"分析和报告生成完成，耗时 {analysis_end - analysis_start:.2f} 秒")
        
        # 记录总耗时
        end_time = time.time()
        total_time = end_time - start_time
        logger.info(f"全部完成，总耗时 {total_time:.2f} 秒")
        
        # 设置返回结果
        result['success'] = True
        result['message'] = "报告生成成功"
        result['time'] = total_time
        
        return result
        
    except Exception as e:
        import traceback
        logger.error(f"处理过程中出错: {e}")
        traceback.print_exc()
        
        end_time = time.time()
        logger.info(f"由于错误结束，耗时 {end_time - start_time:.2f} 秒")
        
        return {'success': False, 'error': str(e)}

def main():
    """主函数"""
    # 解析命令行参数
    args = parse_arguments()
    
    # 检查必要的参数
    if not args.pdf and not args.json:
        print("错误: 必须提供PDF文件路径(--pdf)或JSON数据文件路径(--json)")
        sys.exit(1)
    
    # 执行报告生成
    result = generate_report(
        pdf_path=args.pdf,
        json_path=args.json,
        output_path=args.output,
        extract_only=args.extract_only,
        visualize=not args.no_viz,
        verbose=args.verbose
    )
    
    # 输出结果
    if result['success']:
        print(f"\n处理完成! {result['message']}")
        if 'files' in result and result['files']:
            print("\n生成的文件:")
            for file in result['files']:
                print(f"- {file}")
    else:
        print(f"\n处理失败: {result.get('error', '未知错误')}")
        sys.exit(1)

if __name__ == "__main__":
    main() 