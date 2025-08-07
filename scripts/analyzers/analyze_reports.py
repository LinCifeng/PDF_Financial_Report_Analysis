#!/usr/bin/env python3
"""
Analyze Financial Reports with Visualizations
分析财报并生成可视化

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
import warnings
warnings.filterwarnings('ignore')

# Set project path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import extractor
from scripts.enhanced_master_extractor import EnhancedMasterExtractor

# Configure matplotlib
plt.style.use('default')
plt.rcParams['figure.figsize'] = (10, 6)
plt.rcParams['font.size'] = 10


def extract_and_analyze(limit=50):
    """Extract financial data and analyze"""
    print("=" * 80)
    print(f"Financial Report Analysis - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # Initialize extractor
    extractor = EnhancedMasterExtractor(use_llm=False)
    
    # Get PDF files
    pdf_dir = project_root / "data/raw_reports"
    pdf_files = list(pdf_dir.glob("*.pdf"))[:limit]
    
    print(f"Processing {len(pdf_files)} PDF files...")
    
    results = []
    success_count = 0
    
    for i, pdf_path in enumerate(pdf_files):
        if (i + 1) % 10 == 0:
            print(f"Progress: {i+1}/{len(pdf_files)}")
        
        try:
            # Extract data
            result = extractor.extract(str(pdf_path))
            
            # Parse filename
            filename = pdf_path.stem
            parts = filename.split('_')
            company = parts[0] if parts else "Unknown"
            
            # Find year
            year = None
            for part in parts:
                if part.isdigit() and len(part) == 4:
                    year = int(part)
                    break
            
            # Create record
            record = {
                'company': company,
                'year': year,
                'total_assets': result['data'].get('total_assets'),
                'total_liabilities': result['data'].get('total_liabilities'),
                'revenue': result['data'].get('revenue'),
                'net_profit': result['data'].get('net_profit'),
                'method': result.get('method', 'unknown')
            }
            
            # Count fields
            fields_count = sum(1 for v in [record['total_assets'], record['total_liabilities'], 
                                          record['revenue'], record['net_profit']] if v is not None)
            record['fields_extracted'] = fields_count
            
            if fields_count > 0:
                success_count += 1
            
            results.append(record)
            
        except Exception as e:
            print(f"Error with {pdf_path.name}: {str(e)[:50]}")
            continue
    
    # Create DataFrame
    df = pd.DataFrame(results)
    
    # Save results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = project_root / "output" / f"analysis_results_{timestamp}.csv"
    df.to_csv(output_file, index=False)
    
    print(f"\nProcessed: {len(results)} files")
    print(f"Success: {success_count} files")
    print(f"Results saved to: {output_file}")
    
    return df


def create_visualizations(df):
    """Create English visualizations"""
    print("\nCreating visualizations...")
    
    # Create output directory
    viz_dir = project_root / "output" / "visualizations"
    viz_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # 1. Extraction Success Analysis
    fig = plt.figure(figsize=(15, 10))
    
    # 1.1 Field extraction rates
    ax1 = plt.subplot(2, 3, 1)
    fields = ['total_assets', 'total_liabilities', 'revenue', 'net_profit']
    rates = [df[field].notna().sum() / len(df) * 100 for field in fields]
    
    bars = ax1.bar(fields, rates, color=['blue', 'orange', 'green', 'red'])
    ax1.set_title('Extraction Success Rate by Field')
    ax1.set_ylabel('Success Rate (%)')
    ax1.set_ylim(0, 100)
    
    for bar, rate in zip(bars, rates):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                f'{rate:.1f}%', ha='center', va='bottom')
    
    # 1.2 Complete extraction distribution
    ax2 = plt.subplot(2, 3, 2)
    extraction_counts = df['fields_extracted'].value_counts().sort_index()
    ax2.bar(extraction_counts.index, extraction_counts.values, color='skyblue')
    ax2.set_title('Number of Fields Extracted')
    ax2.set_xlabel('Fields Count')
    ax2.set_ylabel('Number of Reports')
    ax2.set_xticks([0, 1, 2, 3, 4])
    
    # 1.3 Method distribution
    ax3 = plt.subplot(2, 3, 3)
    method_counts = df['method'].value_counts()
    ax3.pie(method_counts.values, labels=method_counts.index, autopct='%1.1f%%')
    ax3.set_title('Extraction Methods Used')
    
    # 2. Financial Analysis
    
    # 2.1 Assets distribution
    ax4 = plt.subplot(2, 3, 4)
    assets = df['total_assets'].dropna()
    if len(assets) > 0:
        ax4.hist(assets / 1e6, bins=20, edgecolor='black', alpha=0.7)
        ax4.set_title('Total Assets Distribution')
        ax4.set_xlabel('Million HKD')
        ax4.set_ylabel('Count')
    
    # 2.2 Profitability
    ax5 = plt.subplot(2, 3, 5)
    profits = df['net_profit'].dropna()
    if len(profits) > 0:
        profitable = (profits > 0).sum()
        unprofitable = (profits <= 0).sum()
        ax5.bar(['Profitable', 'Loss-making'], [profitable, unprofitable], 
               color=['green', 'red'])
        ax5.set_title('Profitability Distribution')
        ax5.set_ylabel('Number of Banks')
    
    # 2.3 Top companies by extraction quality
    ax6 = plt.subplot(2, 3, 6)
    company_quality = df.groupby('company')['fields_extracted'].mean().sort_values(ascending=False).head(10)
    company_quality.plot(kind='barh', ax=ax6)
    ax6.set_title('Top 10 Companies by Data Quality')
    ax6.set_xlabel('Average Fields Extracted')
    
    plt.tight_layout()
    plt.savefig(viz_dir / f'analysis_overview_{timestamp}.png', dpi=150, bbox_inches='tight')
    plt.close()
    
    # 3. Summary statistics
    print("\nSUMMARY STATISTICS")
    print("-" * 40)
    print(f"Total reports: {len(df)}")
    print(f"Unique companies: {df['company'].nunique()}")
    
    print("\nExtraction rates:")
    for field in fields:
        rate = df[field].notna().sum() / len(df) * 100
        print(f"  {field}: {rate:.1f}%")
    
    complete = (df['fields_extracted'] == 4).sum()
    print(f"\nComplete extraction: {complete} ({complete/len(df)*100:.1f}%)")
    
    if len(assets) > 0:
        print(f"\nAverage total assets: {assets.mean()/1e6:.1f}M HKD")
    
    if len(profits) > 0:
        profitable_pct = (profits > 0).sum() / len(profits) * 100
        print(f"Profitable banks: {profitable_pct:.1f}%")
    
    print(f"\nVisualizations saved to: {viz_dir}")


def main():
    """Main function"""
    # Extract data
    df = extract_and_analyze(limit=50)
    
    # Create visualizations
    if len(df) > 0:
        create_visualizations(df)
        print("\nAnalysis complete!")
    else:
        print("No data extracted.")


if __name__ == "__main__":
    main()