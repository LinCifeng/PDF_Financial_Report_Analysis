#!/usr/bin/env python3
"""
Batch Analysis and Visualization
批量分析和可视化

Author: Lin Cifeng
Date: 2025-08-06
"""
import os
import sys
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import json

# Set project path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import the enhanced extractor
from financial_analysis.extractor import MasterExtractor

# Set matplotlib style
plt.style.use('ggplot')
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 11


def batch_extract_and_analyze(sample_size=100):
    """Extract data from multiple reports and analyze"""
    print("=" * 80)
    print(f"Batch Financial Report Analysis - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # Initialize extractor
    extractor = EnhancedMasterExtractor(use_llm=False)
    
    # Get PDF files
    pdf_dir = project_root / "data/raw_reports"
    pdf_files = list(pdf_dir.glob("*.pdf"))[:sample_size]
    
    print(f"Found {len(pdf_files)} PDF files")
    print(f"Processing {min(sample_size, len(pdf_files))} files...")
    print("-" * 80)
    
    # Extract data
    results = []
    
    for i, pdf_path in enumerate(pdf_files):
        if (i + 1) % 10 == 0:
            print(f"Progress: {i+1}/{len(pdf_files)}")
        
        try:
            # Extract company and year from filename
            filename = pdf_path.stem
            parts = filename.split('_')
            
            company = parts[0] if parts else "Unknown"
            year = None
            for part in parts:
                if part.isdigit() and len(part) == 4:
                    year = int(part)
                    break
            
            # Extract financial data
            result = extractor.extract(str(pdf_path))
            
            # Count extracted fields
            field_count = sum(1 for v in result['data'].values() if v is not None)
            
            # Prepare record
            record = {
                'filename': pdf_path.name,
                'company': company,
                'year': year,
                'total_assets': result['data'].get('total_assets'),
                'total_liabilities': result['data'].get('total_liabilities'),
                'revenue': result['data'].get('revenue'),
                'net_profit': result['data'].get('net_profit'),
                'method': result.get('method', 'unknown'),
                'fields_extracted': field_count,
                'confidence': result.get('confidence', 0)
            }
            
            # Calculate ratios
            if record['total_assets'] and record['total_liabilities']:
                record['debt_ratio'] = record['total_liabilities'] / record['total_assets']
            
            if record['revenue'] and record['net_profit']:
                record['profit_margin'] = record['net_profit'] / record['revenue']
            
            if record['total_assets'] and record['net_profit']:
                record['roa'] = record['net_profit'] / record['total_assets']
            
            results.append(record)
            
        except Exception as e:
            print(f"Error processing {pdf_path.name}: {str(e)[:50]}")
    
    # Create DataFrame
    df = pd.DataFrame(results)
    
    # Save data
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = project_root / "output" / f"batch_analysis_{timestamp}.csv"
    df.to_csv(output_file, index=False)
    print(f"\nData saved to: {output_file}")
    
    return df


def create_comprehensive_visualizations(df):
    """Create visualizations in English"""
    print("\nGenerating visualizations...")
    
    # Create output directory
    viz_dir = project_root / "output" / "visualizations"
    viz_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # 1. Overall Extraction Performance
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    fig.suptitle('Hong Kong Virtual Banks Financial Data Analysis', fontsize=18, fontweight='bold')
    
    # 1.1 Extraction Success by Field
    ax1 = axes[0, 0]
    fields = ['total_assets', 'total_liabilities', 'revenue', 'net_profit']
    success_rates = [(df[field].notna().sum() / len(df) * 100) for field in fields]
    
    bars = ax1.bar(fields, success_rates, color=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728'])
    ax1.set_title('Field Extraction Success Rate', fontsize=14, fontweight='bold')
    ax1.set_ylabel('Success Rate (%)')
    ax1.set_ylim(0, 100)
    
    # Add value labels
    for bar, rate in zip(bars, success_rates):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                f'{rate:.1f}%', ha='center', va='bottom')
    
    # 1.2 Complete Extraction Rate
    ax2 = axes[0, 1]
    extraction_dist = df['fields_extracted'].value_counts().sort_index()
    ax2.bar(extraction_dist.index, extraction_dist.values, color='skyblue', edgecolor='black')
    ax2.set_title('Fields Extracted Distribution', fontsize=14, fontweight='bold')
    ax2.set_xlabel('Number of Fields Extracted')
    ax2.set_ylabel('Number of Reports')
    ax2.set_xticks([0, 1, 2, 3, 4])
    
    # 1.3 Extraction Method Distribution
    ax3 = axes[0, 2]
    method_counts = df['method'].value_counts()
    wedges, texts, autotexts = ax3.pie(method_counts.values, labels=method_counts.index, 
                                       autopct='%1.1f%%', startangle=90)
    ax3.set_title('Extraction Methods Used', fontsize=14, fontweight='bold')
    
    # 2. Financial Metrics Analysis
    
    # 2.1 Assets Distribution
    ax4 = axes[1, 0]
    assets_data = df['total_assets'].dropna() / 1e6  # Convert to millions
    if len(assets_data) > 0:
        ax4.hist(assets_data, bins=20, edgecolor='black', alpha=0.7, color='green')
        ax4.set_title('Total Assets Distribution', fontsize=14, fontweight='bold')
        ax4.set_xlabel('Total Assets (Million HKD)')
        ax4.set_ylabel('Frequency')
        ax4.axvline(assets_data.median(), color='red', linestyle='--', 
                   label=f'Median: {assets_data.median():.1f}M')
        ax4.legend()
    
    # 2.2 Profitability Analysis
    ax5 = axes[1, 1]
    profit_data = df['net_profit'].dropna() / 1e6
    if len(profit_data) > 0:
        profitable = (profit_data > 0).sum()
        unprofitable = (profit_data <= 0).sum()
        
        ax5.bar(['Profitable', 'Loss-making'], [profitable, unprofitable], 
               color=['green', 'red'])
        ax5.set_title('Profitability Distribution', fontsize=14, fontweight='bold')
        ax5.set_ylabel('Number of Banks')
        
        # Add percentage labels
        total = profitable + unprofitable
        ax5.text(0, profitable + 0.5, f'{profitable/total*100:.1f}%', 
                ha='center', va='bottom')
        ax5.text(1, unprofitable + 0.5, f'{unprofitable/total*100:.1f}%', 
                ha='center', va='bottom')
    
    # 2.3 Year-over-Year Trend
    ax6 = axes[1, 2]
    if df['year'].notna().sum() > 5:
        yearly_avg = df.groupby('year')[['total_assets', 'revenue', 'net_profit']].mean() / 1e6
        yearly_avg.plot(ax=ax6, marker='o', linewidth=2)
        ax6.set_title('Average Financial Metrics by Year', fontsize=14, fontweight='bold')
        ax6.set_xlabel('Year')
        ax6.set_ylabel('Amount (Million HKD)')
        ax6.legend(['Total Assets', 'Revenue', 'Net Profit'])
        ax6.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(viz_dir / f'financial_analysis_overview_{timestamp}.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # 3. Company Performance Comparison
    plt.figure(figsize=(14, 10))
    
    # Get top companies by report count
    top_companies = df['company'].value_counts().head(10).index
    company_df = df[df['company'].isin(top_companies)]
    
    if len(company_df) > 0:
        # Calculate average metrics by company
        company_metrics = company_df.groupby('company').agg({
            'total_assets': 'mean',
            'revenue': 'mean',
            'net_profit': 'mean',
            'fields_extracted': 'mean'
        }).dropna()
        
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle('Top 10 Companies Performance Analysis', fontsize=16, fontweight='bold')
        
        # Assets comparison
        ax1 = axes[0, 0]
        if 'total_assets' in company_metrics:
            (company_metrics['total_assets'] / 1e6).plot(kind='barh', ax=ax1, color='blue')
            ax1.set_xlabel('Average Total Assets (Million HKD)')
            ax1.set_title('Total Assets by Company')
        
        # Revenue comparison
        ax2 = axes[0, 1]
        if 'revenue' in company_metrics:
            (company_metrics['revenue'] / 1e6).plot(kind='barh', ax=ax2, color='green')
            ax2.set_xlabel('Average Revenue (Million HKD)')
            ax2.set_title('Revenue by Company')
        
        # Profit comparison
        ax3 = axes[1, 0]
        if 'net_profit' in company_metrics:
            (company_metrics['net_profit'] / 1e6).plot(kind='barh', ax=ax3, color='orange')
            ax3.set_xlabel('Average Net Profit (Million HKD)')
            ax3.set_title('Net Profit by Company')
            ax3.axvline(0, color='black', linestyle='-', linewidth=1)
        
        # Extraction quality
        ax4 = axes[1, 1]
        company_metrics['fields_extracted'].plot(kind='barh', ax=ax4, color='purple')
        ax4.set_xlabel('Average Fields Extracted (out of 4)')
        ax4.set_title('Data Extraction Quality by Company')
        ax4.set_xlim(0, 4)
        
        plt.tight_layout()
        plt.savefig(viz_dir / f'company_comparison_{timestamp}.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    # 4. Generate Summary Report
    generate_summary_report(df, viz_dir / f'analysis_summary_{timestamp}.txt')
    
    print(f"\nVisualizations saved to: {viz_dir}")


def generate_summary_report(df, output_file):
    """Generate text summary report"""
    with open(output_file, 'w') as f:
        f.write("HONG KONG VIRTUAL BANKS FINANCIAL DATA ANALYSIS SUMMARY\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("1. DATA COVERAGE\n")
        f.write("-" * 40 + "\n")
        f.write(f"Total Reports Analyzed: {len(df)}\n")
        f.write(f"Unique Companies: {df['company'].nunique()}\n")
        f.write(f"Year Range: {df['year'].min()} - {df['year'].max()}\n\n")
        
        f.write("2. EXTRACTION PERFORMANCE\n")
        f.write("-" * 40 + "\n")
        for field in ['total_assets', 'total_liabilities', 'revenue', 'net_profit']:
            rate = df[field].notna().sum() / len(df) * 100
            f.write(f"{field.replace('_', ' ').title()}: {rate:.1f}%\n")
        
        complete = (df['fields_extracted'] == 4).sum()
        f.write(f"\nComplete Extraction (4 fields): {complete} ({complete/len(df)*100:.1f}%)\n\n")
        
        f.write("3. FINANCIAL METRICS SUMMARY\n")
        f.write("-" * 40 + "\n")
        
        if df['total_assets'].notna().sum() > 0:
            f.write(f"Average Total Assets: {df['total_assets'].mean()/1e6:.1f}M HKD\n")
            f.write(f"Median Total Assets: {df['total_assets'].median()/1e6:.1f}M HKD\n")
        
        if df['revenue'].notna().sum() > 0:
            f.write(f"Average Revenue: {df['revenue'].mean()/1e6:.1f}M HKD\n")
        
        if df['net_profit'].notna().sum() > 0:
            profitable = (df['net_profit'] > 0).sum()
            total_with_profit = df['net_profit'].notna().sum()
            f.write(f"\nProfitable Banks: {profitable} out of {total_with_profit} ({profitable/total_with_profit*100:.1f}%)\n")
            f.write(f"Average Net Profit: {df['net_profit'].mean()/1e6:.1f}M HKD\n")
        
        f.write("\n4. TOP PERFORMING COMPANIES\n")
        f.write("-" * 40 + "\n")
        
        # Top by assets
        if df['total_assets'].notna().sum() > 0:
            top_assets = df.nlargest(5, 'total_assets')[['company', 'year', 'total_assets']]
            f.write("\nTop 5 by Total Assets:\n")
            for _, row in top_assets.iterrows():
                f.write(f"  {row['company']} ({row['year']}): {row['total_assets']/1e6:.1f}M HKD\n")
        
        # Most profitable
        if df['net_profit'].notna().sum() > 0:
            top_profit = df.nlargest(5, 'net_profit')[['company', 'year', 'net_profit']]
            f.write("\nTop 5 by Net Profit:\n")
            for _, row in top_profit.iterrows():
                f.write(f"  {row['company']} ({row['year']}): {row['net_profit']/1e6:.1f}M HKD\n")


def main():
    """Main execution"""
    # Extract and analyze data
    df = batch_extract_and_analyze(sample_size=100)
    
    # Create visualizations
    if len(df) > 0:
        create_comprehensive_visualizations(df)
        print("\nAnalysis complete!")
    else:
        print("No data extracted.")


if __name__ == "__main__":
    main()