# 财务分析系统 v3.1
Financial Analysis System v3.1

**作者 Author**: Lin Cifeng

## 项目简介 Project Overview

本项目是一个自动化的财务数据提取和分析系统，专门用于从PDF和HTML格式的财务报表中提取关键财务指标。系统针对香港虚拟银行、金融科技公司和国际数字银行的财务报告进行了深度优化，支持批量处理和多种提取策略。

This is an automated financial data extraction and analysis system designed to extract key financial metrics from PDF and HTML financial reports. The system is optimized for Hong Kong virtual banks, fintech companies, and international digital banks, supporting batch processing and multiple extraction strategies.

## 🚀 快速开始 Quick Start

### 安装依赖 Install Dependencies
```bash
pip install -r requirements.txt
```

### 基本用法 Basic Usage
```bash
# 下载财报
python main.py download

# 提取数据
python main.py extract

# 分析结果
python main.py analyze
```

## 📊 当前数据统计 Current Statistics

- **财报数据库**: 1,478份财报链接，涵盖126家公司
- **已下载财报**: 1,224份（1,059 PDF + 165 HTML）
- **下载覆盖率**: 82.8%
- **提取成功率**: ~34% (基于测试样本)
- **支持格式**: PDF, HTML
- **支持语言**: 中文、英文、日文

## 🏗️ 项目结构 Project Structure

```
FinancialAnalysis/
├── main.py                    # 主入口文件
├── financial_analysis/        # 核心功能包
│   ├── __init__.py           
│   ├── extract.py            # 数据提取
│   ├── download.py           # 财报下载
│   ├── analyze.py            # 数据分析
│   ├── utils.py              # 工具函数
│   └── models.py             # 数据模型（包含扩展模型）
├── scripts/                  # 工具脚本（已重组）
│   ├── extractors/           # 提取器
│   │   └── master_extractor.py
│   ├── analyzers/            # 分析工具
│   │   ├── data_analyzer.py
│   │   ├── analyze_reports.py
│   │   └── ...
│   ├── visualizers/          # 可视化工具
│   │   ├── visualize_performance.py
│   │   └── ...
│   ├── utilities/            # 实用工具
│   │   ├── batch_processor.py
│   │   ├── cross_validator.py
│   │   ├── pdf_manager.py
│   │   └── deepseek_client.py
│   └── README.md
├── data/                     # 数据目录
│   ├── raw_reports/          # PDF/HTML财报（1,224个文件）
│   └── Company_Financial_report.csv
├── output/                   # 输出结果（已整理）
│   ├── results/              # 提取结果CSV
│   ├── reports/              # 分析报告
│   ├── cache/                # LLM缓存
│   └── visualizations/       # 图表输出
├── config/                   # 配置文件
├── docs/                     # 文档
│   └── CLAUDE.md            # Claude配置指南
└── requirements.txt          # 依赖包
```

## 📖 详细用法 Detailed Usage

### 1. 下载财报
```bash
# 下载所有财报
python main.py download

# 限制下载数量
python main.py download --limit 100

# 调整并发数
python main.py download --workers 10
```

### 2. 提取财务数据
```bash
# 提取所有PDF
python main.py extract

# 限制处理文件数
python main.py extract --limit 50

# 调整批处理大小
python main.py extract --batch-size 200
```

### 3. 数据分析
```bash
# 分析公司覆盖情况
python main.py analyze

# 分析提取结果
python main.py analyze --type extraction
```

### 4. 工具功能
```bash
# 检查并清理损坏的PDF
python main.py utils --clean-pdfs

# 生成项目摘要
python main.py utils --summary
```

## 🔑 主要功能 Key Features

- **智能提取**: 使用正则表达式匹配中英文财务数据
- **并发下载**: 支持多线程并发下载提高效率
- **批量处理**: 可处理大量PDF/HTML文件
- **数据分析**: 自动生成统计报告和可视化图表
- **错误处理**: 自动识别和隔离损坏文件
- **多策略提取**: 支持正则、OCR、LLM等多种提取方法
- **交叉验证**: 多重验证确保数据准确性
- **缓存机制**: LLM结果缓存，避免重复调用

## 📈 提取指标 Extracted Metrics

- 总资产 (Total Assets)
- 总负债 (Total Liabilities)
- 营业收入 (Revenue)
- 净利润 (Net Profit/Loss)

## 🛠️ 技术栈 Tech Stack

### 核心依赖 Core Dependencies
- Python 3.6+
- pdfplumber - PDF文本提取
- PyPDF2 - PDF处理
- requests - 网络请求
- concurrent.futures - 并发处理

### 数据处理 Data Processing
- pandas - 数据分析框架
- numpy - 数值计算
- openpyxl - Excel文件处理

### 可视化 Visualization
- matplotlib - 图表绘制
- seaborn - 统计图表

### Web相关 Web Related
- selenium - 网页自动化
- beautifulsoup4 - HTML解析
- lxml - XML/HTML处理

### 可选组件 Optional Components
- PyMuPDF - PDF转图像
- pytesseract - OCR文字识别
- paddleocr - 高精度OCR

## 📝 注意事项 Notes

1. 确保有足够的磁盘空间存储财报文件（约15GB）
2. 部分PDF可能因加密或损坏无法提取
3. 网络下载可能因服务器限制而失败

## 🚀 高级功能 Advanced Features

### 使用主提取器
```bash
# 使用主提取器（推荐）
python scripts/extractors/master_extractor.py

# 批量处理所有PDF
python scripts/utilities/batch_processor.py

# 交叉验证结果
python scripts/utilities/cross_validator.py
```

### 数据分析与可视化
```bash
# 生成综合分析报告
python scripts/analyzers/data_analyzer.py

# 生成性能可视化
python scripts/visualizers/visualize_performance.py

# 分析提取失败案例
python scripts/analyzers/analyze_extraction_failures.py
```

## 🔄 更新日志 Changelog

### v3.1 (2024-08-07)
- 添加高级脚本工具集
- 增强LLM集成功能
- 改进提取算法准确率
- 添加数据可视化功能
- 优化项目文档结构

### v3.0 (2024-08-06)
- 完全重构项目结构
- 统一所有功能到单一包
- 简化命令行接口
- 提高代码可维护性

### v2.0
- 添加并发下载支持
- 改进数据提取算法
- 添加数据分析功能

### v1.0
- 初始版本
- 基础PDF提取功能

## ❓ 常见问题 FAQ

### Q: 如何处理加密的PDF文件？
A: 系统会自动跳过加密的PDF文件并记录到日志中。如需处理，请先手动解密。

### Q: 提取失败的常见原因？
A: 
- PDF文件损坏或加密
- 财务数据格式不标准
- 表格嵌入为图片而非文本

### Q: 如何提高提取成功率？
A: 
- 使用LLM增强提取模式
- 启用OCR处理扫描版PDF
- 使用交叉验证确保准确性

### Q: 支持哪些财务报表格式？
A: 支持标准的资产负债表、损益表、现金流量表等，中英文均可。

## 📧 联系方式 Contact

- 作者 Author: Lin Cifeng
- 项目地址 Repository: [GitHub](https://github.com/your-repo/FinancialAnalysis)

---

如有问题或建议，欢迎提交Issue！