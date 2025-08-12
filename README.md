# 财务分析系统 v3.2

Financial Analysis System v3.2

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

# 监控提取进度
python main.py monitor

# 合并所有结果
python main.py merge

# 生成综合报告
python main.py report

# 分析结果
python main.py analyze

# 工具功能
python main.py utils --clean-pdfs  # 清理损坏的PDF
python main.py utils --summary      # 生成项目摘要
```

## 📊 当前数据统计 Current Statistics (更新: 2025-08-12)

- **财报数据库**: 1,478 份财报链接，涵盖 126 家公司
- **有效PDF文件**: 1,208 份（已清理26个损坏文件和167个HTML错误文件）
- **文件总大小**: 约15GB
- **成功提取**: 511 条财务记录（42.3%成功率，基于1,208份有效文件）
- **数据覆盖**: 56 家公司，2015-2024年
- **支持语言**: 中文（简体/繁体）、英文、日文

## 🏗️ 项目结构 Project Structure

```
FinancialAnalysis/
├── main.py                     # 主入口文件
├── install.sh                  # 安装脚本
├── requirements.txt            # 依赖包
├── README.md                   # 项目说明
├── CLAUDE.md                   # Claude AI指导文档
│
├── financial_analysis/         # 核心功能包 (策略模式重构2025-08-11)
│   ├── __init__.py
│   │
│   ├── download/              # 下载模块
│   │   ├── __init__.py
│   │   ├── downloader.py      # 多线程下载器
│   │   ├── pdf_utils.py       # PDF工具函数
│   │   ├── pdf_manager.py     # PDF文件管理
│   │   ├── batch_processor.py # 批处理器
│   │   └── cross_validator.py # 交叉验证器
│   │
│   ├── extractor/             # 提取模块 (策略模式架构)
│   │   ├── __init__.py
│   │   ├── base_extractor.py  # 基类(通用工具函数)
│   │   ├── financial_models.py# 数据模型(FinancialData)
│   │   ├── smart_extractor.py # 🆕 策略调度器(主提取器)
│   │   └── strategies/        # 🆕 提取策略目录
│   │       ├── base_strategy.py   # 策略接口
│   │       ├── regex_strategy.py  # 正则提取策略
│   │       ├── llm_strategy.py    # LLM策略(DeepSeek)
│   │       ├── ocr_strategy.py    # OCR策略(扫描版)
│   │       └── table_strategy.py  # 表格提取策略
│   │
│   ├── analysis/              # 分析模块
│   │   ├── __init__.py
│   │   └── analyzer.py        # 统计分析器
│   │
│   └── visualization/         # 可视化模块
│       ├── __init__.py
│       └── visualizer.py      # 图表生成器
│
├── config/                    # 配置文件
│   ├── __init__.py
│   ├── config.yaml            # 主配置文件
│   └── settings.py            # 设置管理
│
├── data/                      # 数据目录
│   ├── raw_reports/           # PDF/HTML财报 (15GB+)
│   │   ├── *.pdf              # 1,200+ PDF文件
│   │   └── corrupted_backup/  # 损坏文件备份
│   └── Company_Financial_report.csv  # 公司财报数据库
│
└── output/                    # 输出结果
    ├── results/               # 最终提取结果
    │   ├── final_extraction_results.xlsx  # Excel格式结果
    │   └── final_extraction_results.csv   # CSV格式结果
    ├── archive/               # 历史批次结果归档
    ├── extraction_master.json # 主控跟踪文件
    ├── extraction_quality_report.json # 质量分析报告
    └── llm_cache/             # LLM缓存(降低API成本)
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
# 快速提取（正则模式，60-70文件/秒）
python main.py extract --method regex_only --batch-size 500

# 标准提取（Smart模式，平衡速度与准确性）
python main.py extract --method smart --batch-size 200

# 激进提取（处理失败文件，~80%恢复率）
python main.py extract --method aggressive --failed-only

# LLM增强提取（最高准确率，需要API密钥）
export DEEPSEEK_API_KEY="your-api-key"
python main.py extract --use-llm --limit 50
```

### 3. 数据分析

```bash
# 分析公司数据
python main.py analyze --type companies

# 分析提取结果
python main.py analyze --type extraction
```

### 4. 监控与报告

```bash
# 实时监控提取进度
python main.py monitor

# 合并所有提取结果
python main.py merge

# 查看提取状态
python main.py status

# 生成综合报告
python main.py report

# 重试失败文件
python main.py retry --failed
```

### 5. 工具功能

```bash
# 检查并清理损坏的PDF
python main.py utils --clean-pdfs

# 生成项目摘要
python main.py utils --summary
```

## 🔧 高级功能 Advanced Features

### 多策略提取

系统采用策略模式架构，支持多种提取模式：

1. **regex_only**: 仅使用正则表达式（最快，60-70文件/秒）
2. **smart**: 综合多种策略（平衡模式，10-20文件/秒）
3. **aggressive**: 激进恢复模式（针对失败文件，~80%恢复率）
4. **llm_only**: 仅使用LLM（需要DeepSeek API）
5. **adaptive**: 自适应选择最佳策略组合

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

### 基础指标
- **资产负债表**: 总资产、总负债、股东权益、现金及现金等价物
- **损益表**: 营业收入、净利润/亏损、营业费用、税前利润
- **现金流量表**: 经营现金流、投资现金流、融资现金流

### 银行特有指标
- **利息收入**: 利息收入、净利息收入、手续费收入
- **资产质量**: 贷款及垫款、客户存款
- **关键比率**: ROA、ROE、资产负债率、净息差

## 🛠️ 配置说明

### 环境变量

```bash
# 设置DeepSeek API密钥（使用LLM时必须）
# 项目已包含.env文件，可直接在其中配置
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

## 🌟 最新更新 Latest Updates

### v3.3.0 (2025-08-12)
- 🚀 **性能优化**: 正则模式速度提升至60-70文件/秒
- 🎯 **激进提取**: 新增aggressive模式，失败文件恢复率达80%
- 📊 **最新成果**: 成功提取511条记录，覆盖56家公司
- 🗂️ **输出整理**: 规范化output目录结构，支持结果归档
- 📈 **并行处理**: 支持15个并发线程，大幅提升处理速度

### v3.2.0 (2025-08-11)
- 🆕 采用策略模式(Strategy Pattern)重构整个extractor模块
- ✨ 整合冗余代码：extraction_utils→regex_strategy
- 📦 新的目录结构：strategies/子目录包含所有提取策略
- 🔧 SmartExtractor作为策略调度器，支持多种提取模式
- 🆕 每个策略独立文件，更易维护和扩展

---

**最后更新 Last Updated**: 2025-08-12
**作者 Author**: Lin Cifeng