"""
智能提取器 - 策略模式重构版
Smart Extractor - Strategy Pattern Version

作者: Lin Cifeng
创建: 2025-08-11
"""

import warnings
from pathlib import Path
from typing import Optional, Dict, Any, List
import pdfplumber
from datetime import datetime
import csv
import time
import concurrent.futures
import json
import hashlib
from tqdm import tqdm

warnings.filterwarnings('ignore')

from .base_extractor import BaseExtractor
from .financial_models import FinancialData
from .strategies import (
    RegexStrategy,
    LLMStrategy,
    OCRStrategy,
    TableStrategy,
    ExtractionResult
)


class SmartExtractor(BaseExtractor):
    """
    智能提取器 - 策略调度器
    
    支持的提取模式：
    - regex_only: 仅使用正则表达式
    - llm_only: 仅使用LLM
    - regex_first: 优先正则，其他策略补充（默认）
    - llm_first: 优先LLM，其他策略补充
    - adaptive: 自适应选择最佳策略组合
    """
    
    def __init__(self, extraction_mode: str = 'regex_first', use_llm: bool = False):
        """
        初始化智能提取器
        
        Args:
            extraction_mode: 提取模式
            use_llm: 是否启用LLM
        """
        super().__init__()
        
        # 验证提取模式
        valid_modes = ['regex_only', 'regex_table', 'llm_only', 'regex_first', 'llm_first', 'adaptive']
        if extraction_mode not in valid_modes:
            print(f"  ⚠️ 未知模式 '{extraction_mode}'，使用默认 'regex_first'")
            extraction_mode = 'regex_first'
        
        self.extraction_mode = extraction_mode
        self.use_llm = use_llm
        
        # 初始化策略
        self.strategies = {
            'regex': RegexStrategy(),
            'table': TableStrategy(),
            'ocr': OCRStrategy()
        }
        
        # 根据模式和设置初始化LLM策略
        if extraction_mode in ['llm_only', 'llm_first'] or use_llm:
            self.strategies['llm'] = LLMStrategy()
        
        # 统计信息
        self.stats = {
            'total_processed': 0,
            'complete_success': 0,
            'partial_success': 0,
            'failed': 0,
            'strategy_usage': {name: 0 for name in self.strategies.keys()}
        }
    
    def _extract_data(self, pdf: pdfplumber.PDF, result: FinancialData) -> None:
        """
        实现策略调度逻辑
        
        Args:
            pdf: PDF对象
            result: 结果对象
        """
        self.stats['total_processed'] += 1
        pdf_path = getattr(pdf, 'path', result.file_path)
        
        # 根据模式执行不同的策略组合
        if self.extraction_mode == 'regex_only':
            extracted = self._extract_regex_only(pdf)
        elif self.extraction_mode == 'regex_table':
            extracted = self._extract_regex_table(pdf)
        elif self.extraction_mode == 'llm_only':
            extracted = self._extract_llm_only(pdf)
        elif self.extraction_mode == 'regex_first':
            extracted = self._extract_regex_first(pdf)
        elif self.extraction_mode == 'llm_first':
            extracted = self._extract_llm_first(pdf)
        else:  # adaptive
            extracted = self._extract_adaptive(pdf, pdf_path)
        
        # 填充结果
        self._fill_result(result, extracted)
        
        # 更新统计
        self._update_stats(result)
    
    def _extract_regex_only(self, pdf: pdfplumber.PDF) -> ExtractionResult:
        """仅使用正则提取（快速模式）"""
        # 提取文本 - 增加扫描页数以提高成功率
        text = self.extract_text_from_pages(pdf, max_pages=30)
        unit_multiplier = self.detect_unit(text)
        
        # 正则提取
        regex_result = self.strategies['regex'].execute(text, unit_multiplier=unit_multiplier)
        self.stats['strategy_usage']['regex'] += 1
        
        # 激进模式：如果正则没有提取到足够数据，尝试提取任何大数字
        if regex_result.fields_count < 2:
            import re
            # 查找所有大数字（百万级以上）
            number_patterns = [
                r'\$\s*([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]+)?)\s*(?:million|Million|M|m)',
                r'([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]+)?)\s*(?:million|Million|千万|百万|億)',
                r'\$\s*([0-9]{7,}(?:\.[0-9]+)?)',  # 7位数以上
                r'([0-9]{7,}(?:\.[0-9]+)?)\s*(?:元|円|₩|€)',
            ]
            
            all_numbers = []
            for pattern in number_patterns:
                matches = re.findall(pattern, text)
                for match in matches:
                    try:
                        # 清理数字并转换
                        clean_num = match.replace(',', '')
                        value = float(clean_num)
                        if value > 1000000:  # 只保留百万以上的数字
                            all_numbers.append(value)
                    except:
                        pass
            
            # 将找到的数字分配给缺失的字段
            if all_numbers:
                all_numbers.sort(reverse=True)  # 从大到小排序
                if regex_result.total_assets is None and len(all_numbers) > 0:
                    regex_result.total_assets = all_numbers[0]
                if regex_result.total_liabilities is None and len(all_numbers) > 1:
                    regex_result.total_liabilities = all_numbers[1]
                if regex_result.revenue is None and len(all_numbers) > 2:
                    regex_result.revenue = all_numbers[2]
                if regex_result.net_profit is None and len(all_numbers) > 3:
                    regex_result.net_profit = all_numbers[3]
        
        # 注意：regex_only模式不进行表格提取，以保证速度
        regex_result.method = "regex"
        
        return regex_result
    
    def _extract_regex_table(self, pdf: pdfplumber.PDF) -> ExtractionResult:
        """使用正则和表格提取（标准模式）"""
        # 提取文本
        text = self.extract_text_from_pages(pdf, max_pages=50)
        unit_multiplier = self.detect_unit(text)
        
        # 正则提取
        regex_result = self.strategies['regex'].execute(text, unit_multiplier=unit_multiplier)
        self.stats['strategy_usage']['regex'] += 1
        
        # 表格提取补充
        table_result = self.strategies['table'].execute(pdf)
        self.stats['strategy_usage']['table'] += 1
        
        # 合并结果
        regex_result.merge(table_result)
        regex_result.method = "regex+table"
        
        return regex_result
    
    def _extract_llm_only(self, pdf: pdfplumber.PDF) -> ExtractionResult:
        """仅使用LLM提取 - 改进版，专注财务报表页面"""
        if 'llm' not in self.strategies:
            print("  ❌ LLM策略不可用")
            return ExtractionResult(method="failed")
        
        print("    📖 扫描PDF寻找财务报表...")
        
        # 更精确的财务报表关键词
        financial_keywords = [
            # 英文
            'total assets', 'total liabilities', 'total equity',
            'statement of financial position', 'balance sheet',
            'income statement', 'profit or loss',
            'comprehensive income', 'cash flow',
            # 中文
            '总资产', '总负债', '净资产', '资产负债表',
            '利润表', '损益表', '现金流量表',
            # 葡萄牙语（巴西）
            'ativo total', 'passivo total', 'patrimônio líquido',
            'demonstração', 'balanço patrimonial',
            # 西班牙语
            'activos totales', 'pasivos totales'
        ]
        
        # 扫描页面，找到最可能包含财务报表的页面
        financial_pages = []
        table_pages = []  # 包含表格的页面
        
        for i, page in enumerate(pdf.pages):
            text = page.extract_text()
            tables = page.extract_tables()
            
            if text:
                text_lower = text.lower()
                # 计算关键词密度
                keyword_count = sum(1 for keyword in financial_keywords if keyword in text_lower)
                
                # 检查是否有数字（财务数据通常包含大量数字）
                import re
                numbers = re.findall(r'\b\d{1,3}(?:,\d{3})*(?:\.\d+)?\b', text)
                
                if keyword_count > 0 and len(numbers) > 5:  # 至少有1个关键词和5个数字
                    financial_pages.append((i, text, keyword_count, len(numbers)))
            
            # 记录有表格的页面
            if tables:
                for table in tables:
                    if table and len(table) > 3:  # 至少4行的表格
                        table_text = str(table).lower()
                        if any(kw in table_text for kw in ['asset', 'liabil', 'revenue', 'income', 'ativo', 'passivo']):
                            table_pages.append((i, text if text else ''))
                            break
        
        print(f"    📊 找到 {len(financial_pages)} 个财务页面，{len(table_pages)} 个表格页面")
        
        # 组合最相关的页面
        combined_text = ""
        
        if financial_pages:
            # 按关键词密度和数字数量排序
            financial_pages.sort(key=lambda x: (x[2], x[3]), reverse=True)
            
            # 优先使用关键词密度高的页面
            for page_num, text, keyword_count, number_count in financial_pages[:5]:
                print(f"      📄 页面 {page_num+1}: {keyword_count} 个关键词, {number_count} 个数字")
                combined_text += f"\n\n--- Page {page_num+1} ---\n{text}"
                
                if len(combined_text) > 25000:  # 限制总长度
                    break
        
        # 如果财务页面不够，补充表格页面
        if len(combined_text) < 10000 and table_pages:
            for page_num, text in table_pages[:3]:
                if text and text not in combined_text:
                    combined_text += f"\n\n--- Table Page {page_num+1} ---\n{text}"
                    if len(combined_text) > 25000:
                        break
        
        # 如果还是没有内容，使用前20页
        if len(combined_text) < 1000:
            print("    ⚠️ 未找到明确的财务报表，使用前20页")
            combined_text = self.extract_text_from_pages(pdf, max_pages=20)
        
        print(f"    📝 准备发送 {len(combined_text)} 字符给LLM...")
        
        # 获取公司名和年份（从文件名推测）
        pdf_path = getattr(pdf, 'path', '')
        if pdf_path:
            from pathlib import Path
            filename = Path(pdf_path).stem
            parts = filename.split('_')
            company_name = parts[0] if parts else ''
            year = parts[1] if len(parts) > 1 else ''
        else:
            company_name = ''
            year = ''
        
        # LLM提取
        llm_result = self.strategies['llm'].execute(
            combined_text, 
            text_limit=30000,
            company_name=company_name,
            year=year
        )
        self.stats['strategy_usage']['llm'] += 1
        
        return llm_result
    
    def _extract_regex_first(self, pdf: pdfplumber.PDF) -> ExtractionResult:
        """优先正则，LLM补充"""
        # 先执行正则提取
        result = self._extract_regex_only(pdf)
        
        # 如果不完整且有LLM，使用LLM补充
        if not result.is_complete and 'llm' in self.strategies:
            print(f"    🤖 使用LLM增强提取（当前{result.fields_count}/4字段）...")
            text = self.extract_text_from_pages(pdf, max_pages=50)
            llm_result = self.strategies['llm'].execute(text)
            self.stats['strategy_usage']['llm'] += 1
            
            result.merge(llm_result)
            result.method = "regex+table+llm"
        
        return result
    
    def _extract_llm_first(self, pdf: pdfplumber.PDF) -> ExtractionResult:
        """优先LLM，正则补充"""
        # 先执行LLM提取
        result = self._extract_llm_only(pdf)
        
        # 如果不完整，使用正则补充
        if not result.is_complete:
            regex_result = self._extract_regex_only(pdf)
            result.merge(regex_result)
            result.method = "llm+regex+table"
        
        return result
    
    def _extract_adaptive(self, pdf: pdfplumber.PDF, pdf_path: str) -> ExtractionResult:
        """自适应策略选择"""
        # Step 1: 检查是否为扫描版
        method_prefix = ""
        if self.strategies['ocr'].can_handle(pdf):
            # 执行OCR
            ocr_result = self.strategies['ocr'].execute(pdf_path)
            self.stats['strategy_usage']['ocr'] += 1
            
            if hasattr(ocr_result, 'ocr_text'):
                text = ocr_result.ocr_text
                method_prefix = "ocr+"
            else:
                text = self.extract_text_from_pages(pdf, max_pages=50)
        else:
            text = self.extract_text_from_pages(pdf, max_pages=50)
        
        # Step 2: 检测单位
        unit_multiplier = self.detect_unit(text)
        
        # Step 3: 执行正则提取
        regex_result = self.strategies['regex'].execute(text, unit_multiplier=unit_multiplier)
        self.stats['strategy_usage']['regex'] += 1
        
        # Step 4: 表格提取补充
        table_result = self.strategies['table'].execute(pdf)
        self.stats['strategy_usage']['table'] += 1
        regex_result.merge(table_result)
        
        # Step 5: 如果不完整且有LLM，使用LLM补充
        if not regex_result.is_complete and 'llm' in self.strategies:
            print(f"    🤖 使用LLM增强提取（当前{regex_result.fields_count}/4字段）...")
            llm_result = self.strategies['llm'].execute(text)
            self.stats['strategy_usage']['llm'] += 1
            regex_result.merge(llm_result)
            regex_result.method = f"{method_prefix}regex+table+llm"
        else:
            regex_result.method = f"{method_prefix}regex+table"
        
        return regex_result
    
    def _fill_result(self, result: FinancialData, extracted: ExtractionResult):
        """填充提取结果到FinancialData对象"""
        result.total_assets = extracted.total_assets
        result.total_liabilities = extracted.total_liabilities
        result.revenue = extracted.revenue
        result.net_profit = extracted.net_profit
        result.confidence = extracted.confidence
        result.extraction_method = extracted.method
        
        # 设置成功级别
        if extracted.is_complete:
            result.success_level = "Complete"
        elif extracted.fields_count > 0:
            result.success_level = f"Partial({extracted.fields_count}/4)"
        else:
            result.success_level = "Failed"
    
    def _update_stats(self, result: FinancialData):
        """更新统计信息"""
        if result.success_level == "Complete":
            self.stats['complete_success'] += 1
        elif result.success_level and "Partial" in result.success_level:
            self.stats['partial_success'] += 1
        else:
            self.stats['failed'] += 1
    
    def print_stats(self):
        """打印统计信息"""
        print("\n" + "="*60)
        print("智能提取器统计")
        print("="*60)
        print(f"提取模式: {self.extraction_mode}")
        print(f"总处理文件: {self.stats['total_processed']}")
        
        if self.stats['total_processed'] > 0:
            complete_rate = self.stats['complete_success'] / self.stats['total_processed'] * 100
            partial_rate = self.stats['partial_success'] / self.stats['total_processed'] * 100
            failed_rate = self.stats['failed'] / self.stats['total_processed'] * 100
            
            print(f"\n成功率统计:")
            print(f"  完全成功: {complete_rate:.1f}% ({self.stats['complete_success']}/{self.stats['total_processed']})")
            print(f"  部分成功: {partial_rate:.1f}% ({self.stats['partial_success']}/{self.stats['total_processed']})")
            print(f"  失败: {failed_rate:.1f}% ({self.stats['failed']}/{self.stats['total_processed']})")
            
            print(f"\n策略使用统计:")
            for strategy, count in self.stats['strategy_usage'].items():
                if count > 0:
                    print(f"  {strategy}: {count}次")


