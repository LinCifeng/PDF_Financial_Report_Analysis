#!/usr/bin/env python3
"""
Visualize Existing Extraction Data
可视化现有提取数据

Author: Lin Cifeng
Date: 2025-08-06
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from datetime import datetime


def load_and_merge_data():
    """Load existing CSV files"""
    # Try batch results first (larger dataset)
    batch_dir = Path(__file__).parent.parent / "output/archive/2025-08-06/batch_results"
    
    # Load the largest batch result
    csv_file = batch_dir / "extraction_batch_200_20250806_134440.csv"
    
    if not csv_file.exists():
        print(f"File not found: {csv_file}")
        return None
    
    df = pd.read_csv(csv_file)
    print(f"Loaded {len(df)} records from {csv_file.name}")
    
    # Company and year are already in the dataframe
    # Just ensure they exist
    if 'company' not in df.columns and 'file_name' in df.columns:
        df['company'] = df['file_name'].apply(lambda x: x.split('_')[0] if pd.notna(x) else 'Unknown')
    
    if 'year' not in df.columns and 'file_name' in df.columns:
        def extract_year(filename):
            if pd.isna(filename):
                return None
            parts = filename.split('_')
            for part in parts:
                if part.isdigit() and len(part) == 4:
                    return int(part)
            return None
        
        df['year'] = df['file_name'].apply(extract_year)
    
    return df


def create_comprehensive_visualization(df):
    """Create comprehensive English visualizations"""
    print("\nGenerating visualizations...")
    
    # Output directory
    viz_dir = Path(__file__).parent.parent / "output/visualizations"
    viz_dir.mkdir(exist_ok=True)
    
    # Set style
    plt.style.use('ggplot')
    
    # 1. Main Analysis Dashboard
    fig = plt.figure(figsize=(16, 12))
    
    # Title
    fig.suptitle('Hong Kong Virtual Banks Financial Data Extraction Analysis', 
                 fontsize=18, fontweight='bold')
    
    # 1.1 Extraction Success by Field
    ax1 = plt.subplot(3, 3, 1)
    fields = ['total_assets', 'total_liabilities', 'revenue', 'net_profit']
    field_names = ['Total Assets', 'Total Liabilities', 'Revenue', 'Net Profit']
    
    success_rates = []
    for field in fields:
        if field in df.columns:
            rate = df[field].notna().sum() / len(df) * 100
            success_rates.append(rate)
        else:
            success_rates.append(0)
    
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
    bars = ax1.bar(field_names, success_rates, color=colors)
    ax1.set_title('Field Extraction Success Rates', fontsize=14, fontweight='bold')
    ax1.set_ylabel('Success Rate (%)')
    ax1.set_ylim(0, 100)
    
    # Add value labels
    for bar, rate in zip(bars, success_rates):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                f'{rate:.1f}%', ha='center', va='bottom', fontweight='bold')
    
    # 1.2 Extraction Method Distribution
    ax2 = plt.subplot(3, 3, 2)
    if 'extraction_method' in df.columns:
        method_counts = df['extraction_method'].value_counts()
        ax2.pie(method_counts.values, labels=method_counts.index, autopct='%1.1f%%',
                startangle=90, colors=plt.cm.Set3.colors)
        ax2.set_title('Extraction Methods Used', fontsize=14, fontweight='bold')
    
    # 1.3 Data Completeness
    ax3 = plt.subplot(3, 3, 3)
    
    # Count fields extracted per record
    field_counts = []
    for _, row in df.iterrows():
        count = sum(1 for field in fields if field in df.columns and pd.notna(row.get(field)))
        field_counts.append(count)
    
    df['fields_extracted'] = field_counts
    
    completeness_dist = pd.Series(field_counts).value_counts().sort_index()
    ax3.bar(completeness_dist.index, completeness_dist.values, color='skyblue', edgecolor='black')
    ax3.set_title('Data Completeness Distribution', fontsize=14, fontweight='bold')
    ax3.set_xlabel('Number of Fields Extracted')
    ax3.set_ylabel('Number of Reports')
    ax3.set_xticks([0, 1, 2, 3, 4])
    
    # Add percentage labels
    total = len(df)
    for x, y in zip(completeness_dist.index, completeness_dist.values):
        ax3.text(x, y + 0.5, f'{y/total*100:.1f}%', ha='center', va='bottom')
    
    # 2. Financial Metrics Analysis
    
    # 2.1 Total Assets Distribution
    ax4 = plt.subplot(3, 3, 4)
    if 'total_assets' in df.columns:
        assets = df['total_assets'].dropna()
        if len(assets) > 0:
            assets_millions = assets / 1e6
            ax4.hist(assets_millions, bins=20, edgecolor='black', alpha=0.7, color='green')
            ax4.set_title('Total Assets Distribution', fontsize=14, fontweight='bold')
            ax4.set_xlabel('Total Assets (Million HKD)')
            ax4.set_ylabel('Frequency')
            
            # Add median line
            median_assets = assets_millions.median()
            ax4.axvline(median_assets, color='red', linestyle='--', linewidth=2,
                       label=f'Median: {median_assets:.1f}M')
            ax4.legend()
    
    # 2.2 Revenue Distribution
    ax5 = plt.subplot(3, 3, 5)
    if 'revenue' in df.columns:
        revenue = df['revenue'].dropna()
        if len(revenue) > 0:
            revenue_millions = revenue / 1e6
            ax5.hist(revenue_millions, bins=20, edgecolor='black', alpha=0.7, color='orange')
            ax5.set_title('Revenue Distribution', fontsize=14, fontweight='bold')
            ax5.set_xlabel('Revenue (Million HKD)')
            ax5.set_ylabel('Frequency')
            
            # Add median line
            median_revenue = revenue_millions.median()
            ax5.axvline(median_revenue, color='red', linestyle='--', linewidth=2,
                       label=f'Median: {median_revenue:.1f}M')
            ax5.legend()
    
    # 2.3 Profitability Analysis
    ax6 = plt.subplot(3, 3, 6)
    if 'net_profit' in df.columns:
        profits = df['net_profit'].dropna()
        if len(profits) > 0:
            profitable = (profits > 0).sum()
            unprofitable = (profits <= 0).sum()
            
            labels = ['Profitable', 'Loss-making']
            sizes = [profitable, unprofitable]
            colors = ['green', 'red']
            
            wedges, texts, autotexts = ax6.pie(sizes, labels=labels, colors=colors, 
                                               autopct='%1.1f%%', startangle=90)
            ax6.set_title('Profitability Distribution', fontsize=14, fontweight='bold')
    
    # 3. Company and Time Analysis
    
    # 3.1 Top Companies by Report Count
    ax7 = plt.subplot(3, 3, 7)
    company_counts = df['company'].value_counts().head(10)
    company_counts.plot(kind='barh', ax=ax7, color='purple')
    ax7.set_title('Top 10 Companies by Report Count', fontsize=14, fontweight='bold')
    ax7.set_xlabel('Number of Reports')
    
    # 3.2 Year Distribution
    ax8 = plt.subplot(3, 3, 8)
    if df['year'].notna().sum() > 0:
        year_counts = df['year'].value_counts().sort_index()
        ax8.bar(year_counts.index, year_counts.values, color='teal', edgecolor='black')
        ax8.set_title('Reports by Year', fontsize=14, fontweight='bold')
        ax8.set_xlabel('Year')
        ax8.set_ylabel('Number of Reports')
        plt.xticks(rotation=45)
    
    # 3.3 Extraction Quality by Company
    ax9 = plt.subplot(3, 3, 9)
    company_quality = df.groupby('company')['fields_extracted'].mean().sort_values(ascending=False).head(10)
    company_quality.plot(kind='barh', ax=ax9, color='brown')
    ax9.set_title('Top 10 Companies by Data Quality', fontsize=14, fontweight='bold')
    ax9.set_xlabel('Average Fields Extracted (out of 4)')
    ax9.set_xlim(0, 4)
    
    plt.tight_layout()
    
    # Save figure
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = viz_dir / f'financial_analysis_dashboard_{timestamp}.png'
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"\nVisualization saved to: {output_file}")
    
    # 4. Create Summary Report
    create_summary_report(df, viz_dir)


def create_summary_report(df, output_dir):
    """Create text summary report"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_file = output_dir / f'analysis_summary_{timestamp}.txt'
    
    with open(report_file, 'w') as f:
        f.write("HONG KONG VIRTUAL BANKS FINANCIAL DATA EXTRACTION ANALYSIS\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("1. DATA OVERVIEW\n")
        f.write("-" * 40 + "\n")
        f.write(f"Total Reports Analyzed: {len(df)}\n")
        f.write(f"Unique Companies: {df['company'].nunique()}\n")
        
        if df['year'].notna().sum() > 0:
            f.write(f"Year Range: {df['year'].min():.0f} - {df['year'].max():.0f}\n")
        
        f.write("\n2. EXTRACTION PERFORMANCE\n")
        f.write("-" * 40 + "\n")
        
        fields = ['total_assets', 'total_liabilities', 'revenue', 'net_profit']
        for field in fields:
            if field in df.columns:
                rate = df[field].notna().sum() / len(df) * 100
                f.write(f"{field.replace('_', ' ').title()}: {rate:.1f}%\n")
        
        complete = (df['fields_extracted'] == 4).sum()
        f.write(f"\nComplete Extraction (4 fields): {complete} ({complete/len(df)*100:.1f}%)\n")
        
        f.write("\n3. FINANCIAL METRICS SUMMARY\n")
        f.write("-" * 40 + "\n")
        
        if 'total_assets' in df.columns:
            assets = df['total_assets'].dropna()
            if len(assets) > 0:
                f.write(f"Average Total Assets: {assets.mean()/1e6:.1f}M HKD\n")
                f.write(f"Median Total Assets: {assets.median()/1e6:.1f}M HKD\n")
                f.write(f"Range: {assets.min()/1e6:.1f}M - {assets.max()/1e6:.1f}M HKD\n")
        
        if 'revenue' in df.columns:
            revenue = df['revenue'].dropna()
            if len(revenue) > 0:
                f.write(f"\nAverage Revenue: {revenue.mean()/1e6:.1f}M HKD\n")
                f.write(f"Median Revenue: {revenue.median()/1e6:.1f}M HKD\n")
        
        if 'net_profit' in df.columns:
            profits = df['net_profit'].dropna()
            if len(profits) > 0:
                profitable = (profits > 0).sum()
                f.write(f"\nProfitable Banks: {profitable} out of {len(profits)} ({profitable/len(profits)*100:.1f}%)\n")
                f.write(f"Average Net Profit: {profits.mean()/1e6:.1f}M HKD\n")
                f.write(f"Median Net Profit: {profits.median()/1e6:.1f}M HKD\n")
        
        f.write("\n4. TOP PERFORMING BANKS\n")
        f.write("-" * 40 + "\n")
        
        # Top by assets
        if 'total_assets' in df.columns and df['total_assets'].notna().sum() > 0:
            top_assets = df.nlargest(5, 'total_assets')[['company', 'year', 'total_assets']]
            f.write("\nLargest Banks by Total Assets:\n")
            for _, row in top_assets.iterrows():
                year_str = f"({int(row['year'])})" if pd.notna(row['year']) else ""
                f.write(f"  {row['company']} {year_str}: {row['total_assets']/1e6:.1f}M HKD\n")
        
        # Most profitable
        if 'net_profit' in df.columns and df['net_profit'].notna().sum() > 0:
            top_profit = df.nlargest(5, 'net_profit')[['company', 'year', 'net_profit']]
            f.write("\nMost Profitable Banks:\n")
            for _, row in top_profit.iterrows():
                year_str = f"({int(row['year'])})" if pd.notna(row['year']) else ""
                f.write(f"  {row['company']} {year_str}: {row['net_profit']/1e6:.1f}M HKD\n")
    
    print(f"Summary report saved to: {report_file}")


def main():
    """Main function"""
    # Load data
    df = load_and_merge_data()
    
    if df is not None and len(df) > 0:
        # Create visualizations
        create_comprehensive_visualization(df)
        print("\nAnalysis complete!")
    else:
        print("No data available for visualization.")


if __name__ == "__main__":
    main()