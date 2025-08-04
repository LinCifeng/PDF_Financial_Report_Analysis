#!/usr/bin/env python3
"""
分析财报下载状态，找出未下载的原因
"""
import csv
import os
from pathlib import Path
from collections import defaultdict

def clean_filename(text):
    """清理文件名中的特殊字符"""
    replacements = {
        ' ': '_', '/': '_', '\\': '_', ':': '_', 
        '*': '', '?': '', '"': '', '<': '', '>': '', 
        '|': '', '(': '', ')': '', ',': '_', '&': '_',
        '\n': '', '\r': '', '\t': '', '（': '(', '）': ')'
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    while '__' in text:
        text = text.replace('__', '_')
    return text.strip('_')

def main():
    project_root = Path(__file__).parent.parent
    csv_path = project_root / 'data' / 'Company_Financial_report.csv'
    reports_dir = project_root / 'data' / 'raw_reports'
    
    # 获取已下载文件
    downloaded_files = set(f.name for f in reports_dir.glob('*') if f.suffix in ['.pdf', '.html'])
    
    # 分析CSV中的所有报告
    stats = defaultdict(int)
    not_downloaded = []
    downloaded = []
    invalid_urls = []
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get('Financial Report(Y/N)') == 'Y':
                stats['total'] += 1
                
                url = row.get('Report_link', '').strip()
                company = row['name']
                year = row['Fiscal_year']
                quarter = row.get('Quarter', '').strip()
                
                # 检查URL有效性
                if not url or url == 'N/A' or url == '#N/A':
                    stats['no_url'] += 1
                    invalid_urls.append({
                        'company': company,
                        'year': year,
                        'quarter': quarter,
                        'reason': 'No URL'
                    })
                    continue
                
                if url.startswith('#'):
                    stats['hash_url'] += 1
                    invalid_urls.append({
                        'company': company,
                        'year': year,
                        'quarter': quarter,
                        'reason': 'URL starts with #'
                    })
                    continue
                
                if not url.startswith('http'):
                    stats['invalid_url'] += 1
                    invalid_urls.append({
                        'company': company,
                        'year': year,
                        'quarter': quarter,
                        'reason': f'Invalid URL: {url[:50]}'
                    })
                    continue
                
                # 有效URL
                stats['valid_urls'] += 1
                
                # 构建预期的文件名
                company_clean = clean_filename(company)
                if quarter and quarter not in ['', 'None', 'nan', 'N/A']:
                    base_name = f"{company_clean}_{year}_{clean_filename(quarter)}"
                else:
                    base_name = f"{company_clean}_{year}_Annual"
                
                # 检查是否已下载
                found = False
                for ext in ['.pdf', '.html']:
                    if f"{base_name}{ext}" in downloaded_files:
                        found = True
                        downloaded.append({
                            'company': company,
                            'year': year,
                            'file': f"{base_name}{ext}"
                        })
                        break
                
                if not found:
                    stats['not_downloaded'] += 1
                    not_downloaded.append({
                        'company': company,
                        'year': year,
                        'quarter': quarter,
                        'url': url,
                        'expected_file': base_name
                    })
                else:
                    stats['downloaded'] += 1
    
    # 打印统计信息
    print("=" * 60)
    print("财报下载状态分析")
    print("=" * 60)
    print(f"\n总体统计:")
    print(f"  CSV中总财报数: {stats['total']}")
    print(f"  有效URL数: {stats['valid_urls']}")
    print(f"  已下载: {stats['downloaded']} ({stats['downloaded']/stats['total']*100:.1f}%)")
    print(f"  未下载: {stats['not_downloaded']}")
    print(f"  无效URL: {stats['total'] - stats['valid_urls']}")
    print(f"    - 无URL: {stats['no_url']}")
    print(f"    - Hash URL: {stats['hash_url']}")
    print(f"    - 其他无效: {stats['invalid_url']}")
    
    print(f"\n实际文件统计:")
    print(f"  目录中的文件数: {len(downloaded_files)}")
    
    # 显示一些未下载的例子
    print(f"\n未下载的前20个报告:")
    for item in not_downloaded[:20]:
        print(f"  {item['company']} {item['year']} - {item['url'][:80]}...")
    
    # 显示无效URL
    print(f"\n无效URL的例子:")
    for item in invalid_urls[:10]:
        print(f"  {item['company']} {item['year']} - {item['reason']}")
    
    # 分析未下载的URL模式
    url_domains = defaultdict(int)
    for item in not_downloaded:
        url = item['url']
        if 'investors' in url:
            url_domains['investor_relations'] += 1
        elif 'ir.' in url:
            url_domains['ir_subdomain'] += 1
        elif '.pdf' in url:
            url_domains['direct_pdf'] += 1
        else:
            url_domains['other'] += 1
    
    print(f"\n未下载URL的模式:")
    for pattern, count in sorted(url_domains.items(), key=lambda x: x[1], reverse=True):
        print(f"  {pattern}: {count}")

if __name__ == "__main__":
    main()