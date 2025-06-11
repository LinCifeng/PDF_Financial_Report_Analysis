#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Collection Status of Financial Reports Analysis Tool
轻量级财报收集情况分析工具（不使用pandas）
"""

import csv
from datetime import datetime
from collections import defaultdict

def analyze_reports():
    print("开始财报收集情况分析...")
    
    # 基本计数器
    total_records = 0
    companies = set()
    has_reports = 0
    no_reports = 0
    companies_with_reports = set()
    company_report_counts = defaultdict(int)
    company_years = defaultdict(list)  # 存储每个公司的年份
    
    print("读取数据...")
    
    # 逐行读取CSV，避免内存问题
    with open('data/Company_Financial_report.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            total_records += 1
            
            company_id = row.get('new_id', '').strip()
            company_name = row.get('name', '').strip()
            report_status = row.get('Financial Report(Y/N)', '').strip()
            fiscal_year = row.get('Fiscal_year', '').strip()
            
            if company_id:
                companies.add(company_id)
            
            if report_status == 'Y':
                has_reports += 1
                if company_id:
                    companies_with_reports.add(company_id)
                    company_report_counts[company_name] += 1
                
                # 处理年份数据
                if fiscal_year:
                    try:
                        if '/' in fiscal_year:
                            year_parts = fiscal_year.split('/')
                            if len(year_parts) == 2:
                                year = int(year_parts[1])
                                if year < 50:
                                    year += 2000
                                elif year < 100:
                                    year += 1900
                        else:
                            year = int(float(fiscal_year))
                        
                        if 1990 <= year <= 2030:
                            company_years[company_name].append(year)
                    except (ValueError, IndexError):
                        continue
                        
            elif report_status == 'N':
                no_reports += 1
            
            # 显示进度
            if total_records % 500 == 0:
                print(f"已处理 {total_records} 条记录...")
    
    # 计算统计数据
    total_companies = len(companies)
    companies_with_reports_count = len(companies_with_reports)
    collection_rate = (companies_with_reports_count / total_companies * 100) if total_companies > 0 else 0
    
    # 计算平均每公司报告数
    avg_reports_per_company = sum(company_report_counts.values()) / len(company_report_counts) if company_report_counts else 0
    
    # 分析每个公司的年份范围
    company_year_ranges = []
    earliest_years = []
    latest_years = []
    year_spans = []
    
    for company, years in company_years.items():
        if years:
            years = sorted(set(years))  # 去重并排序
            earliest = min(years)
            latest = max(years)
            span = latest - earliest + 1
            
            company_year_ranges.append((company, earliest, latest, span, len(years)))
            earliest_years.append(earliest)
            latest_years.append(latest)
            year_spans.append(span)
    
    # 计算统计
    avg_earliest_year = sum(earliest_years) / len(earliest_years) if earliest_years else 0
    avg_latest_year = sum(latest_years) / len(latest_years) if latest_years else 0
    avg_year_span = sum(year_spans) / len(year_spans) if year_spans else 0
    
    # 统计最近几年开始的公司
    recent_starters = len([year for year in earliest_years if year >= 2015])
    very_recent_starters = len([year for year in earliest_years if year >= 2020])
    
    print(f"数据处理完成，共 {total_records} 条记录")
    
    # 生成markdown格式的报告
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    report = f"""# Collection Status of Financial Reports Analysis

**Generated:** {timestamp}

## Data Summary

| Metric | Value | Percentage |
|--------|-------|------------|
| Total Records | {total_records:,} | 100.0% |
| Total Companies | {total_companies:,} | - |
| Records with Reports | {has_reports:,} | {has_reports/total_records*100:.1f}% |
| Records without Reports | {no_reports:,} | {no_reports/total_records*100:.1f}% |
| Companies with Reports | {companies_with_reports_count:,} | {collection_rate:.1f}% |

## Report Coverage Analysis

- **Average Reports per Company:** {avg_reports_per_company:.1f}
- **Companies with Year Data:** {len(company_years):,}

## Year Range Analysis

| Metric | Value |
|--------|-------|
| Average Starting Year | {avg_earliest_year:.0f} |
| Average Ending Year | {avg_latest_year:.0f} |
| Average Year Span per Company | {avg_year_span:.1f} years |

### Recent Data Focus

- **Companies starting from 2015+:** {recent_starters} ({recent_starters/len(earliest_years)*100:.1f}%)
- **Companies starting from 2020+:** {very_recent_starters} ({very_recent_starters/len(earliest_years)*100:.1f}%)

## Assessment

> **Collection Rate:** {collection_rate:.1f}% indicates moderate coverage.

- {companies_with_reports_count} out of {total_companies} companies have financial reports available
- Most companies have reports spanning {avg_year_span:.1f} years on average
- Majority of data collection focuses on recent years (post-2015)

---

*Report generated by Financial Reports Collection Analysis Tool*
"""
    
    # 保存为markdown文件
    filename = f"collection_status_of_financial_reports_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"报告已保存至: {filename}")
    print("\n报告内容:")
    print(report)

if __name__ == "__main__":
    analyze_reports() 