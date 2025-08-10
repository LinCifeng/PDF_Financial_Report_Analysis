"""
数据分析模块
Data Analysis Module
"""
import csv
import json
from pathlib import Path
from typing import Dict, List, Optional
from collections import defaultdict
import pandas as pd
import numpy as np


class Analyzer:
    """数据分析器"""
    
    def __init__(self):
        self.results = {}
    
    def analyze(self, data: pd.DataFrame) -> Dict:
        """分析数据"""
        return self.analyze_extraction_results(data)
    
    def generate_report(self, stats: Dict, output_path: Optional[str] = None) -> str:
        """生成分析报告"""
        if output_path:
            output_file = Path(output_path) / f"analysis_report_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(stats, f, ensure_ascii=False, indent=2)
            return str(output_file)
        return json.dumps(stats, ensure_ascii=False, indent=2)


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
        raise ValueError(f"Unknown task: {task}")#!/usr/bin/env python3
"""
数据分析工具
Data Analysis Tool

作者: Lin Cifeng
创建时间: 2025-08-06

提供全面的统计分析和可视化报告
"""
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import json
from datetime import datetime
import matplotlib.pyplot as plt
from collections import defaultdict

# 设置英文显示
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial']
plt.rcParams['axes.unicode_minus'] = False


class DataAnalyzer:
    """数据分析器"""
    
    def __init__(self):
        # 定义字段分类
        self.field_categories = {
            'core': ['total_assets', 'total_liabilities', 'revenue', 'net_profit'],
            'balance_sheet': ['total_assets', 'total_liabilities', 'total_equity', 
                            'cash_and_equivalents', 'loans_and_advances', 'customer_deposits'],
            'income_statement': ['revenue', 'net_profit', 'operating_expenses', 'ebit',
                               'interest_income', 'net_interest_income', 'fee_income'],
            'cash_flow': ['operating_cash_flow', 'investing_cash_flow', 'financing_cash_flow']
        }
        
        # 所有字段
        self.all_fields = list(set(sum(self.field_categories.values(), [])))
    
    def analyze_extraction_results(self, results_df: pd.DataFrame) -> Dict[str, Any]:
        """
        分析提取结果
        
        Returns:
            包含各种统计信息的字典
        """
        analysis = {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'total_files': len(results_df),
            'overall_statistics': self._calculate_overall_stats(results_df),
            'field_statistics': self._calculate_field_stats(results_df),
            'company_statistics': self._calculate_company_stats(results_df),
            'method_statistics': self._calculate_method_stats(results_df),
            'quality_metrics': self._calculate_quality_metrics(results_df),
            'recommendations': self._generate_recommendations(results_df)
        }
        
        return analysis
    
    def _calculate_overall_stats(self, df: pd.DataFrame) -> Dict:
        """计算整体统计"""
        stats = {
            'total_files': len(df),
            'extraction_success': 0,
            'extraction_failed': 0,
            'empty_pdf': 0,
            'average_confidence': 0,
            'average_completeness': 0
        }
        
        if 'extraction_status' in df:
            status_counts = df['extraction_status'].value_counts()
            stats['extraction_success'] = status_counts.get('success', 0)
            stats['extraction_failed'] = status_counts.get('failed', 0)
            stats['empty_pdf'] = status_counts.get('empty_pdf', 0)
        
        if 'confidence' in df:
            stats['average_confidence'] = df['confidence'].mean()
        
        if 'data_completeness' in df:
            stats['average_completeness'] = df['data_completeness'].mean()
        
        # 计算成功率
        if stats['total_files'] > 0:
            stats['success_rate'] = stats['extraction_success'] / stats['total_files'] * 100
            stats['failure_rate'] = stats['extraction_failed'] / stats['total_files'] * 100
            stats['empty_rate'] = stats['empty_pdf'] / stats['total_files'] * 100
        
        return stats
    
    def _calculate_field_stats(self, df: pd.DataFrame) -> Dict:
        """计算各字段统计"""
        field_stats = {}
        
        for field in self.all_fields:
            if field in df.columns:
                non_null = df[field].notna().sum()
                extraction_rate = non_null / len(df) * 100 if len(df) > 0 else 0
                
                field_stats[field] = {
                    'extracted_count': non_null,
                    'extraction_rate': extraction_rate,
                    'category': self._get_field_category(field)
                }
                
                # 如果是数值字段，计算统计信息
                if non_null > 0 and pd.api.types.is_numeric_dtype(df[field]):
                    field_stats[field].update({
                        'mean': df[field].mean(),
                        'median': df[field].median(),
                        'std': df[field].std(),
                        'min': df[field].min(),
                        'max': df[field].max()
                    })
        
        return field_stats
    
    def _calculate_company_stats(self, df: pd.DataFrame) -> Dict:
        """计算公司层面统计"""
        if 'company' not in df:
            return {}
        
        company_stats = {}
        
        for company in df['company'].unique():
            if pd.isna(company):
                continue
                
            company_df = df[df['company'] == company]
            
            stats = {
                'total_files': len(company_df),
                'success_count': len(company_df[company_df['extraction_status'] == 'success']) 
                                if 'extraction_status' in company_df else 0,
                'field_extraction_rates': {}
            }
            
            # 计算各字段提取率
            for field in self.field_categories['core']:
                if field in company_df:
                    rate = company_df[field].notna().sum() / len(company_df) * 100
                    stats['field_extraction_rates'][field] = rate
            
            # 计算完整提取率
            if all(f in company_df for f in self.field_categories['core']):
                complete = company_df[self.field_categories['core']].notna().all(axis=1).sum()
                stats['complete_extraction_rate'] = complete / len(company_df) * 100
            
            company_stats[company] = stats
        
        return company_stats
    
    def _calculate_method_stats(self, df: pd.DataFrame) -> Dict:
        """计算提取方法统计"""
        if 'extraction_method' not in df:
            return {}
        
        method_counts = df['extraction_method'].value_counts()
        
        method_stats = {}
        for method, count in method_counts.items():
            if pd.isna(method):
                continue
                
            method_df = df[df['extraction_method'] == method]
            
            stats = {
                'count': count,
                'percentage': count / len(df) * 100,
                'average_confidence': method_df['confidence'].mean() if 'confidence' in method_df else 0,
                'average_completeness': method_df['data_completeness'].mean() 
                                      if 'data_completeness' in method_df else 0
            }
            
            method_stats[method] = stats
        
        return method_stats
    
    def _calculate_quality_metrics(self, df: pd.DataFrame) -> Dict:
        """计算质量指标"""
        metrics = {
            'high_confidence_rate': 0,  # 高置信度（>80%）的比例
            'complete_extraction_rate': 0,  # 完整提取的比例
            'data_consistency': 0  # 数据一致性评分
        }
        
        if 'confidence' in df:
            high_confidence = df[df['confidence'] > 80]
            metrics['high_confidence_rate'] = len(high_confidence) / len(df) * 100
        
        # 计算完整提取率
        core_fields = self.field_categories['core']
        if all(f in df for f in core_fields):
            complete = df[core_fields].notna().all(axis=1).sum()
            metrics['complete_extraction_rate'] = complete / len(df) * 100
        
        # 计算数据一致性（这里简化处理）
        if 'validation_status' in df:
            consistent = df[df['validation_status'] == 'consistent']
            metrics['data_consistency'] = len(consistent) / len(df) * 100
        
        return metrics
    
    def _get_field_category(self, field: str) -> str:
        """获取字段类别"""
        for category, fields in self.field_categories.items():
            if field in fields:
                return category
        return 'other'
    
    def _generate_recommendations(self, df: pd.DataFrame) -> List[str]:
        """生成改进建议"""
        recommendations = []
        
        # 基于整体成功率
        if 'extraction_status' in df:
            success_rate = len(df[df['extraction_status'] == 'success']) / len(df) * 100
            if success_rate < 50:
                recommendations.append("整体提取成功率低于50%，建议优化提取算法")
        
        # 基于字段提取率
        field_stats = self._calculate_field_stats(df)
        for field, stats in field_stats.items():
            if stats['extraction_rate'] < 30 and field in self.field_categories['core']:
                recommendations.append(f"{field}提取率仅{stats['extraction_rate']:.1f}%，需要重点优化")
        
        # 基于空PDF率
        if 'extraction_status' in df:
            empty_rate = len(df[df['extraction_status'] == 'empty_pdf']) / len(df) * 100
            if empty_rate > 20:
                recommendations.append(f"空PDF文件占{empty_rate:.1f}%，建议检查下载流程并重新下载")
        
        # 基于公司差异
        company_stats = self._calculate_company_stats(df)
        for company, stats in company_stats.items():
            if stats.get('complete_extraction_rate', 100) < 20:
                recommendations.append(f"{company}的完整提取率极低，建议开发专门的提取策略")
        
        return recommendations
    
    def generate_visualization_report(self, analysis: Dict, output_dir: str = "output"):
        """生成可视化报告"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 创建图表
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('财务数据提取分析报告', fontsize=16)
        
        # 1. 整体成功率饼图
        if 'overall_statistics' in analysis:
            stats = analysis['overall_statistics']
            labels = ['成功', '失败', '空PDF']
            sizes = [stats.get('extraction_success', 0),
                    stats.get('extraction_failed', 0),
                    stats.get('empty_pdf', 0)]
            
            axes[0, 0].pie(sizes, labels=labels, autopct='%1.1f%%')
            axes[0, 0].set_title('提取状态分布')
        
        # 2. 字段提取率柱状图
        if 'field_statistics' in analysis:
            field_data = []
            for field, stats in analysis['field_statistics'].items():
                if field in self.field_categories['core']:
                    field_data.append((field, stats['extraction_rate']))
            
            if field_data:
                fields, rates = zip(*field_data)
                axes[0, 1].bar(fields, rates)
                axes[0, 1].set_title('核心字段提取率')
                axes[0, 1].set_ylabel('提取率 (%)')
                axes[0, 1].set_xticklabels(fields, rotation=45)
        
        # 3. 公司提取率对比
        if 'company_statistics' in analysis:
            companies = []
            complete_rates = []
            
            for company, stats in analysis['company_statistics'].items():
                if 'complete_extraction_rate' in stats:
                    companies.append(company)
                    complete_rates.append(stats['complete_extraction_rate'])
            
            if companies:
                axes[1, 0].bar(companies, complete_rates)
                axes[1, 0].set_title('各公司完整提取率')
                axes[1, 0].set_ylabel('完整提取率 (%)')
                axes[1, 0].set_xticklabels(companies, rotation=45)
        
        # 4. 提取方法分布
        if 'method_statistics' in analysis:
            methods = list(analysis['method_statistics'].keys())
            counts = [stats['count'] for stats in analysis['method_statistics'].values()]
            
            if methods:
                axes[1, 1].bar(methods, counts)
                axes[1, 1].set_title('提取方法使用频次')
                axes[1, 1].set_ylabel('使用次数')
        
        plt.tight_layout()
        
        # 保存图表
        chart_file = output_path / f"analysis_charts_{timestamp}.png"
        plt.savefig(chart_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        # 生成文本报告
        report_file = output_path / f"analysis_report_{timestamp}.md"
        self._generate_text_report(analysis, report_file)
        
        print(f"\n分析报告已生成:")
        print(f"  - 图表: {chart_file}")
        print(f"  - 文本报告: {report_file}")
    
    def _generate_text_report(self, analysis: Dict, output_file: Path):
        """生成文本报告"""
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("# 财务数据提取分析报告\n\n")
            f.write(f"生成时间: {analysis['timestamp']}\n\n")
            
            # 整体统计
            f.write("## 一、整体统计\n\n")
            stats = analysis['overall_statistics']
            f.write(f"- 总文件数: {stats['total_files']}\n")
            f.write(f"- 提取成功: {stats['extraction_success']} ({stats.get('success_rate', 0):.1f}%)\n")
            f.write(f"- 提取失败: {stats['extraction_failed']} ({stats.get('failure_rate', 0):.1f}%)\n")
            f.write(f"- 空PDF: {stats['empty_pdf']} ({stats.get('empty_rate', 0):.1f}%)\n")
            f.write(f"- 平均置信度: {stats['average_confidence']:.1f}%\n")
            f.write(f"- 平均完整度: {stats['average_completeness']:.1f}%\n\n")
            
            # 字段统计
            f.write("## 二、字段提取统计\n\n")
            f.write("| 字段 | 提取率 | 类别 |\n")
            f.write("|------|--------|------|\n")
            
            for field, stats in sorted(analysis['field_statistics'].items(), 
                                      key=lambda x: x[1]['extraction_rate'], reverse=True):
                f.write(f"| {field} | {stats['extraction_rate']:.1f}% | {stats['category']} |\n")
            
            # 质量指标
            f.write("\n## 三、质量指标\n\n")
            metrics = analysis['quality_metrics']
            f.write(f"- 高置信度率: {metrics['high_confidence_rate']:.1f}%\n")
            f.write(f"- 完整提取率: {metrics['complete_extraction_rate']:.1f}%\n")
            f.write(f"- 数据一致性: {metrics['data_consistency']:.1f}%\n\n")
            
            # 改进建议
            f.write("## 四、改进建议\n\n")
            for i, rec in enumerate(analysis['recommendations'], 1):
                f.write(f"{i}. {rec}\n")


def test_analyzer():
    """测试分析器"""
    analyzer = DataAnalyzer()
    
    # 创建测试数据
    test_data = {
        'filename': ['file1.pdf', 'file2.pdf', 'file3.pdf', 'file4.pdf', 'file5.pdf'],
        'company': ['CompanyA', 'CompanyA', 'CompanyB', 'CompanyB', 'CompanyC'],
        'extraction_status': ['success', 'success', 'failed', 'empty_pdf', 'success'],
        'extraction_method': ['regex', 'llm', None, None, 'mixed'],
        'confidence': [85, 92, 0, 0, 78],
        'data_completeness': [100, 75, 0, 0, 50],
        'total_assets': [1000000, 2000000, None, None, 1500000],
        'total_liabilities': [600000, 1200000, None, None, 900000],
        'revenue': [100000, None, None, None, 150000],
        'net_profit': [20000, 30000, None, None, None]
    }
    
    df = pd.DataFrame(test_data)
    
    print("测试数据分析器")
    print("-" * 60)
    
    # 分析数据
    analysis = analyzer.analyze_extraction_results(df)
    
    # 打印部分结果
    print(f"\n总文件数: {analysis['overall_statistics']['total_files']}")
    print(f"成功率: {analysis['overall_statistics'].get('success_rate', 0):.1f}%")
    
    print("\n字段提取率:")
    for field, stats in analysis['field_statistics'].items():
        if field in analyzer.field_categories['core']:
            print(f"  {field}: {stats['extraction_rate']:.1f}%")
    
    # 生成报告
    analyzer.generate_visualization_report(analysis)


if __name__ == "__main__":
    test_analyzer()