# 财务分析系统 v3.0
Financial Analysis System v3.0

**作者 Author**: Lin Cifeng

## 项目简介 Project Overview

本项目是一个自动化的财务数据提取和分析系统，专门用于从PDF格式的财务报表中提取关键财务指标。主要针对香港虚拟银行等金融科技公司的财务报告进行优化。

This is an automated financial data extraction and analysis system designed to extract key financial metrics from PDF financial reports, with a focus on Hong Kong virtual banks and fintech companies.

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
│   └── models.py             # 数据模型
├── data/                     # 数据目录
│   ├── raw_reports/          # PDF/HTML财报
│   └── Company_Financial_report.csv
├── output/                   # 输出结果
├── docs/                     # 文档
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
- **批量处理**: 可处理大量PDF文件
- **数据分析**: 自动生成统计报告
- **错误处理**: 自动识别和隔离损坏文件

## 📈 提取指标 Extracted Metrics

- 总资产 (Total Assets)
- 总负债 (Total Liabilities)
- 营业收入 (Revenue)
- 净利润 (Net Profit/Loss)

## 🛠️ 技术栈 Tech Stack

- Python 3.6+
- pdfplumber - PDF文本提取
- requests - 网络请求
- concurrent.futures - 并发处理

## 📝 注意事项 Notes

1. 确保有足够的磁盘空间存储财报文件（约15GB）
2. 部分PDF可能因加密或损坏无法提取
3. 网络下载可能因服务器限制而失败

## 🔄 更新日志 Changelog

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

---

如有问题或建议，欢迎提交Issue！