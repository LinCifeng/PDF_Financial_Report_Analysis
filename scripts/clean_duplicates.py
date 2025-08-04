#!/usr/bin/env python3
"""
清理重复的财报文件
保留带有中文顿号(、)的版本，删除带下划线(_)的版本
"""
import os
from pathlib import Path
import shutil

def main():
    project_root = Path(__file__).parent.parent
    reports_dir = project_root / 'data' / 'raw_reports'
    backup_dir = project_root / 'data' / 'duplicate_backup'
    
    # 创建备份目录
    backup_dir.mkdir(exist_ok=True)
    
    # 查找所有带下划线的Q1_Q2格式文件
    duplicates = []
    for file in reports_dir.iterdir():
        if file.is_file() and 'Q1_Q2' in file.name:
            # 检查是否存在对应的中文顿号版本
            chinese_version = file.name.replace('Q1_Q2', 'Q1、Q2')
            chinese_path = reports_dir / chinese_version
            
            if chinese_path.exists():
                duplicates.append(file)
    
    print(f"找到 {len(duplicates)} 个重复文件")
    
    if duplicates:
        print("\n即将移动以下文件到备份目录:")
        for f in duplicates:
            print(f"  - {f.name}")
        
        # 移动重复文件
        moved = 0
        for file in duplicates:
            try:
                shutil.move(str(file), str(backup_dir / file.name))
                moved += 1
            except Exception as e:
                print(f"移动 {file.name} 失败: {e}")
        
        print(f"\n成功移动 {moved} 个重复文件到 {backup_dir}")
    else:
        print("没有找到重复文件")
    
    # 重新统计文件数量
    pdf_count = len(list(reports_dir.glob('*.pdf')))
    html_count = len(list(reports_dir.glob('*.html')))
    total = pdf_count + html_count
    
    print(f"\n清理后的文件统计:")
    print(f"  - PDF文件: {pdf_count}")
    print(f"  - HTML文件: {html_count}")
    print(f"  - 总计: {total}")

if __name__ == "__main__":
    main()