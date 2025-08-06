#!/usr/bin/env python3
"""
生成财报下载情况总结
Generate financial report download summary
"""
import os
import csv
from pathlib import Path
from collections import defaultdict
import json

def main():
    project_root = Path(__file__).parent.parent
    csv_path = project_root / 'data' / 'Company_Financial_report.csv'
    reports_dir = project_root / 'data' / 'raw_reports'
    
    # 统计CSV中的财报
    csv_stats = defaultdict(int)
    companies_in_csv = set()
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get('Financial Report(Y/N)') == 'Y':
                csv_stats['total'] += 1
                companies_in_csv.add(row['name'])
    
    csv_stats['companies'] = len(companies_in_csv)
    
    # 统计已下载的文件
    downloaded_files = []
    downloaded_companies = set()
    
    for file in reports_dir.iterdir():
        if file.suffix in ['.pdf', '.html']:
            downloaded_files.append(file.name)
            # 提取公司名（文件名格式: Company_Year_Type.ext）
            parts = file.stem.split('_')
            if parts:
                company = parts[0]
                downloaded_companies.add(company)
    
    # 生成报告
    report = {
        'csv_statistics': {
            'total_reports': csv_stats['total'],
            'total_companies': csv_stats['companies']
        },
        'download_statistics': {
            'total_downloaded': len(downloaded_files),
            'companies_covered': len(downloaded_companies),
            'pdf_files': len([f for f in downloaded_files if f.endswith('.pdf')]),
            'html_files': len([f for f in downloaded_files if f.endswith('.html')])
        },
        'coverage': {
            'report_coverage': f"{len(downloaded_files) / csv_stats['total'] * 100:.1f}%" if csv_stats['total'] > 0 else "0%",
            'company_coverage': f"{len(downloaded_companies) / csv_stats['companies'] * 100:.1f}%" if csv_stats['companies'] > 0 else "0%"
        },
        'top_companies': list(downloaded_companies)[:20]
    }
    
    # 保存报告
    output_path = project_root / 'output' / 'download_summary.json'
    output_path.parent.mkdir(exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    # 打印报告
    print("财报下载情况总结")
    print("=" * 60)
    print(f"CSV数据库统计:")
    print(f"  - 总财报数: {report['csv_statistics']['total_reports']}")
    print(f"  - 总公司数: {report['csv_statistics']['total_companies']}")
    print()
    print(f"下载统计:")
    print(f"  - 已下载文件: {report['download_statistics']['total_downloaded']}")
    print(f"  - 覆盖公司数: {report['download_statistics']['companies_covered']}")
    print(f"  - PDF文件: {report['download_statistics']['pdf_files']}")
    print(f"  - HTML文件: {report['download_statistics']['html_files']}")
    print()
    print(f"覆盖率:")
    print(f"  - 财报覆盖率: {report['coverage']['report_coverage']}")
    print(f"  - 公司覆盖率: {report['coverage']['company_coverage']}")
    print()
    print(f"报告已保存至: {output_path}")

if __name__ == "__main__":
    main()