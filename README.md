# 📊 财务分析系统

这是一个用于分析金融机构财务报告的工具，可以从 PDF 文件中提取数据，进行财务分析，并生成报告和可视化图表。

## 🏗️ 项目结构

重构后的项目采用模块化结构：

```
financial_analyzer/
├── __init__.py                 # 包初始化文件
├── main.py                     # 主函数
├── data_extraction/            # 数据提取模块
│   ├── __init__.py
│   └── pdf_extractor.py        # PDF数据提取工具
├── analysis/                   # 分析模块
│   ├── __init__.py
│   ├── financial_analyzer.py   # 财务分析器
│   └── report_generator.py     # 报告生成器
├── visualization/              # 可视化模块
│   ├── __init__.py
│   └── chart_generator.py      # 图表生成器
└── utils/                      # 工具类模块
    └── __init__.py
```

## 📦 安装依赖

```bash
pip install -r requirements.txt
```

## 🚀 使用方法

### 📄 从 PDF 提取数据并生成报告

```bash
python run_analysis.py --pdf ./data/your_report.pdf --output ./output
```

### 🔍 仅提取数据

```bash
python run_analysis.py --pdf ./data/your_report.pdf --output ./output --extract-only
```

### 📝 使用已提取的数据生成报告

```bash
python run_analysis.py --json ./output/extracted_data.json --output ./output
```

### 🎯 不生成可视化图表

```bash
python run_analysis.py --pdf ./data/your_report.pdf --output ./output --no-viz
```

### 🔬 显示详细日志

```bash
python run_analysis.py --pdf ./data/your_report.pdf --output ./output --verbose
```

## ✨ 功能描述

1. **📑 数据提取**：从 PDF 财务报告中提取关键财务数据
2. **📈 财务分析**：计算财务比率，分析财务趋势
3. **📋 报告生成**：生成全面的财务分析报告
4. **📊 数据可视化**：创建收入结构对比图和财务比率雷达图

## 🏦 支持的报告类型

目前特别支持以下报告类型：

- 🏦 ZA Bank 财务报告

## 📜 许可证

[MIT](LICENSE)
