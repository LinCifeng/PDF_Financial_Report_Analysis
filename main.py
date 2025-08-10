#!/usr/bin/env python3
"""
财务分析系统主入口
Financial Analysis System Main Entry Point

作者: Lin Cifeng
版本: 3.0
"""
import argparse
import sys
from pathlib import Path

# 导入核心模块
from financial_analysis.download import batch_download
from financial_analysis.extractor import MasterExtractor
from financial_analysis.analysis import analyze_extraction_results
from financial_analysis.visualization import create_charts
from financial_analysis.utils import clean_pdfs, generate_summary

# 为了向后兼容，保留旧的接口
from financial_analysis.extractor.regex_extractor import extract_financial_data
from financial_analysis.download.downloader import download_reports
from financial_analysis.analysis.analyzer import analyze_data


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='财务分析系统 - Financial Analysis System v3.0',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # 下载财报
  python main.py download
  python main.py download --limit 100
  
  # 提取数据
  python main.py extract
  python main.py extract --limit 50
  
  # 分析数据
  python main.py analyze
  python main.py analyze --type extraction
  
  # 工具功能
  python main.py utils --clean-pdfs
  python main.py utils --summary
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 下载命令
    download_parser = subparsers.add_parser('download', help='下载财报')
    download_parser.add_argument('--limit', type=int, help='限制下载数量')
    download_parser.add_argument('--workers', type=int, default=5, help='并发下载数')
    
    # 提取命令
    extract_parser = subparsers.add_parser('extract', help='提取财务数据')
    extract_parser.add_argument('--limit', type=int, help='限制处理文件数')
    extract_parser.add_argument('--batch-size', type=int, default=100, help='批处理大小')
    extract_parser.add_argument('--use-llm', action='store_true', help='使用LLM增强提取')
    extract_parser.add_argument('--method', choices=['regex', 'master'], default='regex', help='提取方法')
    
    # 分析命令
    analyze_parser = subparsers.add_parser('analyze', help='分析数据')
    analyze_parser.add_argument('--type', choices=['companies', 'extraction'], 
                              default='companies', help='分析类型')
    
    # 工具命令
    utils_parser = subparsers.add_parser('utils', help='工具功能')
    utils_parser.add_argument('--clean-pdfs', action='store_true', help='清理损坏的PDF')
    utils_parser.add_argument('--summary', action='store_true', help='生成项目摘要')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        if args.command == 'download':
            print("开始下载财报...")
            stats = download_reports(limit=args.limit, max_workers=args.workers)
            
        elif args.command == 'extract':
            print("开始提取财务数据...")
            if args.method == 'master' or args.use_llm:
                # 使用高级提取器
                extractor = MasterExtractor(use_llm=args.use_llm)
                print("使用Master Extractor进行提取...")
                # TODO: 添加批处理逻辑
            else:
                # 使用基础提取器
                output_file, success_rate = extract_financial_data(
                    limit=args.limit,
                    batch_size=args.batch_size
                )
            
        elif args.command == 'analyze':
            print(f"开始{args.type}分析...")
            stats = analyze_data(task=args.type)
            
        elif args.command == 'utils':
            if args.clean_pdfs:
                print("检查PDF文件...")
                stats = clean_pdfs()
            elif args.summary:
                generate_summary()
            else:
                print("请指定工具功能: --clean-pdfs 或 --summary")
                
    except KeyboardInterrupt:
        print("\n操作已取消")
        sys.exit(1)
    except Exception as e:
        print(f"\n错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()