def smart_extract(
    input_dir: str = "data/raw_reports",
    output_dir: str = "output",
    limit: Optional[int] = None,
    extraction_mode: str = 'regex_first',
    use_llm: bool = False,
    max_workers: int = 1,
    use_cache: bool = False,
    batch_id: Optional[int] = None,
    batch_size: int = 200,
    skip_processed: bool = True,
    master_table_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    智能提取主函数
    
    Args:
        input_dir: PDF文件目录
        output_dir: 输出目录
        limit: 限制处理文件数
        extraction_mode: 提取模式
        use_llm: 是否启用LLM
    """
    # 记录开始时间
    total_start_time = time.time()
    
    # 缓存和主表设置
    cache_dir = Path("output/extraction_cache")
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file = cache_dir / "processed_files.json"
    
    # 主控制表
    if master_table_path:
        master_table_file = Path(master_table_path)
    else:
        master_table_file = Path("output/extraction_master.json")
    
    # 加载或创建主控制表
    if master_table_file.exists():
        with open(master_table_file, 'r', encoding='utf-8') as f:
            master_table = json.load(f)
    else:
        master_table = {
            "metadata": {
                "total_files": 0,
                "processed": 0,
                "successful": 0,
                "partial": 0,
                "failed": 0,
                "last_update": datetime.now().isoformat(),
                "batches": {}
            },
            "files": {}
        }
    
    # 加载缓存
    processed_cache = {}
    if use_cache and cache_file.exists():
        with open(cache_file, 'r') as f:
            processed_cache = json.load(f)
    
    # 获取PDF文件
    all_pdf_files = sorted(list(Path(input_dir).glob("*.pdf")))  # 排序以保证一致性
    master_table["metadata"]["total_files"] = len(all_pdf_files)
    
    # 批次处理
    if batch_id is not None:
        # 计算批次范围
        start_idx = (batch_id - 1) * batch_size
        end_idx = min(start_idx + batch_size, len(all_pdf_files))
        pdf_files = all_pdf_files[start_idx:end_idx]
        print(f"处理批次 {batch_id}: 文件 {start_idx+1}-{end_idx} (共{len(pdf_files)}个)")
        
        # 记录批次信息
        master_table["metadata"]["batches"][str(batch_id)] = {
            "start": start_idx,
            "end": end_idx,
            "size": len(pdf_files),
            "status": "processing",
            "start_time": datetime.now().isoformat()
        }
    else:
        pdf_files = all_pdf_files
    
    # 过滤已处理文件
    if skip_processed:
        original_count = len(pdf_files)
        # 简化逻辑：只处理未成功的文件
        filtered_files = []
        for f in pdf_files:
            # 检查主表中的状态
            if f.name in master_table["files"]:
                status = master_table["files"][f.name].get("status")
                # 只重新处理失败的文件，跳过成功和部分成功的
                if status in ["completed", "partial"]:
                    continue
            # 如果不在主表中，或者状态是失败，则需要处理
            filtered_files.append(f)
        
        pdf_files = filtered_files
        skipped_count = original_count - len(pdf_files)
        if skipped_count > 0:
            print(f"跳过 {skipped_count} 个已处理文件")
    
    if limit:
        pdf_files = pdf_files[:limit]
    
    print(f"\n{'='*60}")
    print(f"智能财务数据提取 - 批量管理模式")
    print(f"{'='*60}")
    if batch_id:
        print(f"批次ID: {batch_id}")
    print(f"总文件数: {master_table['metadata']['total_files']}")
    print(f"已处理: {master_table['metadata']['processed']}")
    print(f"本次待处理: {len(pdf_files)}")
    print(f"提取模式: {extraction_mode}")
    print(f"LLM支持: {'启用' if use_llm else '猁用'}")
    print(f"并行线程: {max_workers}")
    print(f"缓存: {'启用' if use_cache else '禁用'}")
    print(f"{'='*60}")
    
    # 定义单文件处理函数
    def process_single_file(pdf_path: Path) -> FinancialData:
        try:
            # 检查重试次数
            retry_count = master_table["files"].get(pdf_path.name, {}).get("retry_count", 0)
            
            # 如果已经重试多次，直接跳过
            if retry_count > 3:
                print(f"  ⏭️ 跳过多次失败文件: {pdf_path.name} (已重试{retry_count}次)")
                result = FinancialData(company=pdf_path.stem.split('_')[0], file_path=str(pdf_path))
                result.success_level = "Skipped"
                return result
            
            # 检查缓存
            if use_cache and pdf_path.name in processed_cache:
                cached = processed_cache[pdf_path.name]
                # 只有成功或部分成功的才使用缓存
                if cached.get('success_level') not in ['Failed', 'Skipped']:
                    result = FinancialData(company=pdf_path.stem.split('_')[0], file_path=str(pdf_path))
                    result.company = cached.get('company')
                    result.year = cached.get('year')
                    result.total_assets = cached.get('total_assets')
                    result.total_liabilities = cached.get('total_liabilities')
                    result.revenue = cached.get('revenue')
                    result.net_profit = cached.get('net_profit')
                    result.success_level = cached.get('success_level')
                    result.extraction_method = "cached"
                    return result
            
            # 创建新的提取器实例（线程安全）
            # 对于重试的文件，使用更保守的策略
            if retry_count > 0:
                # 重试时尝试使用不同的模式
                retry_mode = 'regex_only' if extraction_mode == 'llm_only' else 'regex_first'
                extractor = SmartExtractor(extraction_mode=retry_mode, use_llm=False)
            else:
                extractor = SmartExtractor(extraction_mode=extraction_mode, use_llm=use_llm)
            
            result = extractor.extract_from_pdf(str(pdf_path))
            
            # 保存到缓存和主表
            file_info = {
                'company': result.company,
                'year': result.year,
                'total_assets': result.total_assets,
                'total_liabilities': result.total_liabilities,
                'revenue': result.revenue,
                'net_profit': result.net_profit,
                'success_level': result.success_level,
                'timestamp': datetime.now().isoformat()
            }
            
            if use_cache and result.success_level != "Failed":
                processed_cache[pdf_path.name] = file_info
            
            # 更新主表
            extracted_fields = sum([
                1 for field in [result.total_assets, result.total_liabilities, 
                               result.revenue, result.net_profit]
                if field is not None
            ])
            
            master_table["files"][pdf_path.name] = {
                "status": "completed" if result.success_level == "Complete" else 
                         "partial" if "Partial" in str(result.success_level) else "failed",
                "batch_id": batch_id,
                "extracted_fields": extracted_fields,
                "quality_score": extracted_fields / 4.0,
                "retry_count": master_table["files"].get(pdf_path.name, {}).get("retry_count", 0),
                "last_update": datetime.now().isoformat()
            }
            
            return result
        except Exception as e:
            print(f"  ❌ {pdf_path.name}: {e}")
            result = FinancialData(company=pdf_path.stem.split('_')[0], file_path=str(pdf_path))
            result.success_level = "Failed"
            return result
    
    # 提取数据
    results = []
    
    if max_workers > 1:
        # 并行处理
        # LLM模式限制并发数（API限制）
        if extraction_mode == 'llm_only' and use_llm:
            actual_workers = min(max_workers, 2)
        else:
            actual_workers = max_workers
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=actual_workers) as executor:
            # 使用tqdm显示进度
            with tqdm(total=len(pdf_files), desc="处理进度") as pbar:
                future_to_pdf = {executor.submit(process_single_file, pdf): pdf for pdf in pdf_files}
                
                for future in concurrent.futures.as_completed(future_to_pdf):
                    pdf = future_to_pdf[future]
                    try:
                        # 减少超时时间到30秒，快速跳过问题文件
                        result = future.result(timeout=30)
                        results.append(result)
                        
                        # 更新进度条
                        if result.success_level == "Complete":
                            status = "✅"
                        elif "Partial" in str(result.success_level):
                            status = "⚠️"
                        else:
                            status = "❌"
                        pbar.set_description(f"{pdf.name[:30]} {status}")
                        pbar.update(1)
                        
                        # 每处理10个文件保存一次进度
                        if len(results) % 10 == 0:
                            # 保存中间进度
                            if use_cache:
                                with open(cache_file, 'w') as f:
                                    json.dump(processed_cache, f, indent=2)
                            with open(master_table_file, 'w', encoding='utf-8') as f:
                                json.dump(master_table, f, indent=2, ensure_ascii=False)
                            
                    except concurrent.futures.TimeoutError:
                        print(f"\n  ⏱️ {pdf.name}: 处理超时(60秒)，标记为失败")
                        # 创建失败结果
                        failed_result = FinancialData(company=pdf.stem.split('_')[0], file_path=str(pdf))
                        failed_result.success_level = "Failed"
                        results.append(failed_result)
                        # 标记需要重试
                        master_table["files"][pdf.name] = {
                            "status": "failed",
                            "retry_needed": True,
                            "error": "Timeout",
                            "timestamp": datetime.now().isoformat()
                        }
                        pbar.update(1)
                    except Exception as e:
                        print(f"\n  ❌ {pdf.name}: {str(e)[:100]}")
                        # 创建失败结果但继续处理
                        failed_result = FinancialData(company=pdf.stem.split('_')[0], file_path=str(pdf))
                        failed_result.success_level = "Failed"
                        results.append(failed_result)
                        pbar.update(1)
    else:
        # 串行处理（原逻辑）
        for i, pdf_path in enumerate(pdf_files, 1):
            print(f"\n[{i}/{len(pdf_files)}] {pdf_path.name}")
            result = process_single_file(pdf_path)
            results.append(result)
            
            # 打印结果摘要
            if result.success_level == "Complete":
                print(f"  ✅ 完全成功 - {result.extraction_method}")
            elif "Partial" in str(result.success_level):
                print(f"  ⚠️ 部分成功 - {result.success_level} - {result.extraction_method}")
            else:
                print(f"  ❌ 失败")
    
    # 保存缓存和主表
    if use_cache:
        with open(cache_file, 'w') as f:
            json.dump(processed_cache, f, indent=2)
    
    # 更新主表元数据
    master_table["metadata"]["processed"] = len([f for f in master_table["files"].values() 
                                                 if f.get("status") in ["completed", "partial"]])
    master_table["metadata"]["successful"] = len([f for f in master_table["files"].values() 
                                                   if f.get("status") == "completed"])
    master_table["metadata"]["partial"] = len([f for f in master_table["files"].values() 
                                               if f.get("status") == "partial"])
    master_table["metadata"]["failed"] = len([f for f in master_table["files"].values() 
                                              if f.get("status") == "failed"])
    master_table["metadata"]["last_update"] = datetime.now().isoformat()
    
    # 更新批次状态
    if batch_id and str(batch_id) in master_table["metadata"]["batches"]:
        master_table["metadata"]["batches"][str(batch_id)]["status"] = "completed"
        master_table["metadata"]["batches"][str(batch_id)]["end_time"] = datetime.now().isoformat()
    
    # 保存主表
    with open(master_table_file, 'w', encoding='utf-8') as f:
        json.dump(master_table, f, indent=2, ensure_ascii=False)
    
    # 保存结果
    output_path = Path(output_dir)
    results_dir = output_path / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d%H%M')
    prefix = "parallel_" if max_workers > 1 else ""
    output_file = results_dir / f"{prefix}extraction_{timestamp}.csv"
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['Company', 'Year', 'Total Assets', 'Total Liabilities',
                     'Revenue', 'Net Profit', 'Method', 'File', 'Status',
                     'Success Level', 'Currency', 'Unit', 'Language']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for result in results:
            row = result.to_dict()
            row['Method'] = result.extraction_method
            writer.writerow(row)
    
    # 打印统计（只在单线程模式下有extractor实例）
    if max_workers == 1:
        # 创建一个临时extractor实例来打印统计
        temp_extractor = SmartExtractor(extraction_mode=extraction_mode, use_llm=use_llm)
        temp_extractor.stats['total_processed'] = len(results)
        temp_extractor.stats['complete_success'] = sum(1 for r in results if r.success_level == "Complete")
        temp_extractor.stats['partial_success'] = sum(1 for r in results if "Partial" in str(r.success_level))
        temp_extractor.stats['failed'] = sum(1 for r in results if r.success_level == "Failed")
        temp_extractor.print_stats()
    else:
        # 多线程模式下直接打印统计
        print("\n" + "="*60)
        print("提取统计")
        print("="*60)
        complete = sum(1 for r in results if r.success_level == "Complete")
        partial = sum(1 for r in results if "Partial" in str(r.success_level))
        failed = sum(1 for r in results if r.success_level == "Failed")
        cached = sum(1 for r in results if hasattr(r, 'extraction_method') and r.extraction_method == "cached")
        
        total = len(results)
        if total > 0:
            print(f"总文件数: {total}")
            print(f"  完全成功: {complete} ({complete/total*100:.1f}%)")
            print(f"  部分成功: {partial} ({partial/total*100:.1f}%)")
            print(f"  失败: {failed} ({failed/total*100:.1f}%)")
            if cached > 0:
                print(f"  使用缓存: {cached}")
    
    # 显示总执行时间
    total_elapsed = time.time() - total_start_time
    print(f"\n总执行时间: {total_elapsed:.2f}秒")
    if len(pdf_files) > 0:
        print(f"平均每文件: {total_elapsed/len(pdf_files):.2f}秒")
    
    print(f"\n结果已保存至: {output_file}")
    print(f"主控制表已更新: {master_table_file}")
    
    # 返回统计信息
    return {
        "total_processed": len(results),
        "successful": complete if 'complete' in locals() else sum(1 for r in results if r.success_level == "Complete"),
        "partial": partial if 'partial' in locals() else sum(1 for r in results if "Partial" in str(r.success_level)),
        "failed": failed if 'failed' in locals() else sum(1 for r in results if r.success_level == "Failed"),
        "batch_id": batch_id,
        "elapsed_time": total_elapsed
    }


if __name__ == "__main__":
    # 测试策略模式
    smart_extract(limit=5, extraction_mode='regex_first')