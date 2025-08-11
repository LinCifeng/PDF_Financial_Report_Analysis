#!/usr/bin/env python3
"""
批量处理工具
Batch Processing Tool

作者: Lin Cifeng
创建时间: 2025-08-06

支持并行处理、自动重试、进度追踪
"""
import os
import sys
from pathlib import Path
import pandas as pd
from typing import List, Dict, Optional, Any
import json
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import time
import warnings

warnings.filterwarnings('ignore')

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from financial_analysis.extractor import MasterExtractor
from .cross_validator import CrossValidator


class BatchProcessor:
    """批量处理器"""
    
    def __init__(self, 
                 use_llm: bool = True,
                 api_key: Optional[str] = None,
                 max_workers: int = 4,
                 retry_times: int = 2):
        """
        初始化批量处理器
        
        Args:
            use_llm: 是否使用LLM
            api_key: LLM API密钥
            max_workers: 最大并行工作线程数
            retry_times: 失败重试次数
        """
        self.use_llm = use_llm
        self.api_key = api_key or os.getenv('DEEPSEEK_API_KEY')
        self.max_workers = max_workers
        self.retry_times = retry_times
        
        # 初始化提取器和验证器
        self.extractor = MasterExtractor(use_llm=use_llm, api_key=self.api_key)
        self.validator = CrossValidator()
        
        # 处理统计
        self.stats = {
            'total_files': 0,
            'processed': 0,
            'success': 0,
            'failed': 0,
            'empty_pdf': 0,
            'extraction_methods': {},
            'processing_time': 0
        }
    
    def process_batch(self, 
                     pdf_files: Optional[List[Path]] = None,
                     input_dir: Optional[str] = None,
                     output_dir: str = "output",
                     limit: Optional[int] = None) -> pd.DataFrame:
        """
        批量处理PDF文件
        
        Args:
            pdf_files: PDF文件列表
            input_dir: 输入目录（如果不提供pdf_files）
            output_dir: 输出目录
            limit: 限制处理数量
        
        Returns:
            处理结果的DataFrame
        """
        start_time = time.time()
        
        # 获取文件列表
        if pdf_files is None:
            if input_dir is None:
                input_dir = "data/raw_reports"
            pdf_files = list(Path(input_dir).glob("*.pdf"))
        
        if limit:
            pdf_files = pdf_files[:limit]
        
        self.stats['total_files'] = len(pdf_files)
        
        print(f"\n{'='*80}")
        print(f"批量处理开始")
        print(f"{'='*80}")
        print(f"总文件数: {len(pdf_files)}")
        print(f"使用LLM: {'是' if self.use_llm else '否'}")
        print(f"并行线程: {self.max_workers}")
        print(f"重试次数: {self.retry_times}")
        
        # 创建输出目录
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # 并行处理
        results = []
        failed_files = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交所有任务
            future_to_file = {
                executor.submit(self._process_single_file, pdf_file): pdf_file
                for pdf_file in pdf_files
            }
            
            # 处理完成的任务
            with tqdm(total=len(pdf_files), desc="处理进度") as pbar:
                for future in as_completed(future_to_file):
                    pdf_file = future_to_file[future]
                    
                    try:
                        result = future.result()
                        results.append(result)
                        
                        # 更新统计
                        self.stats['processed'] += 1
                        if result['extraction_status'] == 'success':
                            self.stats['success'] += 1
                            method = result.get('extraction_method', 'unknown')
                            self.stats['extraction_methods'][method] = \
                                self.stats['extraction_methods'].get(method, 0) + 1
                        elif result['extraction_status'] == 'empty_pdf':
                            self.stats['empty_pdf'] += 1
                        else:
                            self.stats['failed'] += 1
                            failed_files.append(pdf_file)
                    
                    except Exception as e:
                        print(f"\n处理出错 {pdf_file.name}: {str(e)}")
                        self.stats['failed'] += 1
                        failed_files.append(pdf_file)
                        
                        # 创建失败记录
                        results.append({
                            'filename': pdf_file.name,
                            'extraction_status': 'error',
                            'error': str(e)
                        })
                    
                    pbar.update(1)
        
        # 处理时间
        self.stats['processing_time'] = time.time() - start_time
        
        # 创建结果DataFrame
        results_df = pd.DataFrame(results)
        
        # 创建results和reports子目录
        results_dir = output_path / "results"
        reports_dir = output_path / "reports"
        results_dir.mkdir(exist_ok=True)
        reports_dir.mkdir(exist_ok=True)
        
        # 保存结果
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        date = datetime.now().strftime("%Y-%m-%d")
        
        # 保存详细结果到results目录
        detail_file = results_dir / f"extraction_result_{date}_{timestamp}.csv"
        results_df.to_csv(detail_file, index=False, encoding='utf-8')
        
        # 保存统计报告到reports目录
        stats_file = reports_dir / f"extraction_report_{date}_{timestamp}.json"
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(self.stats, f, ensure_ascii=False, indent=2)
        
        # 打印统计摘要
        self._print_summary(failed_files)
        
        print(f"\n结果已保存至:")
        print(f"  - 详细结果: {detail_file.relative_to(Path.cwd())}")
        print(f"  - 统计报告: {stats_file.relative_to(Path.cwd())}")
        
        return results_df
    
    def _process_single_file(self, pdf_file: Path) -> Dict[str, Any]:
        """处理单个文件"""
        result = {
            'filename': pdf_file.name,
            'file_path': str(pdf_file),
            'extraction_status': 'failed',
            'extraction_method': None,
            'confidence': 0,
            'data_completeness': 0
        }
        
        # 提取公司名和年份
        filename_parts = pdf_file.stem.split('_')
        if len(filename_parts) >= 2:
            result['company'] = filename_parts[0]
            result['year'] = filename_parts[1]
        
        # 重试机制
        for attempt in range(self.retry_times + 1):
            try:
                # 使用主提取器
                extraction_result = self.extractor.extract(str(pdf_file))
                
                if extraction_result['status'] == 'success':
                    result['extraction_status'] = 'success'
                    result['extraction_method'] = extraction_result['method']
                    result['confidence'] = extraction_result['confidence']
                    result['unit_multiplier'] = extraction_result.get('unit_multiplier', 1)
                    
                    # 添加提取的数据
                    for field, value in extraction_result['data'].items():
                        result[field] = value
                    
                    # 计算数据完整度
                    core_fields = ['total_assets', 'total_liabilities', 'revenue', 'net_profit']
                    complete_count = sum(1 for f in core_fields if f in extraction_result['data'])
                    result['data_completeness'] = complete_count / len(core_fields) * 100
                    
                    break  # 成功则退出重试
                
                elif 'error' in extraction_result and extraction_result['error'] == 'Empty PDF':
                    result['extraction_status'] = 'empty_pdf'
                    result['error'] = 'Empty PDF file'
                    break  # 空文件不需要重试
                
                else:
                    if attempt < self.retry_times:
                        time.sleep(1)  # 重试前等待
                    else:
                        result['error'] = extraction_result.get('error', 'Unknown error')
            
            except Exception as e:
                if attempt < self.retry_times:
                    time.sleep(1)
                else:
                    result['error'] = str(e)
        
        return result
    
    def _print_summary(self, failed_files: List[Path]):
        """打印处理摘要"""
        print(f"\n{'='*80}")
        print(f"处理完成")
        print(f"{'='*80}")
        
        print(f"\n总体统计:")
        print(f"  总文件数: {self.stats['total_files']}")
        print(f"  处理成功: {self.stats['success']} ({self.stats['success']/self.stats['total_files']*100:.1f}%)")
        print(f"  处理失败: {self.stats['failed']} ({self.stats['failed']/self.stats['total_files']*100:.1f}%)")
        print(f"  空PDF: {self.stats['empty_pdf']} ({self.stats['empty_pdf']/self.stats['total_files']*100:.1f}%)")
        
        print(f"\n提取方法分布:")
        for method, count in self.stats['extraction_methods'].items():
            print(f"  {method}: {count} ({count/self.stats['success']*100:.1f}%)")
        
        print(f"\n处理时间: {self.stats['processing_time']:.1f} 秒")
        print(f"平均每个文件: {self.stats['processing_time']/self.stats['total_files']:.2f} 秒")
        
        if failed_files:
            print(f"\n失败文件列表 (前10个):")
            for f in failed_files[:10]:
                print(f"  - {f.name}")
            if len(failed_files) > 10:
                print(f"  ... 还有 {len(failed_files)-10} 个文件")
    
    def validate_batch_results(self, extraction_df: pd.DataFrame) -> pd.DataFrame:
        """
        对批量提取结果进行交叉验证
        
        Args:
            extraction_df: 包含正则和LLM提取结果的DataFrame
        
        Returns:
            验证后的结果DataFrame
        """
        print(f"\n开始交叉验证...")
        
        validated_results = []
        
        for _, row in tqdm(extraction_df.iterrows(), total=len(extraction_df), desc="验证进度"):
            # 如果有正则和LLM两种结果，进行验证
            if 'regex_data' in row and 'llm_data' in row:
                validation = self.validator.validate(
                    row['regex_data'],
                    row['llm_data']
                )
                
                # 合并验证结果
                validated_row = {
                    'filename': row['filename'],
                    'validation_status': validation['status'],
                    'overall_confidence': validation['overall_confidence']
                }
                
                # 添加最终确定的值
                for field, value in validation['final_data'].items():
                    validated_row[f'final_{field}'] = value
                
                validated_results.append(validated_row)
        
        return pd.DataFrame(validated_results)
    
    def generate_final_report(self, results_df: pd.DataFrame, output_dir: str = "output"):
        """生成最终报告"""
        output_path = Path(output_dir)
        reports_dir = output_path / "reports"
        reports_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        date = datetime.now().strftime("%Y-%m-%d")
        
        # 生成Excel报告到reports目录
        excel_file = reports_dir / f"extraction_report_{date}_{timestamp}.xlsx"
        
        with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
            # 主要结果
            results_df.to_excel(writer, sheet_name='提取结果', index=False)
            
            # 统计摘要
            summary_data = {
                '指标': ['总文件数', '提取成功', '提取失败', '空PDF', '平均置信度'],
                '数值': [
                    len(results_df),
                    len(results_df[results_df['extraction_status'] == 'success']),
                    len(results_df[results_df['extraction_status'] == 'failed']),
                    len(results_df[results_df['extraction_status'] == 'empty_pdf']),
                    results_df['confidence'].mean() if 'confidence' in results_df else 0
                ]
            }
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='统计摘要', index=False)
            
            # 按公司统计
            if 'company' in results_df:
                company_stats = results_df.groupby('company').agg({
                    'extraction_status': 'count',
                    'confidence': 'mean',
                    'data_completeness': 'mean'
                }).round(2)
                company_stats.columns = ['文件数', '平均置信度', '平均完整度']
                company_stats.to_excel(writer, sheet_name='公司统计')
        
        print(f"\n最终报告已生成: {excel_file}")


def test_batch_processor():
    """测试批量处理器"""
    processor = BatchProcessor(use_llm=False, max_workers=2)
    
    # 测试少量文件
    test_dir = Path("data/raw_reports")
    test_files = list(test_dir.glob("*.pdf"))[:5]
    
    if test_files:
        print(f"测试批量处理 {len(test_files)} 个文件")
        results = processor.process_batch(pdf_files=test_files)
        
        print(f"\n提取结果预览:")
        print(results[['filename', 'extraction_status', 'confidence', 'data_completeness']].head())
    else:
        print("未找到测试文件")


if __name__ == "__main__":
    test_batch_processor()