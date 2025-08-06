#!/usr/bin/env python3
"""清理旧文件"""
import os
import shutil

# 要删除的旧文件和目录
OLD_ITEMS = [
    # 根目录的旧脚本
    "fast_extract.py",
    "full_extraction.py", 
    "quick_extract.py",
    "run_extraction.py",
    "simple_extraction.py",
    "test_extract.py",
    "reorganize_project.py",
    
    # 旧目录
    "scripts",
    "src",
    "backup_old_structure",
]

print("清理旧文件...")
for item in OLD_ITEMS:
    if os.path.isfile(item):
        os.remove(item)
        print(f"删除文件: {item}")
    elif os.path.isdir(item):
        shutil.rmtree(item)
        print(f"删除目录: {item}/")

print("\n清理完成！")