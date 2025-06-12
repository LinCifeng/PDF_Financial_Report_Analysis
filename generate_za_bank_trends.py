#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ZA Bank 多年资产趋势分析脚本
基于现有的图表生成器功能
"""

import os
import sys
import logging
from datetime import datetime

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from financial_analyzer.visualization.chart_generator import ChartGenerator

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """主函数"""
    print("=" * 60)
    print("ZA Bank Multi-Year Asset Trend Analysis (2020-2024)")
    print("=" * 60)
    
    # 创建图表生成器
    chart_generator = ChartGenerator()
    
    # 生成多年趋势图表
    print("\nGenerating multi-year asset trend charts...")
    result = chart_generator.generate_multi_year_asset_trends(
        data_dir='./data',
        output_path='./output'
    )
    
    chart_files = result.get('chart_files', [])
    json_file = result.get('json_file')
    data_summary = result.get('data_summary', {})
    
    if chart_files:
        print(f"\n✅ Successfully generated {len(chart_files)} charts:")
        for chart_file in chart_files:
            print(f"  - {os.path.basename(chart_file)}")
        
        if json_file:
            print(f"\n📄 Merged data saved to: {os.path.basename(json_file)}")
            
            # 显示数据汇总
            if data_summary:
                print(f"\n📈 Data Summary:")
                print(f"  - Analysis period: {data_summary.get('year_range', 'N/A')}")
                print(f"  - Total years analyzed: {data_summary.get('total_years', 0)}")
                
                growth_analysis = data_summary.get('growth_analysis', {})
                if 'Total Assets' in growth_analysis:
                    ta_growth = growth_analysis['Total Assets']
                    print(f"  - Total Assets growth: {ta_growth.get('growth_rate_percent', 0):.1f}%")
                    print(f"    ({ta_growth.get('start_value', 0)/1000000:.1f}B → {ta_growth.get('end_value', 0)/1000000:.1f}B HKD)")
        
        print(f"\n📊 All files saved to: ./output/")
        print(f"📅 Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        print("\n❌ No charts were generated. Please check the data files.")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main() 