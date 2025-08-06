# 项目结构说明 - Project Structure

## 整理后的清晰结构

```
FinancialAnalysis/
├── main.py                    # 主入口文件
├── financial_analysis/        # 核心功能包
│   ├── __init__.py           
│   ├── extract/              # 数据提取模块
│   │   ├── __init__.py
│   │   ├── simple.py         # 简单提取
│   │   └── optimized.py      # 优化提取
│   ├── download/             # 下载模块
│   │   ├── __init__.py
│   │   └── download_reports.py
│   ├── analyze/              # 分析模块
│   │   ├── __init__.py
│   │   ├── companies.py      # 公司分析
│   │   └── coverage.py       # 覆盖率分析
│   └── utils/                # 工具模块
│       ├── __init__.py
│       ├── clean_pdfs.py     # PDF清理
│       └── generate_summary.py # 生成摘要
├── data/                     # 数据目录
│   ├── raw_reports/          # 原始PDF/HTML文件
│   └── Company_Financial_report.csv  # 财报数据库
├── output/                   # 输出目录
│   ├── extractions/          # 提取结果
│   └── downloads/            # 下载统计
├── config/                   # 配置文件
└── logs/                     # 日志文件
```

## 使用方法

### 1. 数据提取
```bash
# 简单提取（快速）
python main.py extract

# 优化提取（更准确）
python main.py extract --optimized

# 限制处理数量
python main.py extract --limit 100
```

### 2. 下载财报
```bash
python main.py download
```

### 3. 数据分析
```bash
# 分析公司覆盖
python main.py analyze

# 分析下载覆盖率
python main.py analyze --coverage
```

## 主要改进

1. **单一入口**: 所有功能通过 `main.py` 访问
2. **模块化设计**: 功能按类型组织在 `financial_analysis` 包中
3. **清晰的命名**: 文件名直接反映功能
4. **易于扩展**: 新功能可以轻松添加到对应模块

## 数据流程

1. **下载**: `download/` 模块负责从CSV数据库下载财报
2. **提取**: `extract/` 模块从PDF/HTML中提取财务数据
3. **分析**: `analyze/` 模块生成各种统计报告
4. **输出**: 所有结果保存在 `output/` 目录

## 最新统计

- 已下载财报: 1,224份 (82.8%)
  - PDF: 1,059份
  - HTML: 165份
- 提取成功率: ~34% (基于初步测试)