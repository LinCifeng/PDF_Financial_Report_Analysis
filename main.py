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
from financial_analysis.extractor import SmartExtractor, smart_extract
from financial_analysis.analysis import analyze_extraction_results
from financial_analysis.visualization import create_charts
from financial_analysis.download.pdf_utils import clean_pdfs, generate_summary

# 导入旧接口（兼容性）
try:
    from financial_analysis.download.downloader import download_reports
except:
    from financial_analysis.download import batch_download as download_reports

try:
    from financial_analysis.analysis.analyzer import analyze_data
except:
    from financial_analysis.analysis import analyze_extraction_results as analyze_data


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
    extract_parser.add_argument('--batch-size', type=int, default=200, help='批处理大小')
    extract_parser.add_argument('--use-llm', action='store_true', help='使用LLM增强提取')
    extract_parser.add_argument('--method', choices=['regex', 'smart'], default='smart', help='提取方法（默认使用智能提取）')
    extract_parser.add_argument('--batch', type=int, help='批次ID（例如: 1, 2, 3...）')
    extract_parser.add_argument('--mode', choices=['regex_only', 'llm_only', 'regex_first', 'llm_first', 'adaptive'], 
                              default='regex_only', help='提取模式')
    extract_parser.add_argument('--workers', type=int, default=4, help='并行线程数')
    extract_parser.add_argument('--cache', action='store_true', help='启用缓存')
    extract_parser.add_argument('--skip-processed', action='store_true', default=True, help='跳过已处理文件')
    extract_parser.add_argument('--all', action='store_true', help='处理所有文件（自动断点续传）')
    
    # 分析命令
    analyze_parser = subparsers.add_parser('analyze', help='分析数据')
    analyze_parser.add_argument('--type', choices=['companies', 'extraction'], 
                              default='companies', help='分析类型')
    
    # 状态命令
    status_parser = subparsers.add_parser('status', help='查看提取进度')
    
    # 重试命令
    retry_parser = subparsers.add_parser('retry', help='重试失败项')
    retry_parser.add_argument('--failed', action='store_true', help='重试所有失败项')
    retry_parser.add_argument('--partial', action='store_true', help='重试部分成功项')
    retry_parser.add_argument('--mode', default='llm_only', help='重试模式')
    
    # 报告命令
    report_parser = subparsers.add_parser('report', help='生成质量报告')
    
    # 工具命令
    utils_parser = subparsers.add_parser('utils', help='工具功能')
    utils_parser.add_argument('--clean-pdfs', action='store_true', help='清理损坏的PDF')
    utils_parser.add_argument('--summary', action='store_true', help='生成项目摘要')
    
    # 监控命令
    monitor_parser = subparsers.add_parser('monitor', help='实时监控提取进度')
    
    # 合并命令
    merge_parser = subparsers.add_parser('merge', help='合并所有提取结果')
    merge_parser.add_argument('--output', default='output/final_combined_results', help='输出文件前缀')
    
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
            
            # 如果使用 --all 参数，处理所有文件
            if args.all:
                print("\n🚀 全量提取模式：处理所有1158个文件")
                print("=" * 60)
                print("特性：")
                print("  ✅ 自动断点续传")
                print("  ✅ 错误自动跳过")
                print("  ✅ 每10个文件保存进度")
                print("  ✅ 智能重试机制")
                print("=" * 60)
                
                # 设置最优参数
                stats = smart_extract(
                    limit=None,  # 不限制数量，处理所有文件
                    extraction_mode=args.mode if args.mode else 'regex_first',
                    use_llm=args.use_llm,
                    max_workers=args.workers if args.workers else 4,
                    use_cache=True,  # 强制启用缓存
                    batch_id=1,
                    batch_size=args.batch_size,
                    skip_processed=True  # 强制跳过已处理
                )
                print(f"\n✅ 全量提取完成!")
                print(f"成功: {stats['successful']} | 部分: {stats['partial']} | 失败: {stats['failed']}")
                
                # 如果有失败，提示重试
                if stats['failed'] > 0:
                    print(f"\n💡 提示: 有 {stats['failed']} 个失败文件")
                    print("   运行以下命令重试失败项：")
                    print("   python main.py retry --failed --mode llm_only")
                    
            elif args.method == 'smart':
                # 使用智能提取器（默认）
                print("使用智能提取器 (Smart Extractor)...")
                stats = smart_extract(
                    limit=args.limit,
                    extraction_mode=args.mode,
                    use_llm=args.use_llm,
                    max_workers=args.workers,
                    use_cache=args.cache,
                    batch_id=args.batch,
                    batch_size=args.batch_size,
                    skip_processed=args.skip_processed
                )
                print(f"\n提取完成: 成功={stats['successful']}, 部分={stats['partial']}, 失败={stats['failed']}")
            else:
                # 使用基础正则提取器
                print("使用正则提取器 (Regex Extractor)...")
                stats = smart_extract(
                    limit=args.limit,
                    extraction_mode='regex_only',
                    max_workers=4,
                    use_cache=True
                )
                print(f"\n提取完成: 成功={stats['successful']}, 部分={stats['partial']}, 失败={stats['failed']}")
            
        elif args.command == 'status':
            # 查看进度
            print("查看提取进度...")
            from financial_analysis.extractor.batch_manager import show_status
            show_status()
            
        elif args.command == 'retry':
            # 重试失败项
            print("重试失败项...")
            from financial_analysis.extractor.batch_manager import retry_failed
            retry_failed(failed_only=args.failed, partial_only=args.partial, mode=args.mode)
            
        elif args.command == 'report':
            # 生成综合报告
            print("生成综合报告...")
            from financial_analysis.extractor.batch_manager import generate_quality_report, generate_final_report
            # 先生成质量报告
            generate_quality_report()
            # 再生成最终报告
            generate_final_report()
            
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
        
        elif args.command == 'monitor':
            # 监控提取进度
            print("启动实时监控...")
            from financial_analysis.extractor.batch_manager import monitor_extraction
            monitor_extraction()
        
        elif args.command == 'merge':
            # 合并所有结果
            print("合并所有提取结果...")
            from financial_analysis.extractor.batch_manager import merge_all_results
            stats = merge_all_results(output_prefix=args.output)
            if stats:
                print(f"\n✅ 合并完成: {stats['total']} 条记录")
                if stats['total'] >= 1000:
                    print(f"🎉 目标达成！成功提取 {stats['total']} 条记录！")
                else:
                    print(f"📈 距离1000条目标还差: {1000 - stats['total']} 条")
                
    except KeyboardInterrupt:
        print("\n操作已取消")
        sys.exit(1)
    except Exception as e:
        print(f"\n错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()