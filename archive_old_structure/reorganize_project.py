#!/usr/bin/env python3
"""
重新组织项目结构
Reorganize Project Structure
"""
import os
import shutil
from pathlib import Path

# 定义新的项目结构
NEW_STRUCTURE = {
    "financial_analysis": {
        "__init__.py": "# Financial Analysis Package",
        "extract": {
            "__init__.py": "# Data Extraction Module",
            "simple.py": "scripts/simple_extract.py",
            "optimized.py": "scripts/extract_data_optimized.py",
            "pdf_extractor.py": "src/extractors/pdf/basic.py",
            "table_extractor.py": "src/extractors/pdf/table.py",
        },
        "download": {
            "__init__.py": "# Download Module",
            "download_reports.py": "scripts/download_all_reports.py",
        },
        "analyze": {
            "__init__.py": "# Analysis Module",
            "companies.py": "scripts/analysis/analyze_companies.py",
            "coverage.py": "scripts/analysis/analyze_download_coverage.py",
        },
        "utils": {
            "__init__.py": "# Utility Module",
            "clean_pdfs.py": "scripts/check_and_clean_pdfs.py",
            "clean_duplicates.py": "scripts/clean_duplicates.py",
            "generate_summary.py": "scripts/generate_download_summary.py",
        },
        "models.py": "src/core/models.py",
        "config.py": "src/core/config.py",
    },
    "main.py": "# 主入口文件（新建）",
    "run_extraction.py": "# 数据提取脚本（新建）",
    "run_download.py": "# 下载脚本（新建）",
}

def create_structure():
    """创建新的项目结构"""
    print("开始重组项目结构...")
    print("=" * 60)
    
    # 创建备份
    backup_dir = Path("backup_old_structure")
    if not backup_dir.exists():
        backup_dir.mkdir()
        
    # 备份旧目录
    for old_dir in ["scripts", "src"]:
        if Path(old_dir).exists():
            print(f"备份 {old_dir}/ -> backup_old_structure/{old_dir}/")
            shutil.copytree(old_dir, backup_dir / old_dir)
    
    # 备份根目录的Python文件
    root_py_files = [f for f in os.listdir('.') if f.endswith('.py') and f != 'reorganize_project.py']
    for py_file in root_py_files:
        print(f"备份 {py_file} -> backup_old_structure/{py_file}")
        shutil.copy2(py_file, backup_dir / py_file)
    
    print("\n创建新结构...")
    
    # 创建新的目录结构
    def create_from_dict(base_path, structure):
        for name, content in structure.items():
            path = base_path / name
            
            if isinstance(content, dict):
                # 创建目录
                path.mkdir(parents=True, exist_ok=True)
                create_from_dict(path, content)
            elif isinstance(content, str):
                if content.startswith("#"):
                    # 创建新文件
                    with open(path, 'w', encoding='utf-8') as f:
                        f.write(f'"""\n{content[2:]}\n"""\n')
                else:
                    # 复制旧文件
                    old_path = Path(content)
                    if old_path.exists():
                        print(f"移动 {content} -> {path}")
                        shutil.copy2(old_path, path)
    
    create_from_dict(Path('.'), NEW_STRUCTURE)
    
    print("\n清理旧文件...")
    
    # 删除旧目录和文件
    for old_dir in ["scripts", "src"]:
        if Path(old_dir).exists():
            shutil.rmtree(old_dir)
            print(f"删除旧目录: {old_dir}/")
    
    # 删除根目录的旧Python文件
    for py_file in root_py_files:
        if Path(py_file).exists():
            os.remove(py_file)
            print(f"删除旧文件: {py_file}")
    
    print("\n项目结构重组完成！")
    print("\n新的项目结构:")
    print("""
financial_analysis/          # 核心包
├── __init__.py
├── extract/                # 数据提取模块
│   ├── simple.py          # 简单提取
│   ├── optimized.py       # 优化提取
│   ├── pdf_extractor.py   # PDF提取器
│   └── table_extractor.py # 表格提取器
├── download/              # 下载模块
│   └── download_reports.py
├── analyze/               # 分析模块
│   ├── companies.py
│   └── coverage.py
├── utils/                 # 工具模块
│   ├── clean_pdfs.py
│   ├── clean_duplicates.py
│   └── generate_summary.py
├── models.py              # 数据模型
└── config.py              # 配置

main.py                    # 主入口
run_extraction.py          # 提取脚本
run_download.py            # 下载脚本
    """)

if __name__ == "__main__":
    create_structure()