#!/usr/bin/env python3
"""
财报下载覆盖率分析脚本
分析已下载的PDF文件与CSV中财报链接的覆盖情况
"""
import os
import pandas as pd
import glob
from collections import defaultdict
from datetime import datetime

def load_company_reports(csv_path):
    """加载公司财报CSV文件"""
    df = pd.read_csv(csv_path)
    # 只选择有财报的记录 (Financial Report(Y/N) == 'Y')
    df = df[df['Financial Report(Y/N)'] == 'Y']
    return df

def get_downloaded_pdfs(pdf_dir):
    """获取已下载的PDF文件列表"""
    pdf_files = glob.glob(os.path.join(pdf_dir, '*.pdf'))
    return [os.path.basename(f) for f in pdf_files]

def analyze_coverage(df, downloaded_pdfs):
    """分析下载覆盖率"""
    results = {
        'total_companies': len(df['name'].unique()),
        'total_reports': len(df),
        'downloaded_pdfs': len(downloaded_pdfs),
        'company_coverage': {},
        'year_coverage': defaultdict(lambda: {'total': 0, 'downloaded': 0}),
        'missing_reports': [],
        'downloaded_companies': set()
    }
    
    # 分析每家公司的覆盖情况
    for company in df['name'].unique():
        company_reports = df[df['name'] == company]
        company_downloaded = 0
        
        for _, report in company_reports.iterrows():
            year = report['Fiscal_year']
            quarter = report.get('Quarter', '')
            
            # 检查是否已下载（基于公司名和年份的模糊匹配）
            is_downloaded = False
            for pdf in downloaded_pdfs:
                # 标准化公司名（去除空格，统一大小写）
                normalized_company = company.lower().replace(' ', '').replace('bank', '')
                normalized_pdf = pdf.lower().replace('_', '').replace('-', '')
                
                if normalized_company in normalized_pdf and str(year) in pdf:
                    is_downloaded = True
                    company_downloaded += 1
                    results['downloaded_companies'].add(company)
                    break
            
            # 更新年份统计
            results['year_coverage'][year]['total'] += 1
            if is_downloaded:
                results['year_coverage'][year]['downloaded'] += 1
            else:
                # 记录缺失的报告
                results['missing_reports'].append({
                    'company': company,
                    'year': year,
                    'quarter': quarter,
                    'link': report.get('Report_link', '')
                })
        
        # 记录公司覆盖率
        results['company_coverage'][company] = {
            'total': len(company_reports),
            'downloaded': company_downloaded,
            'percentage': (company_downloaded / len(company_reports) * 100) if len(company_reports) > 0 else 0
        }
    
    return results

def print_report(results):
    """打印分析报告"""
    print("=" * 80)
    print("财报下载覆盖率分析报告")
    print("=" * 80)
    print(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 总体统计
    print("【总体统计】")
    print(f"CSV中的公司总数: {results['total_companies']}")
    print(f"CSV中的财报链接总数: {results['total_reports']}")
    print(f"已下载的PDF文件数: {results['downloaded_pdfs']}")
    print(f"已下载财报的公司数: {len(results['downloaded_companies'])}")
    print(f"总体下载比例: {results['downloaded_pdfs']/results['total_reports']*100:.1f}%")
    print(f"公司覆盖比例: {len(results['downloaded_companies'])/results['total_companies']*100:.1f}%")
    print()
    
    # 已下载的公司列表
    print("【已下载财报的公司】")
    for i, company in enumerate(sorted(results['downloaded_companies']), 1):
        coverage = results['company_coverage'][company]
        print(f"{i:2d}. {company:<30} ({coverage['downloaded']}/{coverage['total']} 份, {coverage['percentage']:.0f}%)")
    print()
    
    # 按年份统计
    print("【按年份下载统计】")
    print(f"{'年份':<10} {'总数':<10} {'已下载':<10} {'比例':<10}")
    print("-" * 40)
    for year in sorted(results['year_coverage'].keys()):
        data = results['year_coverage'][year]
        percentage = data['downloaded'] / data['total'] * 100 if data['total'] > 0 else 0
        print(f"{year:<10} {data['total']:<10} {data['downloaded']:<10} {percentage:<10.1f}%")
    print()
    
    # 下载覆盖率最高的公司（Top 10）
    print("【下载覆盖率最高的公司 (Top 10)】")
    sorted_companies = sorted(
        results['company_coverage'].items(),
        key=lambda x: (x[1]['percentage'], x[1]['downloaded']),
        reverse=True
    )[:10]
    
    for i, (company, data) in enumerate(sorted_companies, 1):
        if data['downloaded'] > 0:
            print(f"{i:2d}. {company:<30} {data['downloaded']}/{data['total']} ({data['percentage']:.0f}%)")
    print()
    
    # 完全未下载的公司数量
    not_downloaded = [c for c, d in results['company_coverage'].items() if d['downloaded'] == 0]
    print(f"【完全未下载财报的公司数量】: {len(not_downloaded)} 家")
    print()
    
    # 缺失报告统计（按公司）
    print("【缺失最多的公司 (Top 10)】")
    missing_by_company = defaultdict(int)
    for report in results['missing_reports']:
        missing_by_company[report['company']] += 1
    
    sorted_missing = sorted(missing_by_company.items(), key=lambda x: x[1], reverse=True)[:10]
    for i, (company, count) in enumerate(sorted_missing, 1):
        total = results['company_coverage'][company]['total']
        print(f"{i:2d}. {company:<30} 缺失 {count}/{total} 份")

def main():
    # 项目路径
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    csv_path = os.path.join(project_root, 'data', 'Company_Financial_report.csv')
    pdf_dir = os.path.join(project_root, 'data', 'raw_reports')
    
    # 检查文件是否存在
    if not os.path.exists(csv_path):
        print(f"错误: 找不到CSV文件 {csv_path}")
        return
    
    if not os.path.exists(pdf_dir):
        print(f"错误: 找不到PDF目录 {pdf_dir}")
        return
    
    # 加载数据
    print("正在加载数据...")
    df = load_company_reports(csv_path)
    downloaded_pdfs = get_downloaded_pdfs(pdf_dir)
    
    # 分析覆盖率
    print("正在分析覆盖率...")
    results = analyze_coverage(df, downloaded_pdfs)
    
    # 打印报告
    print_report(results)
    
    # 可选：导出缺失报告列表
    output_dir = os.path.join(project_root, 'output')
    os.makedirs(output_dir, exist_ok=True)
    
    missing_df = pd.DataFrame(results['missing_reports'])
    if not missing_df.empty:
        missing_file = os.path.join(output_dir, 'missing_reports.csv')
        missing_df.to_csv(missing_file, index=False)
        print(f"\n缺失报告列表已保存到: {missing_file}")

if __name__ == "__main__":
    main()