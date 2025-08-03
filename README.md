# 财务报表数据提取与分析系统
Financial Report Data Extraction and Analysis System

**作者 Author**: Lin Cifeng

## 项目简介 Project Overview

本项目是一个自动化的财务数据提取和分析系统，专门用于从PDF格式的财务报表中提取关键财务指标。主要针对香港虚拟银行等金融科技公司的财务报告进行优化。

This is an automated financial data extraction and analysis system designed to extract key financial metrics from PDF financial reports, with a focus on Hong Kong virtual banks and fintech companies.

## 主要特性 Key Features

- 📄 **多层次PDF提取**: 支持正则表达式、表格提取、OCR等多种方式
- 🤖 **AI增强提取**: 使用LLM（DeepSeek）提升复杂数据的提取准确率
- 📊 **智能数据处理**: 自动识别负数（亏损）、处理多语言（中英文）
- 🔧 **模块化架构**: 清晰的代码结构，易于扩展和维护
- 📈 **批量处理**: 支持大规模PDF文件的并行处理

## 最新提取效果 Latest Extraction Performance

| 指标 | 提取率 | 说明 |
|------|--------|------|
| 总资产 | 30.6% | Total Assets |
| 总负债 | 47.2% | Total Liabilities |
| 营业收入 | 34.3% | Revenue |
| **净利润** | **41.7%** | Net Profit/Loss |
| 成功率 | 55.6% | Overall Success Rate |

## 项目结构 Project Structure

```
FinancialAnalysis/
├── scripts/              # 可执行脚本
│   ├── main.py          # 主程序入口
│   ├── simple_extract.py # 简单提取
│   └── extract_data_optimized.py # 优化版提取
├── src/                 # 核心代码库
│   ├── core/           # 核心模块
│   ├── extractors/     # 数据提取器
│   │   ├── pdf/       # PDF相关提取器
│   │   └── llm/       # LLM提取器
│   ├── processors/     # 数据处理器
│   └── data/          # 数据管理
├── data/               # 数据目录
│   └── raw_reports/   # PDF财报存放
├── output/            # 输出结果
└── logs/             # 日志文件
```

## 快速开始 Quick Start

### 1. 安装依赖 Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. 准备数据 Prepare Data

将PDF财报文件放入 `data/raw_reports/` 目录

### 3. 运行提取 Run Extraction

#### 简单提取（快速）
```bash
python main.py extract
```

#### 优化版提取（推荐）
```bash
python scripts/extract_data_optimized.py
```

#### LLM增强提取（需要API密钥）
```bash
export DEEPSEEK_API_KEY="your-api-key"
python main.py extract-llm
```

### 4. 查看结果 View Results

提取结果保存在 `output/` 目录：
- `simple_extraction_results.csv` - 简单提取结果
- `optimized_extraction_results.csv` - 优化提取结果
- `all_financial_data.csv` - LLM增强提取结果

## 技术架构 Technical Architecture

### 提取器层次 Extractor Hierarchy

1. **基础提取器** (`src/extractors/base.py`)
   - 所有提取器的基类
   - 提供通用功能：数据验证、格式化等

2. **PDF提取器** (`src/extractors/pdf/`)
   - `basic.py`: 正则表达式提取
   - `table.py`: 表格数据提取
   - `ocr.py`: OCR文字识别

3. **LLM提取器** (`src/extractors/llm/`)
   - `improved.py`: 使用DeepSeek API的智能提取

4. **智能提取器** (`src/extractors/smart.py`)
   - 整合所有提取方式
   - 自动选择最佳提取策略

## 配置说明 Configuration

在 `config/config.yaml` 中配置：
- API密钥设置
- 提取参数调整
- 输出格式配置

## 依赖项 Dependencies

主要依赖：
- `pdfplumber`: PDF文本提取
- `pandas`: 数据处理
- `requests`: API调用
- `tqdm`: 进度显示

可选依赖（用于增强功能）：
- `camelot-py`: 高级表格提取
- `paddleocr`: 中文OCR
- `pymupdf`: PDF渲染

## 常见问题 FAQ

**Q: 为什么有些PDF文件提取失败？**
A: 可能是PDF文件损坏或加密。项目中约有19个Ant Bank和ZA Bank的PDF文件无法打开。

**Q: 如何提高净利润的提取率？**
A: 使用优化版提取脚本 `extract_data_optimized.py`，它包含了更全面的正则表达式模式和负数处理逻辑。

**Q: LLM提取需要付费吗？**
A: 是的，需要DeepSeek API密钥。但基础提取和优化提取是免费的。

## 贡献指南 Contributing

欢迎提交Issue和Pull Request！

---

**最后更新 Last Updated**: 2025-08-04