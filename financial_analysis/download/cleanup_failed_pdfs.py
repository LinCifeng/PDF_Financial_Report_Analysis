#!/usr/bin/env python3
"""
清理失败和损坏的PDF文件
Clean Failed and Corrupted PDF Files

作者: Lin Cifeng
创建: 2025-08-12
"""

import os
import shutil
from pathlib import Path
from typing import Dict, List, Tuple
import pdfplumber
import json
from datetime import datetime


def check_pdf_validity(pdf_path: Path) -> Tuple[bool, str]:
    """
    检查PDF文件是否有效
    
    Returns:
        (is_valid, reason)
    """
    import warnings
    warnings.filterwarnings('ignore')
    
    # 检查文件大小
    file_size = pdf_path.stat().st_size
    if file_size < 50 * 1024:  # 小于50KB - 很可能是错误页面
        return False, "file_too_small"
    
    if file_size > 100 * 1024 * 1024:  # 大于100MB
        return False, "file_too_large"
    
    # 尝试打开PDF
    try:
        with pdfplumber.open(pdf_path) as pdf:
            # 检查页数
            if len(pdf.pages) == 0:
                return False, "no_pages"
            
            # 检查多页以确保是真实报告
            pages_to_check = min(3, len(pdf.pages))
            all_text = ""
            
            for i in range(pages_to_check):
                try:
                    page = pdf.pages[i]
                    text = page.extract_text()
                    if text:
                        all_text += text + " "
                except:
                    pass
            
            # 如果完全没有文本，可能是扫描版
            if not all_text or len(all_text.strip()) < 100:
                return False, "no_text_scanned"
            
            # 检查是否是HTML错误页面内容
            if "<!DOCTYPE" in all_text or "window.dataLayer" in all_text or "googletagmanager" in all_text:
                return False, "html_error_page"
            
            # 检查财务相关关键词
            import re
            financial_keywords = [
                r'资产|asset|負債|liability|收入|revenue|利润|profit|income|equity|cash',
                r'财务|financial|報告|report|年度|annual|季度|quarter',
                r'银行|bank|公司|company|limited|有限'
            ]
            
            has_financial_terms = any(re.search(kw, all_text, re.IGNORECASE) for kw in financial_keywords)
            
            # 简单检查是否包含数字
            numbers = re.findall(r'\d+', all_text)
            has_numbers = len(numbers) >= 10  # 降低要求
            
            if has_financial_terms or has_numbers:
                return True, "valid"
            else:
                return False, "not_financial_report"
            
    except Exception as e:
        error_msg = str(e).lower()
        if 'no /root object' in error_msg:
            return False, "corrupted_no_root"
        elif 'eof marker not found' in error_msg:
            return False, "corrupted_eof"
        elif 'timeout' in error_msg:
            return False, "timeout_corrupted"
        elif 'data-loss' in error_msg:
            return False, "corrupted_data_loss"
        else:
            return False, "corrupted"


