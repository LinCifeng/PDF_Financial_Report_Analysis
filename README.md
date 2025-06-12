# 金融分析系统

> FinTech 公司财务报告分析系统

专为分析 FinTech 公司财务报告而设计的综合工具，支持财报收集状况统计分析、多年趋势分析和专业图表生成。

## 🚀 核心功能

### 📊 财报收集状况分析

- **收集率统计** - 分析 FinTech 公司财务报告收集情况
- **年份覆盖分析** - 统计报告年份分布和覆盖范围
- **公司分类统计** - 按收集状态分类统计公司数量
- **Markdown 报告生成** - 生成专业格式的分析报告

### 📈 多年趋势分析

- **资产趋势图表** - 生成多年资产变化趋势图
- **资产结构演变** - 分析资产结构变化情况
- **财务指标对比** - 核心财务指标年度对比
- **数据整合输出** - 生成统一的 JSON 数据文件

### 🎨 专业可视化

- **英文图表** - 专业的英文财务图表
- **多维度分析** - 总资产、负债、权益等多角度分析
- **增长率计算** - 自动计算各项指标增长率
- **现代化设计** - 基于 matplotlib 的现代化图表设计

## 🏗️ 项目结构

```
FinancialAnalysis/
├── financial_analyzer/           # 核心分析模块
│   ├── data_extraction/         # 数据提取模块
│   │   └── pdf_extractor.py     # PDF数据提取工具
│   ├── analysis/                # 分析模块
│   │   ├── financial_analyzer.py # 财务分析器
│   │   └── report_generator.py   # 报告生成器
│   ├── visualization/           # 可视化模块
│   │   └── chart_generator.py   # 图表生成器（含多年趋势分析）
│   ├── output/                  # 输出示例
│   └── main.py                  # 主模块
├── data/                        # 数据目录
│   ├── Company_Financial_report.csv # 财报收集记录
│   ├── collection_status_analysis.py # 收集状况分析脚本
│   ├── ZABank2020.pdf          # ZA Bank 2020年报
│   ├── ZABank2021.pdf          # ZA Bank 2021年报
│   ├── ZABank2022.pdf          # ZA Bank 2022年报
│   ├── ZABank2023.pdf          # ZA Bank 2023年报
│   └── ZABank2024.pdf          # ZA Bank 2024年报
├── generate_za_bank_trends.py  # ZA Bank趋势分析启动脚本
└── requirements.txt            # 项目依赖
```

## 📦 安装配置

```bash
# 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

## 🚀 使用方法

### 1. 财报收集状况分析

```bash
# 运行收集状况分析
cd data
python3 collection_status_analysis.py
```

**生成报告包含：**

- 总体数据统计（575 家公司，127 家有报告）
- 收集率分析（22.1%整体收集率）
- 年份覆盖范围（主要覆盖 2018-2024 年）
- 每家公司平均报告数量（11.7 份）
- Markdown 格式专业报告

### 2. ZA Bank 多年趋势分析

```bash
# 运行ZA Bank趋势分析
python3 generate_za_bank_trends.py
```

**生成内容包含：**

- **4 张专业英文图表：**
  - `ZA_Bank_Total_Assets_Trend.png` - 总资产趋势图
  - `ZA_Bank_Asset_Structure_Evolution.png` - 资产结构演变图
  - `ZA_Bank_Balance_Comparison.png` - 资产负债对比图
  - `ZA_Bank_Core_Metrics.png` - 核心指标图
- **统一 JSON 数据文件：** `ZA_Bank_Multi_Year_Analysis_*.json`
- **增长率统计：** 总资产增长 379.41%（41.6 亿 →199.5 亿港币）

## 📊 输出文件说明

### 财报收集状况分析输出

| 文件名                                                      | 描述             | 格式     |
| ----------------------------------------------------------- | ---------------- | -------- |
| `collection_status_of_financial_reports_YYYYMMDD_HHMMSS.md` | 收集状况分析报告 | Markdown |

### ZA Bank 趋势分析输出

| 文件名                                  | 描述           | 格式 |
| --------------------------------------- | -------------- | ---- |
| `ZA_Bank_Total_Assets_Trend.png`        | 总资产趋势图   | PNG  |
| `ZA_Bank_Asset_Structure_Evolution.png` | 资产结构演变图 | PNG  |
| `ZA_Bank_Balance_Comparison.png`        | 资产负债对比图 | PNG  |
| `ZA_Bank_Core_Metrics.png`              | 核心财务指标图 | PNG  |
| `ZA_Bank_Multi_Year_Analysis_*.json`    | 整合数据文件   | JSON |

## 📈 数据覆盖范围

### 财报收集数据集

- **575 家** FinTech 公司
- **127 家** 有财报数据的公司
- **平均 11.7 份** 报告每家公司
- **2018-2024 年** 主要覆盖期间
- **22.1%** 整体收集率

### ZA Bank 分析数据

- **2020-2024 年** 连续 5 年数据
- **总资产增长** 379.41%（41.6 亿 →199.5 亿港币）
- **总负债增长** 506.05%
- **股东权益增长** 61.25%
- **资产负债率** 从 71.53%上升至 90.42%

## 🛠️ 核心技术依赖

- **数据处理**: pandas, numpy
- **PDF 处理**: pdfplumber, PyPDF2
- **可视化**: matplotlib, seaborn
- **网页抓取**: selenium, beautifulsoup4
- **机器学习**: scikit-learn

## 🎯 支持的报告类型

当前系统优化支持：

- **香港虚拟银行** (ZA Bank, WeLab Bank, Airstar Bank 等)
- **国际数字银行** (Revolut, Klarna, Wise 等)
- **FinTech 公司** (Square, Affirm, Upstart 等)

## 🔄 版本更新历史

- **v2.0** - 新增 ZA Bank 多年趋势分析功能，整合 JSON 输出
- **v1.2** - 添加 Markdown 格式报告输出
- **v1.1** - 添加财报收集状况分析功能
- **v1.0** - 基础 PDF 分析和可视化功能

## 📧 联系方式

如有问题或建议，请联系数据团队。

---

_由金融分析系统生成 | 香港大学毕业设计项目_
