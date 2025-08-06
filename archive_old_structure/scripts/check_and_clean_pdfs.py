#!/usr/bin/env python3
"""
检查并清理损坏的PDF文件
Check and clean corrupted PDF files
"""
import os
from pathlib import Path
import subprocess

def check_pdf_validity(filepath):
    """检查PDF文件是否有效"""
    try:
        # 检查文件大小
        size = os.path.getsize(filepath)
        if size < 1024:  # 小于1KB的文件可能有问题
            return False, f"文件太小 ({size} bytes)"
        
        # 检查文件头
        with open(filepath, 'rb') as f:
            header = f.read(8)
            if not header.startswith(b'%PDF'):
                return False, "不是有效的PDF文件头"
        
        # 使用pdfinfo命令检查（如果可用）
        try:
            result = subprocess.run(
                ['pdfinfo', filepath],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode != 0:
                return False, "pdfinfo检查失败"
        except (subprocess.TimeoutExpired, FileNotFoundError):
            # pdfinfo不可用，跳过这个检查
            pass
        
        return True, "有效的PDF文件"
    
    except Exception as e:
        return False, f"检查时出错: {str(e)}"

def main():
    # 设置路径
    project_root = Path(__file__).parent.parent
    pdf_dir = project_root / 'data' / 'raw_reports'
    
    # 检查目录是否存在
    if not pdf_dir.exists():
        print(f"错误: 目录不存在 {pdf_dir}")
        return
    
    # 获取所有PDF文件
    pdf_files = list(pdf_dir.glob('*.pdf'))
    print(f"找到 {len(pdf_files)} 个PDF文件")
    
    # 检查每个文件
    valid_count = 0
    invalid_files = []
    
    print("\n开始检查PDF文件...")
    print("-" * 50)
    
    for pdf_file in pdf_files:
        is_valid, message = check_pdf_validity(pdf_file)
        
        if is_valid:
            valid_count += 1
        else:
            invalid_files.append((pdf_file, message))
            print(f"✗ {pdf_file.name}: {message}")
    
    # 统计结果
    print("-" * 50)
    print(f"\n检查完成:")
    print(f"- 有效文件: {valid_count}")
    print(f"- 无效文件: {len(invalid_files)}")
    
    # 如果有无效文件，询问是否删除
    if invalid_files:
        print("\n以下文件可能已损坏:")
        for i, (file, reason) in enumerate(invalid_files, 1):
            print(f"{i}. {file.name} - {reason}")
        
        # 创建备份目录
        backup_dir = pdf_dir / 'corrupted_backup'
        backup_dir.mkdir(exist_ok=True)
        
        print(f"\n将移动损坏的文件到: {backup_dir}")
        
        # 移动文件
        moved_count = 0
        for file, _ in invalid_files:
            try:
                backup_path = backup_dir / file.name
                file.rename(backup_path)
                moved_count += 1
                print(f"已移动: {file.name}")
            except Exception as e:
                print(f"移动失败 {file.name}: {e}")
        
        print(f"\n已移动 {moved_count} 个损坏的文件")
    
    # 显示当前状态
    remaining_pdfs = list(pdf_dir.glob('*.pdf'))
    print(f"\n当前有效的PDF文件数: {len(remaining_pdfs)}")

if __name__ == "__main__":
    main()