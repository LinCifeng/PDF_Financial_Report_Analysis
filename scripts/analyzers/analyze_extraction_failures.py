#!/usr/bin/env python3
"""
深入分析提取失败原因
Deep Analysis of Extraction Failures

作者: Lin Cifeng
创建时间: 2025-08-06
"""
import pandas as pd
from pathlib import Path
import pdfplumber
import random
from collections import defaultdict


def analyze_failures():
    """分析提取失败的原因"""
    print("=" * 80)
    print("提取失败原因分析")
    print("=" * 80)
    
    # 读取之前的提取结果
    old_results_path = Path("output/final_extraction_20250806_143709.csv")
    if not old_results_path.exists():
        print("未找到提取结果文件")
        return
    
    df = pd.read_csv(old_results_path)
    
    # 统计失败情况
    print("\n1. 整体统计:")
    print("-" * 60)
    total = len(df)
    
    # 按字段统计失败
    fields = ['total_assets', 'total_liabilities', 'revenue', 'net_profit']
    for field in fields:
        success = df[field].notna().sum()
        failed = total - success
        print(f"{field}: 成功 {success}/{total} ({success/total*100:.1f}%), 失败 {failed}")
    
    # 找出各字段都失败的文件
    all_failed = df[df[fields].isna().all(axis=1)]
    print(f"\n完全失败的文件: {len(all_failed)} 个")
    
    # 分析失败模式
    print("\n2. 失败模式分析:")
    print("-" * 60)
    
    failure_categories = {
        'empty_pdf': [],
        'scanned_pdf': [],
        'no_financial_data': [],
        'complex_format': [],
        'extraction_error': []
    }
    
    # 随机抽样分析失败文件
    sample_size = min(20, len(all_failed))
    sample_files = all_failed.sample(n=sample_size) if len(all_failed) > 0 else pd.DataFrame()
    
    for _, row in sample_files.iterrows():
        filename = row['file_name']
        pdf_path = Path("data/raw_reports") / filename
        
        if pdf_path.exists():
            category = analyze_single_failure(pdf_path)
            failure_categories[category].append(filename)
    
    # 打印分类结果
    print("\n失败原因分类:")
    for category, files in failure_categories.items():
        if files:
            print(f"\n{category}: {len(files)} 个")
            for f in files[:3]:
                print(f"  - {f}")
            if len(files) > 3:
                print(f"  ... 还有 {len(files)-3} 个")
    
    # 分析部分成功的案例
    print("\n3. 部分成功案例分析:")
    print("-" * 60)
    
    # 收入提取失败但其他成功
    revenue_fail = df[(df['revenue'].isna()) & (df['total_assets'].notna())]
    print(f"\n仅收入提取失败: {len(revenue_fail)} 个")
    
    # 净利润提取失败但其他成功
    profit_fail = df[(df['net_profit'].isna()) & (df['total_assets'].notna())]
    print(f"仅净利润提取失败: {len(profit_fail)} 个")
    
    # 分析特定公司的失败模式
    print("\n4. 公司特定失败模式:")
    print("-" * 60)
    
    # 按公司分组统计
    company_failures = defaultdict(lambda: {'total': 0, 'failures': defaultdict(int)})
    
    for _, row in df.iterrows():
        company = row.get('company', 'Unknown')
        company_failures[company]['total'] += 1
        
        for field in fields:
            if pd.isna(row[field]):
                company_failures[company]['failures'][field] += 1
    
    # 找出失败率高的公司
    high_failure_companies = []
    for company, stats in company_failures.items():
        total = stats['total']
        if total >= 5:  # 至少5个文件
            avg_failure_rate = sum(stats['failures'].values()) / (total * len(fields)) * 100
            if avg_failure_rate > 50:
                high_failure_companies.append((company, avg_failure_rate, stats))
    
    # 按失败率排序
    high_failure_companies.sort(key=lambda x: x[1], reverse=True)
    
    print("\n失败率高的公司 (>50%):")
    for company, rate, stats in high_failure_companies[:5]:
        print(f"\n{company}: 平均失败率 {rate:.1f}%")
        print(f"  文件数: {stats['total']}")
        for field, count in stats['failures'].items():
            field_rate = count / stats['total'] * 100
            print(f"  {field}: {count}/{stats['total']} ({field_rate:.1f}%)")
    
    # 生成改进建议
    print("\n5. 改进建议:")
    print("-" * 60)
    
    suggestions = generate_improvement_suggestions(failure_categories, company_failures)
    for i, suggestion in enumerate(suggestions, 1):
        print(f"{i}. {suggestion}")


def analyze_single_failure(pdf_path: Path) -> str:
    """分析单个PDF失败的原因"""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            if len(pdf.pages) == 0:
                return 'empty_pdf'
            
            # 检查是否能提取文本
            text_found = False
            financial_keywords = ['assets', 'liabilities', 'revenue', 'profit', 
                                '资产', '负债', '收入', '利润']
            
            for i in range(min(10, len(pdf.pages))):
                text = pdf.pages[i].extract_text()
                if text and len(text.strip()) > 50:
                    text_found = True
                    # 检查是否包含财务关键词
                    if any(kw in text.lower() for kw in financial_keywords):
                        # 有文本有关键词但提取失败，可能是格式复杂
                        return 'complex_format'
            
            if not text_found:
                return 'scanned_pdf'
            else:
                return 'no_financial_data'
                
    except Exception as e:
        return 'extraction_error'


def generate_improvement_suggestions(failure_categories, company_failures):
    """生成改进建议"""
    suggestions = []
    
    # 基于失败类别
    if len(failure_categories['scanned_pdf']) > 5:
        suggestions.append(
            "发现大量扫描版PDF，建议：\n"
            "   - 集成OCR功能（如Tesseract或PaddleOCR）\n"
            "   - 优先处理文本版PDF\n"
            "   - 考虑从源头获取电子版报告"
        )
    
    if len(failure_categories['complex_format']) > 5:
        suggestions.append(
            "发现复杂格式的报告，建议：\n"
            "   - 为每家公司建立专门的提取模板\n"
            "   - 增强表格识别算法\n"
            "   - 使用机器学习训练格式识别模型"
        )
    
    if len(failure_categories['empty_pdf']) > 0:
        suggestions.append(
            "发现空PDF文件，建议：\n"
            "   - 运行PDF修复工具重新下载\n"
            "   - 检查下载过程是否有问题\n"
            "   - 建立下载验证机制"
        )
    
    # 基于公司特定问题
    high_failure_companies = []
    for company, stats in company_failures.items():
        if stats['total'] >= 5:
            avg_failure = sum(stats['failures'].values()) / (stats['total'] * 4) * 100
            if avg_failure > 70:
                high_failure_companies.append(company)
    
    if high_failure_companies:
        suggestions.append(
            f"以下公司失败率极高：{', '.join(high_failure_companies[:3])}\n"
            "   建议为这些公司开发专门的提取策略"
        )
    
    # 字段特定建议
    suggestions.append(
        "优化收入(Revenue)提取：\n"
        "   - 增加更多收入相关的模式（营业额、销售收入、服务收入等）\n"
        "   - 特别关注银行的利息收入、手续费收入\n"
        "   - 处理多种语言表述（中英文混合）"
    )
    
    suggestions.append(
        "优化净利润(Net Profit)提取：\n"
        "   - 正确识别亏损（负数、括号表示）\n"
        "   - 区分税前利润和净利润\n"
        "   - 处理'综合收益'等替代指标"
    )
    
    return suggestions


if __name__ == "__main__":
    analyze_failures()