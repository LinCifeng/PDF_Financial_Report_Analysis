#!/usr/bin/env python3
"""
PDF文件管理工具
PDF File Management Tool

作者: Lin Cifeng
创建时间: 2025-08-06

管理PDF文件的下载、验证、去重和修复
"""
import os
import shutil
from pathlib import Path
import pandas as pd
import pdfplumber
import requests
from urllib.parse import unquote, urlparse, parse_qs
import hashlib
from typing import List, Dict, Tuple, Optional, Set
import json
from datetime import datetime
from tqdm import tqdm
import time


class PDFManager:
    """PDF文件管理器"""
    
    def __init__(self, data_dir: str = "data/raw_reports"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # 创建子目录
        self.backup_dir = self.data_dir / "backup"
        self.corrupted_dir = self.data_dir / "corrupted_backup"
        self.duplicate_dir = self.data_dir / "duplicate_backup"
        
        for dir_path in [self.backup_dir, self.corrupted_dir, self.duplicate_dir]:
            dir_path.mkdir(exist_ok=True)
        
        # 统计信息
        self.stats = {
            'total_files': 0,
            'valid_files': 0,
            'empty_files': 0,
            'corrupted_files': 0,
            'duplicate_files': 0,
            'fixed_files': 0,
            'download_failed': 0
        }
    
    def scan_pdf_files(self) -> Dict[str, List[Path]]:
        """
        扫描所有PDF文件并分类
        
        Returns:
            分类后的文件字典
        """
        print(f"\n{'='*80}")
        print("扫描PDF文件")
        print(f"{'='*80}")
        
        all_pdfs = list(self.data_dir.glob("*.pdf"))
        self.stats['total_files'] = len(all_pdfs)
        
        print(f"找到 {len(all_pdfs)} 个PDF文件")
        
        categorized = {
            'valid': [],
            'empty': [],
            'corrupted': [],
            'duplicates': []
        }
        
        # 用于检测重复文件
        file_hashes = {}
        
        for pdf_path in tqdm(all_pdfs, desc="扫描文件"):
            category = self._check_pdf_status(pdf_path)
            
            if category == 'valid':
                # 检查是否重复
                file_hash = self._calculate_file_hash(pdf_path)
                if file_hash in file_hashes:
                    categorized['duplicates'].append((pdf_path, file_hashes[file_hash]))
                    self.stats['duplicate_files'] += 1
                else:
                    categorized['valid'].append(pdf_path)
                    file_hashes[file_hash] = pdf_path
                    self.stats['valid_files'] += 1
            elif category == 'empty':
                categorized['empty'].append(pdf_path)
                self.stats['empty_files'] += 1
            else:  # corrupted
                categorized['corrupted'].append(pdf_path)
                self.stats['corrupted_files'] += 1
        
        # 打印统计
        print(f"\n扫描结果:")
        print(f"  有效文件: {self.stats['valid_files']}")
        print(f"  空文件: {self.stats['empty_files']}")
        print(f"  损坏文件: {self.stats['corrupted_files']}")
        print(f"  重复文件: {self.stats['duplicate_files']}")
        
        return categorized
    
    def _check_pdf_status(self, pdf_path: Path) -> str:
        """检查PDF文件状态"""
        try:
            # 检查文件大小
            if pdf_path.stat().st_size < 1024:  # 小于1KB
                return 'empty'
            
            # 尝试打开PDF
            with pdfplumber.open(pdf_path) as pdf:
                if len(pdf.pages) == 0:
                    return 'empty'
                
                # 尝试提取第一页文本
                try:
                    text = pdf.pages[0].extract_text()
                    if text and len(text.strip()) > 10:
                        return 'valid'
                    else:
                        # 可能是扫描版或空白页
                        return 'empty'
                except:
                    return 'corrupted'
                    
        except Exception as e:
            return 'corrupted'
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """计算文件哈希值"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def clean_files(self, categorized: Dict[str, List[Path]], 
                   move_corrupted: bool = True,
                   remove_duplicates: bool = True) -> None:
        """
        清理文件
        
        Args:
            categorized: 分类后的文件字典
            move_corrupted: 是否移动损坏文件
            remove_duplicates: 是否移除重复文件
        """
        print(f"\n{'='*80}")
        print("清理文件")
        print(f"{'='*80}")
        
        # 移动损坏文件
        if move_corrupted and categorized['corrupted']:
            print(f"\n移动 {len(categorized['corrupted'])} 个损坏文件...")
            for file_path in categorized['corrupted']:
                dest = self.corrupted_dir / file_path.name
                shutil.move(str(file_path), str(dest))
                print(f"  移动: {file_path.name} -> corrupted_backup/")
        
        # 处理重复文件
        if remove_duplicates and categorized['duplicates']:
            print(f"\n处理 {len(categorized['duplicates'])} 个重复文件...")
            for dup_file, original_file in categorized['duplicates']:
                dest = self.duplicate_dir / dup_file.name
                shutil.move(str(dup_file), str(dest))
                print(f"  移动: {dup_file.name} -> duplicate_backup/ (原文件: {original_file.name})")
    
    def fix_empty_pdfs(self, empty_files: List[Path], 
                      csv_path: str = "data/Company_Financial_report.csv") -> Dict[str, int]:
        """
        修复空PDF文件
        
        Args:
            empty_files: 空文件列表
            csv_path: 包含下载链接的CSV文件路径
        
        Returns:
            修复统计
        """
        if not empty_files:
            print("\n没有需要修复的空文件")
            return {'fixed': 0, 'failed': 0}
        
        print(f"\n{'='*80}")
        print(f"修复空PDF文件")
        print(f"{'='*80}")
        print(f"需要修复: {len(empty_files)} 个文件")
        
        # 加载URL映射
        url_mapping = self._load_url_mapping(csv_path)
        
        if not url_mapping:
            print("错误: 无法加载URL映射")
            return {'fixed': 0, 'failed': len(empty_files)}
        
        fixed_count = 0
        failed_count = 0
        
        for pdf_path in tqdm(empty_files, desc="修复文件"):
            # 查找对应的URL
            url = self._find_url_for_file(pdf_path.name, url_mapping)
            
            if url:
                # 备份原文件
                backup_path = self.backup_dir / f"{pdf_path.stem}_empty{pdf_path.suffix}"
                shutil.copy2(pdf_path, backup_path)
                
                # 尝试重新下载
                if self._download_pdf(url, pdf_path):
                    # 验证下载的文件
                    if self._check_pdf_status(pdf_path) == 'valid':
                        fixed_count += 1
                        self.stats['fixed_files'] += 1
                    else:
                        # 恢复备份
                        shutil.copy2(backup_path, pdf_path)
                        failed_count += 1
                else:
                    failed_count += 1
            else:
                failed_count += 1
            
            # 避免请求过快
            time.sleep(0.5)
        
        print(f"\n修复结果:")
        print(f"  成功修复: {fixed_count}")
        print(f"  修复失败: {failed_count}")
        
        return {'fixed': fixed_count, 'failed': failed_count}
    
    def _load_url_mapping(self, csv_path: str) -> Dict[str, str]:
        """加载文件名到URL的映射"""
        try:
            df = pd.read_csv(csv_path)
            mapping = {}
            
            for _, row in df.iterrows():
                if pd.notna(row.get('Report_URL')):
                    # 生成标准化的文件名
                    company = row.get('Company', '').replace(' ', '_').replace('/', '_')
                    year = str(row.get('Year', ''))
                    report_type = row.get('Report_Type', '').replace(' ', '_')
                    
                    filename = f"{company}_{year}_{report_type}.pdf"
                    mapping[filename.lower()] = row['Report_URL']
            
            return mapping
            
        except Exception as e:
            print(f"加载URL映射失败: {str(e)}")
            return {}
    
    def _find_url_for_file(self, filename: str, url_mapping: Dict[str, str]) -> Optional[str]:
        """查找文件对应的URL"""
        # 直接匹配
        if filename.lower() in url_mapping:
            return url_mapping[filename.lower()]
        
        # 模糊匹配
        for mapped_name, url in url_mapping.items():
            if filename.lower().replace('_', '') == mapped_name.replace('_', ''):
                return url
        
        return None
    
    def _download_pdf(self, url: str, output_path: Path) -> bool:
        """下载PDF文件"""
        try:
            # 处理PDF viewer URL
            actual_url = self._extract_pdf_url(url)
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(actual_url, headers=headers, timeout=30, stream=True)
            
            if response.status_code == 200:
                # 检查内容类型
                content_type = response.headers.get('content-type', '').lower()
                if 'pdf' in content_type or response.content[:4] == b'%PDF':
                    # 下载文件
                    with open(output_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    return True
            
            self.stats['download_failed'] += 1
            return False
            
        except Exception as e:
            self.stats['download_failed'] += 1
            return False
    
    def _extract_pdf_url(self, url: str) -> str:
        """从viewer URL提取实际PDF URL"""
        if 'pdf-viewer' in url and 'file=' in url:
            parsed = urlparse(url)
            params = parse_qs(parsed.query)
            if 'file' in params:
                pdf_url = unquote(params['file'][0])
                return pdf_url
        return url
    
    def generate_inventory_report(self, output_dir: str = "output") -> None:
        """生成文件清单报告"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 收集所有文件信息
        inventory = []
        
        # 主目录文件
        for pdf_path in self.data_dir.glob("*.pdf"):
            info = {
                'filename': pdf_path.name,
                'location': 'main',
                'size_mb': pdf_path.stat().st_size / 1024 / 1024,
                'status': self._check_pdf_status(pdf_path),
                'modified_date': datetime.fromtimestamp(pdf_path.stat().st_mtime).strftime("%Y-%m-%d")
            }
            inventory.append(info)
        
        # 备份目录文件
        for subdir in [self.backup_dir, self.corrupted_dir, self.duplicate_dir]:
            location = subdir.name
            for pdf_path in subdir.glob("*.pdf"):
                info = {
                    'filename': pdf_path.name,
                    'location': location,
                    'size_mb': pdf_path.stat().st_size / 1024 / 1024,
                    'status': 'backup',
                    'modified_date': datetime.fromtimestamp(pdf_path.stat().st_mtime).strftime("%Y-%m-%d")
                }
                inventory.append(info)
        
        # 创建DataFrame并保存
        df = pd.DataFrame(inventory)
        
        # 保存Excel报告
        excel_file = output_path / f"pdf_inventory_{timestamp}.xlsx"
        with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
            # 主清单
            df.to_excel(writer, sheet_name='文件清单', index=False)
            
            # 统计摘要
            summary_data = {
                '类别': ['总文件数', '有效文件', '空文件', '损坏文件', '重复文件', '已修复'],
                '数量': [
                    self.stats['total_files'],
                    self.stats['valid_files'],
                    self.stats['empty_files'],
                    self.stats['corrupted_files'],
                    self.stats['duplicate_files'],
                    self.stats['fixed_files']
                ]
            }
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='统计摘要', index=False)
        
        # 保存JSON统计
        stats_file = output_path / f"pdf_stats_{timestamp}.json"
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': timestamp,
                'statistics': self.stats,
                'file_count_by_location': df['location'].value_counts().to_dict(),
                'file_count_by_status': df['status'].value_counts().to_dict(),
                'total_size_gb': df['size_mb'].sum() / 1024
            }, f, ensure_ascii=False, indent=2)
        
        print(f"\n清单报告已生成:")
        print(f"  - Excel报告: {excel_file}")
        print(f"  - 统计信息: {stats_file}")


def test_pdf_manager():
    """测试PDF管理器"""
    manager = PDFManager()
    
    print("PDF文件管理器测试")
    print("=" * 80)
    
    # 扫描文件
    categorized = manager.scan_pdf_files()
    
    # 显示部分结果
    if categorized['empty']:
        print(f"\n空文件示例 (前5个):")
        for f in categorized['empty'][:5]:
            print(f"  - {f.name}")
    
    # 生成报告
    manager.generate_inventory_report()


if __name__ == "__main__":
    test_pdf_manager()