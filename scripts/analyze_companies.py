#!/usr/bin/env python3
"""
Analyze companies with financial reports and create priority list.
分析有财报的公司并创建优先级列表。
"""

import csv
from collections import defaultdict
from pathlib import Path
import json
from datetime import datetime


def analyze_companies(csv_path: str):
    """Analyze companies from CSV and create priority list."""
    
    # Statistics
    company_stats = defaultdict(lambda: {
        'count': 0,
        'years': set(),
        'quarters': 0,
        'has_recent': False,
        'is_bank': False,
        'is_virtual_bank': False,
        'links': []
    })
    
    # Virtual banks in Hong Kong (香港虚拟银行)
    virtual_banks = {
        'ZA Bank', 'weLab Bank', 'Airstar Bank', 'Airstarbank',
        'Ant Bank', 'Fusion Bank', 'Livi Bank', 'Mox Bank', 
        'Ping An OneConnect Bank', 'PingAn OneConnect Bank'
    }
    
    # Read CSV
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            if row.get('Financial Report(Y/N)', '').upper() == 'Y':
                company_name = row.get('name', '').strip()
                year = row.get('Fiscal_year', '')
                quarter = row.get('Quarter', '')
                link = row.get('Report_link', '')
                
                if company_name and year:
                    try:
                        year_int = int(year)
                        stats = company_stats[company_name]
                        stats['count'] += 1
                        stats['years'].add(year_int)
                        
                        if quarter:
                            stats['quarters'] += 1
                        
                        if link:
                            stats['links'].append({
                                'year': year_int,
                                'quarter': quarter,
                                'url': link
                            })
                        
                        # Check if has recent reports (2022-2024)
                        if year_int >= 2022:
                            stats['has_recent'] = True
                        
                        # Check if it's a bank
                        name_lower = company_name.lower()
                        if 'bank' in name_lower or '银行' in company_name:
                            stats['is_bank'] = True
                        
                        # Check if it's a virtual bank
                        if company_name in virtual_banks:
                            stats['is_virtual_bank'] = True
                            
                    except ValueError:
                        pass
    
    # Create priority list
    companies = []
    for name, stats in company_stats.items():
        priority_score = 0
        
        # Virtual banks get highest priority (虚拟银行优先级最高)
        if stats['is_virtual_bank']:
            priority_score += 100
        elif stats['is_bank']:
            priority_score += 50
        
        # Recent reports add priority
        if stats['has_recent']:
            priority_score += 20
        
        # More reports = higher priority
        priority_score += stats['count'] * 2
        
        # Sort links by year
        stats['links'].sort(key=lambda x: (x['year'], x['quarter']), reverse=True)
        
        companies.append({
            'name': name,
            'report_count': stats['count'],
            'annual_reports': stats['count'] - stats['quarters'],
            'interim_reports': stats['quarters'],
            'year_range': f"{min(stats['years'])}-{max(stats['years'])}",
            'has_recent': stats['has_recent'],
            'is_bank': stats['is_bank'],
            'is_virtual_bank': stats['is_virtual_bank'],
            'priority_score': priority_score,
            'latest_reports': stats['links'][:3]  # Keep top 3 recent links
        })
    
    # Sort by priority
    companies.sort(key=lambda x: x['priority_score'], reverse=True)
    
    return companies


def main():
    """Main function."""
    csv_path = Path(__file__).parent.parent / 'data' / 'Company_Financial_report.csv'
    companies = analyze_companies(csv_path)
    
    # Print summary
    print("\n=== 财报公司分析摘要 Company Analysis Summary ===\n")
    print(f"Total companies with reports | 有财报的公司总数: {len(companies)}")
    
    virtual_banks = [c for c in companies if c['is_virtual_bank']]
    print(f"Virtual banks | 虚拟银行: {len(virtual_banks)}")
    
    banks = [c for c in companies if c['is_bank']]
    print(f"All banks | 所有银行: {len(banks)}")
    
    recent = [c for c in companies if c['has_recent']]
    print(f"Companies with recent reports (2022+) | 有近期财报的公司: {len(recent)}")
    
    # Print top 20 priority companies
    print("\n=== Top 20 优先级公司 Priority Companies ===\n")
    print(f"{'Rank':<5} {'Company':<30} {'Reports':<8} {'Years':<12} {'Type':<15} {'Score':<6}")
    print("-" * 80)
    
    for i, company in enumerate(companies[:20], 1):
        company_type = ""
        if company['is_virtual_bank']:
            company_type = "Virtual Bank"
        elif company['is_bank']:
            company_type = "Bank"
        else:
            company_type = "FinTech"
        
        print(f"{i:<5} {company['name']:<30} {company['report_count']:<8} "
              f"{company['year_range']:<12} {company_type:<15} {company['priority_score']:<6}")
    
    # Virtual banks detail
    print("\n=== 虚拟银行详情 Virtual Banks Detail ===\n")
    for vb in virtual_banks:
        print(f"- {vb['name']}: {vb['report_count']} reports ({vb['year_range']})")
    
    # Save to JSON
    output_path = Path(__file__).parent.parent / 'output' / 'company_priority_list.json'
    output_path.parent.mkdir(exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({
            'generated_at': datetime.now().isoformat(),
            'summary': {
                'total_companies': len(companies),
                'virtual_banks': len(virtual_banks),
                'all_banks': len(banks),
                'companies_with_recent_reports': len(recent)
            },
            'virtual_banks': [c for c in companies if c['is_virtual_bank']],
            'top_20_companies': companies[:20],
            'all_companies': companies
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\nFull priority list saved to | 完整优先级列表已保存至: {output_path}")
    
    return companies


if __name__ == '__main__':
    main()