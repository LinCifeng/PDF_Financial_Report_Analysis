"""
数据分析模块
Data Analysis Module
"""
import csv
import json
from pathlib import Path
from typing import Dict, List
from collections import defaultdict


def analyze_companies(csv_path: str = "data/Company_Financial_report.csv",
                     report_dir: str = "data/raw_reports") -> Dict:
    """分析公司财报覆盖情况"""
    # 读取CSV中的公司列表
    companies_in_csv = set()
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get('Financial Report(Y/N)') == 'Y':
                companies_in_csv.add(row['name'])
    
    # 获取已下载的文件
    report_path = Path(report_dir)
    downloaded_companies = set()
    file_count = defaultdict(int)
    
    for file in report_path.glob("*.pdf"):
        company = file.stem.split('_')[0]
        downloaded_companies.add(company)
        file_count[company] += 1
    
    # 统计
    coverage_rate = len(downloaded_companies) / len(companies_in_csv) * 100 if companies_in_csv else 0
    
    stats = {
        'total_companies': len(companies_in_csv),
        'downloaded_companies': len(downloaded_companies),
        'coverage_rate': coverage_rate,
        'missing_companies': sorted(companies_in_csv - downloaded_companies),
        'top_companies': sorted(file_count.items(), key=lambda x: x[1], reverse=True)[:10]
    }
    
    print(f"\nCompany Analysis")
    print("="*60)
    print(f"Total companies: {stats['total_companies']}")
    print(f"Companies with downloads: {stats['downloaded_companies']}")
    print(f"Coverage rate: {stats['coverage_rate']:.1f}%")
    print(f"\nTop 10 companies by report count:")
    for company, count in stats['top_companies']:
        print(f"  {company}: {count} reports")
    
    return stats


def analyze_extraction_results(csv_file: str) -> Dict:
    """分析提取结果"""
    results = []
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        results = list(reader)
    
    total = len(results)
    success = sum(1 for r in results if r.get('Status') == 'Success')
    
    # 统计各指标
    metrics = ['Total Assets', 'Total Liabilities', 'Revenue', 'Net Profit']
    metric_stats = {}
    
    for metric in metrics:
        count = sum(1 for r in results if r.get(metric))
        metric_stats[metric] = {
            'count': count,
            'rate': count / total * 100 if total > 0 else 0
        }
    
    stats = {
        'total_files': total,
        'successful': success,
        'success_rate': success / total * 100 if total > 0 else 0,
        'metrics': metric_stats
    }
    
    print(f"\nExtraction Analysis")
    print("="*60)
    print(f"Total files: {stats['total_files']}")
    print(f"Successful: {stats['successful']} ({stats['success_rate']:.1f}%)")
    print(f"\nMetric extraction rates:")
    for metric, data in metric_stats.items():
        print(f"  {metric}: {data['count']} ({data['rate']:.1f}%)")
    
    return stats


def analyze_data(task: str = "companies", **kwargs) -> Dict:
    """
    数据分析主函数
    
    Args:
        task: 分析任务类型 (companies/extraction)
        **kwargs: 额外参数
        
    Returns:
        分析结果
    """
    if task == "companies":
        return analyze_companies(**kwargs)
    elif task == "extraction":
        if 'csv_file' not in kwargs:
            # 找最新的提取结果
            output_dir = Path("output")
            csv_files = list(output_dir.glob("extraction_results_*.csv"))
            if csv_files:
                latest_file = max(csv_files, key=lambda f: f.stat().st_mtime)
                kwargs['csv_file'] = str(latest_file)
            else:
                raise ValueError("No extraction results found")
        return analyze_extraction_results(**kwargs)
    else:
        raise ValueError(f"Unknown task: {task}")