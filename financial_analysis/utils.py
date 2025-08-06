"""
工具函数模块
Utility Functions Module
"""
import os
import shutil
from pathlib import Path
from typing import List, Dict
import pdfplumber


def check_pdf_integrity(pdf_path: Path) -> bool:
    """检查PDF文件完整性"""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            # 尝试读取第一页
            if len(pdf.pages) > 0:
                pdf.pages[0].extract_text()
                return True
    except:
        return False
    return False


def clean_pdfs(pdf_dir: str = "data/raw_reports",
               backup_dir: str = "data/corrupted_backup") -> Dict:
    """
    检查并清理损坏的PDF文件
    
    Args:
        pdf_dir: PDF目录
        backup_dir: 备份目录
        
    Returns:
        清理统计
    """
    pdf_path = Path(pdf_dir)
    backup_path = Path(backup_dir)
    backup_path.mkdir(parents=True, exist_ok=True)
    
    pdf_files = list(pdf_path.glob("*.pdf"))
    print(f"Checking {len(pdf_files)} PDF files...")
    
    corrupted = []
    valid = []
    
    for pdf_file in pdf_files:
        if check_pdf_integrity(pdf_file):
            valid.append(pdf_file.name)
        else:
            corrupted.append(pdf_file.name)
            # 移动到备份目录
            shutil.move(str(pdf_file), str(backup_path / pdf_file.name))
            print(f"✗ Corrupted: {pdf_file.name}")
    
    stats = {
        'total': len(pdf_files),
        'valid': len(valid),
        'corrupted': len(corrupted),
        'corrupted_files': corrupted
    }
    
    print(f"\n{'='*60}")
    print(f"PDF check completed!")
    print(f"Total: {stats['total']}")
    print(f"Valid: {stats['valid']}")
    print(f"Corrupted: {stats['corrupted']}")
    
    return stats


def generate_summary(output_dir: str = "output") -> None:
    """生成项目摘要"""
    output_path = Path(output_dir)
    
    # 统计各类文件
    extraction_files = list(output_path.glob("extraction_results_*.csv"))
    
    print(f"\nProject Summary")
    print("="*60)
    
    # 数据文件统计
    data_dir = Path("data/raw_reports")
    if data_dir.exists():
        pdf_count = len(list(data_dir.glob("*.pdf")))
        html_count = len(list(data_dir.glob("*.html")))
        print(f"\nData files:")
        print(f"  PDF files: {pdf_count}")
        print(f"  HTML files: {html_count}")
        print(f"  Total: {pdf_count + html_count}")
    
    # 提取结果统计
    print(f"\nExtraction results:")
    print(f"  Result files: {len(extraction_files)}")
    if extraction_files:
        latest = max(extraction_files, key=lambda f: f.stat().st_mtime)
        print(f"  Latest: {latest.name}")
    
    # 输出目录大小
    total_size = sum(f.stat().st_size for f in output_path.rglob("*") if f.is_file())
    print(f"\nOutput directory size: {total_size / 1024 / 1024:.1f} MB")