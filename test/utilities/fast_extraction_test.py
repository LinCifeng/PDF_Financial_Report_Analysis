#!/usr/bin/env python3
"""
快速提取率测试
Fast Extraction Rate Test

作者: Lin Cifeng
创建时间: 2025-08-06
"""
import os
import sys
from pathlib import Path
import time
from datetime import datetime

# 设置项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 设置API密钥
env_path = project_root / '.env'
if env_path.exists():
    with open(env_path, 'r') as f:
        for line in f:
            if 'DEEPSEEK_API_KEY=' in line:
                key = line.split('=', 1)[1].strip()
                os.environ['DEEPSEEK_API_KEY'] = key
                break

# 使用核心模块的提取器
from financial_analysis.extractor import MasterExtractor
# EnhancedMasterExtractor 不存在，注释掉
# from test.enhanced_master_extractor import EnhancedMasterExtractor


def fast_test():
    """快速测试10个文件"""
    print("=" * 80)
    print(f"快速提取率测试 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # 选择有代表性的测试文件
    test_files = [
        # 之前成功的
        "Airstarbank_2019_Annual.pdf",
        "ZA_Bank_2020_Annual.pdf",
        "Livi_Bank_2023_Annual.pdf",
        # 之前失败的
        "Fusion_Bank_2021_Annual.pdf",
        "WeLab_Bank_2021_Annual.pdf",
        # 其他银行
        "Mox_Bank_2023_Annual.pdf",
        "PAO_Bank_2021_Annual.pdf",
        "Ant_Bank_HK_2023_Annual.pdf",
        "Ping_An_OneConnect_Bank_HK_2023_Annual.pdf",
        "WeLab_Bank_2023_Annual.pdf"
    ]
    
    # 初始化提取器
    extractors = {
        '基础提取': MasterExtractor(use_llm=False),
        # '增强提取': EnhancedMasterExtractor(use_llm=False),  # 不存在
        # 'LLM增强': EnhancedMasterExtractor(use_llm=True)  # 不存在
        'LLM提取': MasterExtractor(use_llm=True)
    }
    
    # 统计结果
    stats = {name: {
        'total': 0,
        'assets': 0,
        'liabilities': 0,
        'revenue': 0,
        'profit': 0,
        'complete': 0,
        'time': 0
    } for name in extractors.keys()}
    
    # 处理每个文件
    pdf_dir = project_root / "data/raw_reports"
    
    for i, filename in enumerate(test_files):
        pdf_path = pdf_dir / filename
        
        if not pdf_path.exists():
            # 尝试查找类似文件
            similar = list(pdf_dir.glob(f"*{filename.split('_')[0]}*"))
            if similar:
                pdf_path = similar[0]
            else:
                print(f"\n[{i+1}/10] {filename} - 未找到")
                continue
        
        print(f"\n[{i+1}/10] {pdf_path.name}")
        
        for name, extractor in extractors.items():
            try:
                start = time.time()
                result = extractor.extract(str(pdf_path))
                elapsed = time.time() - start
                
                # 统计
                stats[name]['total'] += 1
                stats[name]['time'] += elapsed
                
                # 字段统计
                field_count = 0
                if result['data'].get('total_assets'):
                    stats[name]['assets'] += 1
                    field_count += 1
                if result['data'].get('total_liabilities'):
                    stats[name]['liabilities'] += 1
                    field_count += 1
                if result['data'].get('revenue'):
                    stats[name]['revenue'] += 1
                    field_count += 1
                if result['data'].get('net_profit'):
                    stats[name]['profit'] += 1
                    field_count += 1
                
                if field_count == 4:
                    stats[name]['complete'] += 1
                
                print(f"  {name}: {field_count}个字段 ({elapsed:.1f}秒) - {result['method']}")
                
            except Exception as e:
                print(f"  {name}: 错误 - {str(e)[:50]}")
                stats[name]['total'] += 1
    
    # 打印统计结果
    print("\n" + "=" * 80)
    print("提取率统计结果")
    print("=" * 80)
    
    # 表格头
    print(f"\n{'提取器':<12} {'总资产':<10} {'总负债':<10} {'营业收入':<10} {'净利润':<10} {'完整率':<10} {'平均耗时'}")
    print("-" * 75)
    
    # 打印每个提取器的结果
    for name, stat in stats.items():
        if stat['total'] == 0:
            continue
        
        assets_rate = stat['assets'] / stat['total'] * 100
        liabilities_rate = stat['liabilities'] / stat['total'] * 100
        revenue_rate = stat['revenue'] / stat['total'] * 100
        profit_rate = stat['profit'] / stat['total'] * 100
        complete_rate = stat['complete'] / stat['total'] * 100
        avg_time = stat['time'] / stat['total']
        
        print(f"{name:<12} {assets_rate:>6.1f}%    {liabilities_rate:>6.1f}%    "
              f"{revenue_rate:>6.1f}%     {profit_rate:>6.1f}%    "
              f"{complete_rate:>6.1f}%     {avg_time:>5.1f}秒")
    
    # 改进对比
    print("\n\n相对于基础提取的改进:")
    base = stats['基础提取']
    
    for name in ['增强提取', 'LLM增强']:
        if stats[name]['total'] == 0:
            continue
        
        print(f"\n{name}:")
        
        # 各字段改进
        fields = [
            ('总资产', 'assets'),
            ('总负债', 'liabilities'),
            ('营业收入', 'revenue'),
            ('净利润', 'profit')
        ]
        
        for field_name, field_key in fields:
            base_rate = base[field_key] / max(base['total'], 1) * 100
            current_rate = stats[name][field_key] / max(stats[name]['total'], 1) * 100
            improvement = current_rate - base_rate
            
            if improvement > 0:
                print(f"  {field_name}: +{improvement:.1f}% (从{base_rate:.1f}%提升到{current_rate:.1f}%)")
            elif improvement < 0:
                print(f"  {field_name}: {improvement:.1f}% (从{base_rate:.1f}%降到{current_rate:.1f}%)")
        
        # 完整率改进
        base_complete = base['complete'] / max(base['total'], 1) * 100
        current_complete = stats[name]['complete'] / max(stats[name]['total'], 1) * 100
        complete_improvement = current_complete - base_complete
        
        if complete_improvement != 0:
            print(f"  完整提取率: {complete_improvement:+.1f}% (从{base_complete:.1f}%到{current_complete:.1f}%)")


if __name__ == "__main__":
    fast_test()