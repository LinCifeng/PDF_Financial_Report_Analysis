# 财务分析系统 v3.1

Financial Analysis System v3.1

**作者 Author**: Lin Cifeng

## 项目简介 Project Overview

本项目是一个自动化的财务数据提取和分析系统，专门用于从 PDF 和 HTML 格式的财务报表中提取关键财务指标。系统针对香港虚拟银行、金融科技公司和国际数字银行的财务报告进行了深度优化，支持批量处理和多种提取策略。

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

# 工具功能
python main.py utils --clean-pdfs  # 清理损坏的PDF
python main.py utils --summary      # 生成项目摘要
```

## 📊 当前数据统计 Current Statistics

- **财报数据库**: 1,478 份财报链接，涵盖 126 家公司
- **已下载财报**: 1,325 份（1,158 PDF + 167 HTML）
- **下载覆盖率**: 89.6%
- **提取成功率**: ~34% (正则) / ~60% (Master提取器)
- **支持格式**: PDF, HTML
- **支持语言**: 中文、英文、日文

## 🏗️ 项目结构 Project Structure

```
FinancialAnalysis/
├── main.py                     # 主入口文件
├── financial_analysis/         # 核心功能包
│   ├── __init__.py
│   ├── models.py              # 数据模型
│   ├── download/              # 下载模块
│   │   ├── downloader.py      # 下载器
│   │   ├── pdf_utils.py       # PDF工具函数
│   │   ├── batch_processor.py # 批处理器
│   │   ├── cross_validator.py # 交叉验证器
│   │   └── pdf_manager.py     # PDF管理器
│   ├── extractor/             # 提取模块
│   │   ├── regex_extractor.py # 正则提取器
│   │   ├── master_extractor.py# 主提取器(推荐)
│   │   └── llm_extractor.py   # LLM提取器
│   ├── analysis/              # 分析模块
│   │   └── analyzer.py        # 数据分析器
│   └── visualization/         # 可视化模块
│       └── visualizer.py      # 图表生成器
├── test/                      # 测试脚本
│   ├── utilities/             # 测试工具
│   ├── analyzers/             # 分析测试
│   └── visualizers/           # 可视化测试
├── data/                      # 数据目录
│   ├── raw_reports/           # PDF/HTML财报
│   └── Company_Financial_report.csv
├── output/                    # 输出结果
│   ├── results/               # 提取结果
│   └── reports/               # 分析报告
├── config/                    # 配置文件
└── requirements.txt           # 依赖包
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
# 基础正则提取
python main.py extract

# 使用Master提取器（推荐）
python main.py extract --method master

# 启用LLM增强（需要API密钥）
python main.py extract --use-llm --limit 50

# 调整批处理大小
python main.py extract --batch-size 200
```

### 3. 数据分析

```bash
# 分析公司数据
python main.py analyze --type companies

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

## 🔧 高级功能 Advanced Features

### 多策略提取

系统提供三种提取策略：

1. **RegexExtractor**: 基于正则表达式，速度快，适合标准格式
2. **LLMExtractor**: 使用DeepSeek API，智能理解复杂布局
3. **MasterExtractor**: 综合多种方法，成功率最高（推荐）

### 批量处理

```python
from financial_analysis.download.batch_processor import BatchProcessor

processor = BatchProcessor()
processor.process_batch(pdf_files, batch_size=100)
```

### 交叉验证

```python
from financial_analysis.download.cross_validator import CrossValidator

validator = CrossValidator()
validator.validate_results(extraction_results)
```

## 📈 提取的财务指标

- **资产负债表**: 总资产、总负债、股东权益
- **损益表**: 营业收入、净利润/亏损
- **现金流量表**: 经营现金流、投资现金流、融资现金流
- **关键比率**: ROA、ROE、资产负债率等

## 🛠️ 配置说明

### 环境变量

```bash
# 设置DeepSeek API密钥（可选）
export DEEPSEEK_API_KEY="your-api-key"
```

### 输出格式

提取结果支持多种格式：
- CSV: 默认格式，便于Excel处理
- JSON: 结构化数据，便于程序处理
- Excel: 带格式的表格输出

## 📝 注意事项

1. **大文件处理**: 系统自动处理大型PDF（>100MB）
2. **损坏文件**: 自动检测并隔离损坏的PDF文件
3. **API限制**: 使用LLM提取时注意API调用限制和成本
4. **内存管理**: 批量处理时自动管理内存使用

## 🤝 贡献指南

欢迎提交Issue和Pull Request来改进系统。

## 📄 许可证

MIT License

## 📞 联系方式

如有问题或建议，请通过GitHub Issues联系。

---

**最后更新 Last Updated**: 2025-08-10