def cleanup_failed_pdfs(
    input_dir: str = "data/raw_reports",
    backup_dir: str = "data/failed_backup",
    dry_run: bool = False
) -> Dict:
    """
    清理失败和损坏的PDF文件
    
    Args:
        input_dir: PDF文件目录
        backup_dir: 备份目录
        dry_run: 只分析不删除
    
    Returns:
        统计信息
    """
    input_path = Path(input_dir)
    backup_path = Path(backup_dir)
    
    if not input_path.exists():
        print(f"错误: 目录 {input_dir} 不存在")
        return {}
    
    # 创建备份目录
    if not dry_run:
        backup_path.mkdir(parents=True, exist_ok=True)
        
        # 按失败原因创建子目录
        (backup_path / "corrupted").mkdir(exist_ok=True)
        (backup_path / "too_small").mkdir(exist_ok=True)
        (backup_path / "too_large").mkdir(exist_ok=True)
        (backup_path / "scanned").mkdir(exist_ok=True)
        (backup_path / "not_financial").mkdir(exist_ok=True)
        (backup_path / "html_error").mkdir(exist_ok=True)
    
    # 获取所有PDF文件
    pdf_files = list(input_path.glob("*.pdf"))
    total_files = len(pdf_files)
    
    print(f"开始检查 {total_files} 个PDF文件...")
    print("=" * 60)
    
    # 统计
    stats = {
        "total": total_files,
        "valid": 0,
        "invalid": 0,
        "corrupted": 0,
        "too_small": 0,
        "too_large": 0,
        "scanned": 0,
        "not_financial": 0,
        "deleted_size_mb": 0
    }
    
    # 详细记录
    invalid_files = []
    valid_files = []
    
    # 检查每个文件
    for i, pdf_path in enumerate(pdf_files, 1):
        if i % 100 == 0:
            print(f"进度: {i}/{total_files} ({i/total_files*100:.1f}%)")
        
        is_valid, reason = check_pdf_validity(pdf_path)
        
        if is_valid:
            stats["valid"] += 1
            valid_files.append(pdf_path.name)
        else:
            stats["invalid"] += 1
            file_size_mb = pdf_path.stat().st_size / 1024 / 1024
            
            # 分类统计
            if "corrupted" in reason:
                stats["corrupted"] += 1
                backup_subdir = "corrupted"
            elif reason == "file_too_small":
                stats["too_small"] += 1
                backup_subdir = "too_small"
            elif reason == "file_too_large":
                stats["too_large"] += 1
                backup_subdir = "too_large"
            elif reason == "no_text_scanned":
                stats["scanned"] += 1
                backup_subdir = "scanned"
            elif reason == "not_financial_report":
                stats["not_financial"] += 1
                backup_subdir = "not_financial"
            elif reason == "html_error_page":
                stats["not_financial"] += 1
                backup_subdir = "html_error"
            else:
                backup_subdir = "corrupted"
            
            invalid_files.append({
                "name": pdf_path.name,
                "reason": reason,
                "size_mb": file_size_mb
            })
            
            stats["deleted_size_mb"] += file_size_mb
            
            # 移动文件到备份目录
            if not dry_run:
                backup_file = backup_path / backup_subdir / pdf_path.name
                try:
                    shutil.move(str(pdf_path), str(backup_file))
                    print(f"  ❌ {pdf_path.name[:50]} -> {backup_subdir}/ ({reason})")
                except Exception as e:
                    print(f"  ⚠️ 无法移动 {pdf_path.name}: {e}")
    
    # 打印统计
    print("\n" + "=" * 60)
    print("清理统计")
    print("=" * 60)
    print(f"总文件数: {stats['total']}")
    print(f"有效文件: {stats['valid']} ({stats['valid']/stats['total']*100:.1f}%)")
    print(f"无效文件: {stats['invalid']} ({stats['invalid']/stats['total']*100:.1f}%)")
    
    if stats['invalid'] > 0:
        print(f"\n无效文件分类:")
        print(f"  损坏文件: {stats['corrupted']}")
        print(f"  文件过小: {stats['too_small']}")
        print(f"  文件过大: {stats['too_large']}")
        print(f"  扫描版PDF: {stats['scanned']}")
        print(f"  非财务报告: {stats['not_financial']}")
        print(f"\n释放空间: {stats['deleted_size_mb']:.2f} MB")
    
    # 保存清理报告
    if not dry_run:
        report = {
            "timestamp": datetime.now().isoformat(),
            "stats": stats,
            "invalid_files": invalid_files[:100],  # 只保存前100个
            "valid_count": len(valid_files)
        }
        
        report_file = Path("output/cleanup_report.json")
        report_file.parent.mkdir(exist_ok=True)
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n清理报告已保存至: {report_file}")
        
        if stats['invalid'] > 0:
            print(f"无效文件已移至: {backup_path}")
    else:
        print("\n[DRY RUN] 未实际删除任何文件")
    
    return stats


def restore_backups(backup_dir: str = "data/failed_backup") -> int:
    """
    恢复备份的文件
    
    Returns:
        恢复的文件数
    """
    backup_path = Path(backup_dir)
    if not backup_path.exists():
        print(f"备份目录不存在: {backup_dir}")
        return 0
    
    target_dir = Path("data/raw_reports")
    restored = 0
    
    for pdf_file in backup_path.rglob("*.pdf"):
        target_file = target_dir / pdf_file.name
        if not target_file.exists():
            try:
                shutil.move(str(pdf_file), str(target_file))
                restored += 1
                print(f"恢复: {pdf_file.name}")
            except Exception as e:
                print(f"无法恢复 {pdf_file.name}: {e}")
    
    print(f"\n共恢复 {restored} 个文件")
    return restored


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='清理失败和损坏的PDF文件')
    parser.add_argument('--dry-run', action='store_true', help='只分析不删除')
    parser.add_argument('--restore', action='store_true', help='恢复备份文件')
    parser.add_argument('--input-dir', default='data/raw_reports', help='输入目录')
    parser.add_argument('--backup-dir', default='data/failed_backup', help='备份目录')
    
    args = parser.parse_args()
    
    if args.restore:
        restore_backups(args.backup_dir)
    else:
        cleanup_failed_pdfs(
            input_dir=args.input_dir,
            backup_dir=args.backup_dir,
            dry_run=args.dry_run
        )