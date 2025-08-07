#!/usr/bin/env python3
"""
Final Financial Analysis and Visualization
最终财务分析和可视化

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

# Set project path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import the enhanced extractor
from scripts.enhanced_master_extractor import EnhancedMasterExtractor

# Configure matplotlib
plt.style.use('default')
plt.rcParams['figure.figsize'] = (12, 8)


def quick_extract_sample(sample_size=30):
    """Quick extraction of sample data"""
    print("=" * 80)
    print(f"Financial Report Quick Analysis - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    extractor = EnhancedMasterExtractor(use_llm=False)
    
    # Get sample files
    pdf_dir = project_root / "data/raw_reports"
    pdf_files = list(pdf_dir.glob("*.pdf"))[:sample_size]
    
    print(f"Processing {len(pdf_files)} files...")
    
    results = []
    for i, pdf_path in enumerate(pdf_files):
        print(f"\r[{i+1}/{len(pdf_files)}] {pdf_path.name[:40]}...", end="", flush=True)
        
        try:
            result = extractor.extract(str(pdf_path))
            
            # Parse filename
            parts = pdf_path.stem.split('_')
            company = parts[0]
            year = None
            for part in parts:
                if part.isdigit() and len(part) == 4:
                    year = int(part)
                    break
            
            record = {
                'Company': company,
                'Year': year,
                'Total Assets': result['data'].get('total_assets'),
                'Total Liabilities': result['data'].get('total_liabilities'),
                'Revenue': result['data'].get('revenue'),
                'Net Profit': result['data'].get('net_profit')
            }
            
            results.append(record)
        except:
            continue
    
    print("\nExtraction complete!")
    return pd.DataFrame(results)


def create_final_visualization(df):
    """Create final English visualization"""
    print("\nGenerating final visualization...")
    
    # Create figure
    fig = plt.figure(figsize=(16, 10))
    fig.suptitle('Hong Kong Virtual Banks Financial Analysis', fontsize=20, fontweight='bold')
    
    # 1. Extraction Success
    ax1 = plt.subplot(2, 3, 1)
    fields = ['Total Assets', 'Total Liabilities', 'Revenue', 'Net Profit']
    success_rates = [(df[field].notna().sum() / len(df) * 100) for field in fields]
    
    colors = ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D']
    bars = ax1.bar(fields, success_rates, color=colors)
    ax1.set_title('Data Extraction Success Rate', fontsize=14)
    ax1.set_ylabel('Success Rate (%)')
    ax1.set_ylim(0, 100)
    
    for bar, rate in zip(bars, success_rates):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2,
                f'{rate:.0f}%', ha='center', fontweight='bold')
    
    # 2. Total Assets Distribution
    ax2 = plt.subplot(2, 3, 2)
    assets_data = df['Total Assets'].dropna() / 1e6  # Convert to millions
    if len(assets_data) > 0:
        ax2.hist(assets_data, bins=15, color='#2E86AB', edgecolor='black', alpha=0.7)
        ax2.set_title('Total Assets Distribution', fontsize=14)
        ax2.set_xlabel('Million HKD')
        ax2.set_ylabel('Count')
        ax2.axvline(assets_data.median(), color='red', linestyle='--', 
                   label=f'Median: {assets_data.median():.0f}M')
        ax2.legend()
    
    # 3. Profitability
    ax3 = plt.subplot(2, 3, 3)
    profits = df['Net Profit'].dropna()
    if len(profits) > 0:
        profitable = (profits > 0).sum()
        unprofitable = (profits <= 0).sum()
        
        labels = ['Profitable', 'Loss-making']
        sizes = [profitable, unprofitable]
        colors = ['#27AE60', '#E74C3C']
        
        wedges, texts, autotexts = ax3.pie(sizes, labels=labels, colors=colors,
                                           autopct='%1.0f%%', startangle=90)
        ax3.set_title('Profitability Distribution', fontsize=14)
    
    # 4. Top Companies by Assets
    ax4 = plt.subplot(2, 3, 4)
    top_companies = df.groupby('Company')['Total Assets'].mean().dropna().sort_values(ascending=False).head(8)
    if len(top_companies) > 0:
        top_companies_millions = top_companies / 1e6
        top_companies_millions.plot(kind='barh', ax=ax4, color='#3498DB')
        ax4.set_title('Top Companies by Average Assets', fontsize=14)
        ax4.set_xlabel('Million HKD')
    
    # 5. Year Trend
    ax5 = plt.subplot(2, 3, 5)
    if df['Year'].notna().sum() > 5:
        yearly_avg = df.groupby('Year')['Total Assets'].mean().dropna() / 1e6
        yearly_avg.plot(ax=ax5, marker='o', linewidth=2, markersize=8, color='#E67E22')
        ax5.set_title('Average Total Assets by Year', fontsize=14)
        ax5.set_xlabel('Year')
        ax5.set_ylabel('Million HKD')
        ax5.grid(True, alpha=0.3)
    
    # 6. Summary Statistics
    ax6 = plt.subplot(2, 3, 6)
    ax6.axis('off')
    
    summary_text = f"""SUMMARY STATISTICS
    
Total Reports: {len(df)}
Companies: {df['Company'].nunique()}

Extraction Rates:
  • Total Assets: {df['Total Assets'].notna().sum() / len(df) * 100:.0f}%
  • Revenue: {df['Revenue'].notna().sum() / len(df) * 100:.0f}%
  • Net Profit: {df['Net Profit'].notna().sum() / len(df) * 100:.0f}%

Financial Metrics:
  • Avg Assets: {df['Total Assets'].mean() / 1e6:.0f}M HKD
  • Avg Revenue: {df['Revenue'].mean() / 1e6:.0f}M HKD
  • Profitable: {(df['Net Profit'] > 0).sum() / df['Net Profit'].notna().sum() * 100:.0f}%"""
    
    ax6.text(0.1, 0.9, summary_text, transform=ax6.transAxes,
             fontsize=12, verticalalignment='top', fontfamily='monospace',
             bbox=dict(boxstyle='round', facecolor='lightgray', alpha=0.5))
    
    plt.tight_layout()
    
    # Save
    output_dir = project_root / "output"
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = output_dir / f'final_financial_analysis_{timestamp}.png'
    plt.savefig(output_file, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    
    print(f"Visualization saved to: {output_file}")
    
    # Save data
    data_file = output_dir / f'financial_data_{timestamp}.csv'
    df.to_csv(data_file, index=False)
    print(f"Data saved to: {data_file}")


def main():
    """Main execution"""
    # Extract sample data
    df = quick_extract_sample(sample_size=30)
    
    # Create visualization
    if len(df) > 0:
        create_final_visualization(df)
        print("\nAnalysis complete!")
    else:
        print("No data extracted.")


if __name__ == "__main__":
    main()