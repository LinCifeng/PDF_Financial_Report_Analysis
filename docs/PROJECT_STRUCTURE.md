# 项目结构说明 Project Structure Guide

## 目录结构 Directory Structure

```
FinancialAnalysis/
├── main.py              # 项目主入口（根目录）
├── requirements.txt     # Python依赖列表
├── README.md           # 项目说明文档
├── .gitignore          # Git忽略文件配置
│
├── scripts/            # 可执行脚本目录
│   ├── main.py        # 命令行主程序
│   ├── simple_extract.py          # 基础PDF数据提取
│   ├── extract_data_optimized.py  # 优化版数据提取
│   ├── extract_all_data.py        # 批量数据提取
│   └── analysis/                  # 分析相关脚本
│       ├── analyze_companies.py   # 公司财报分析
│       └── analyze_download_coverage.py # 下载覆盖率分析
│
├── src/                # 源代码库
│   ├── __init__.py
│   ├── core/          # 核心功能模块
│   ├── extractors/    # 数据提取器
│   │   ├── base.py   # 基础提取器
│   │   ├── pdf/      # PDF相关提取器
│   │   └── llm/      # LLM增强提取器
│   ├── processors/    # 数据处理器
│   └── data/         # 数据管理模块
│
├── data/              # 数据目录
│   ├── raw_reports/   # PDF财报文件（108个文件）
│   └── Company_Financial_report.csv # 财报链接数据（1478条记录）
│
├── output/            # 输出结果目录
│   ├── simple_extraction_results.csv
│   ├── optimized_extraction_results.csv
│   ├── all_financial_data.csv
│   └── download_coverage_report.md
│
├── logs/              # 日志文件目录
│   └── extraction.log
│
└── config/            # 配置文件目录
    └── config.yaml    # 项目配置文件
```

## 文件命名规范 File Naming Convention

1. **Python文件**: 使用小写字母和下划线 (snake_case)
2. **类名**: 使用驼峰命名法 (PascalCase)
3. **函数名**: 使用小写字母和下划线 (snake_case)
4. **常量**: 使用大写字母和下划线 (UPPER_SNAKE_CASE)

## 使用说明 Usage Guide

### 运行数据提取
```bash
# 基础提取
python scripts/simple_extract.py

# 优化提取（推荐）
python scripts/extract_data_optimized.py

# LLM增强提取
python scripts/extract_all_data.py
```

### 运行分析脚本
```bash
# 分析公司财报情况
python scripts/analysis/analyze_companies.py

# 分析下载覆盖率
python scripts/analysis/analyze_download_coverage.py
```

## 数据流程 Data Flow

1. **输入**: PDF财报文件 (data/raw_reports/)
2. **处理**: 提取器提取关键财务指标
3. **输出**: CSV格式的结构化数据 (output/)

## 关键指标 Key Metrics

- 总资产 (Total Assets)
- 总负债 (Total Liabilities)  
- 营业收入 (Revenue)
- 净利润 (Net Profit/Loss)