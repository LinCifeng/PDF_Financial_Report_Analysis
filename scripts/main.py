#!/usr/bin/env python3
"""
财务数据分析项目主入口
Financial Analysis Project Main Entry
"""

import argparse
import sys
import os
from pathlib import Path

# 添加src到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def extract_simple():
    """运行简化版数据提取"""
    from scripts.simple_extract import main
    main()

def extract_all():
    """运行完整数据提取（使用LLM）"""
    from scripts.extract_all_data import main
    main()

def analyze():
    """运行公司分析"""
    from scripts.analyze_companies import main
    main()

def main():
    parser = argparse.ArgumentParser(
        description='财务数据分析工具 Financial Data Analysis Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例 Examples:
  python main.py extract        # 简单提取财务数据
  python main.py extract-llm    # 使用LLM增强提取
  python main.py analyze        # 分析提取的数据
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 简单提取命令
    parser_extract = subparsers.add_parser(
        'extract', 
        help='简单提取财务数据到CSV'
    )
    
    # LLM提取命令
    parser_extract_llm = subparsers.add_parser(
        'extract-llm',
        help='使用LLM增强提取财务数据'
    )
    
    # 分析命令
    parser_analyze = subparsers.add_parser(
        'analyze',
        help='分析已提取的财务数据'
    )
    
    args = parser.parse_args()
    
    if args.command == 'extract':
        print("开始简单数据提取...")
        extract_simple()
    elif args.command == 'extract-llm':
        print("开始LLM增强数据提取...")
        extract_all()
    elif args.command == 'analyze':
        print("开始数据分析...")
        analyze()
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()