# 交叉验证提取报告
生成时间: 2025-08-06 14:11:22

## 总体统计
- 处理文件数: 10
- 成功率: 90.0%
- 一致性结果: 2 (20.0%)
- 存在差异: 7 (70.0%)
- 两种方法都失败: 1

## 差异分析
以下文件在正则和LLM提取之间存在显著差异：

### Airstarbank_2020_Annual.pdf
- **total_assets**:
  - 正则: 2880469.0
  - LLM: None
  - 最终: 2880469.0
  - 选择理由: Regex only
- **total_liabilities**:
  - 正则: 1677433.0
  - LLM: None
  - 最终: 1677433.0
  - 选择理由: Regex only
- **revenue**:
  - 正则: 5.0
  - LLM: 15572000
  - 最终: 5.0
  - 选择理由: Regex selected (simple field)
- **net_profit**:
  - 正则: None
  - LLM: -232088000
  - 最终: -232088000
  - 选择理由: LLM only

### Airstarbank_2020_Q1_Q2.pdf
- **revenue**:
  - 正则: 2.0
  - LLM: 10617573
  - 最终: 2.0
  - 选择理由: Regex selected (simple field)

### Airstarbank_2020_Q1、Q2.pdf
- **revenue**:
  - 正则: 2.0
  - LLM: 10617573
  - 最终: 2.0
  - 选择理由: Regex selected (simple field)

### Airstarbank_2021_Q1_Q2.pdf
- **total_assets**:
  - 正则: 3464490.0
  - LLM: 3464490000
  - 最终: 3464490.0
  - 选择理由: Regex selected (simple field)
- **total_liabilities**:
  - 正则: 2390450.0
  - LLM: 2390450000
  - 最终: 2390450000
  - 选择理由: LLM selected (complex field)
- **revenue**:
  - 正则: 2.0
  - LLM: 13715000
  - 最终: 2.0
  - 选择理由: Regex selected (simple field)
- **net_profit**:
  - 正则: -123375.0
  - LLM: -123375000
  - 最终: -123375000
  - 选择理由: LLM selected (complex field)

### Airstarbank_2021_Q1、Q2.pdf
- **total_assets**:
  - 正则: 3464490.0
  - LLM: 3464490000
  - 最终: 3464490.0
  - 选择理由: Regex selected (simple field)
- **total_liabilities**:
  - 正则: 2390450.0
  - LLM: 2390450000
  - 最终: 2390450000
  - 选择理由: LLM selected (complex field)
- **revenue**:
  - 正则: 2.0
  - LLM: 13715000
  - 最终: 2.0
  - 选择理由: Regex selected (simple field)
- **net_profit**:
  - 正则: -123375.0
  - LLM: -123375000
  - 最终: -123375000
  - 选择理由: LLM selected (complex field)

### Airstarbank_2022_Q1_Q2.pdf
- **total_assets**:
  - 正则: 2857826.0
  - LLM: 2857826000
  - 最终: 2857826.0
  - 选择理由: Regex selected (simple field)
- **total_liabilities**:
  - 正则: 1996911.0
  - LLM: 1996911000
  - 最终: 1996911000
  - 选择理由: LLM selected (complex field)
- **revenue**:
  - 正则: 2.0
  - LLM: 33134000
  - 最终: 2.0
  - 选择理由: Regex selected (simple field)
- **net_profit**:
  - 正则: -97755.0
  - LLM: -97755000
  - 最终: -97755000
  - 选择理由: LLM selected (complex field)

### Airstarbank_2022_Q1、Q2.pdf
- **total_assets**:
  - 正则: 2857826.0
  - LLM: 2857826000
  - 最终: 2857826.0
  - 选择理由: Regex selected (simple field)
- **total_liabilities**:
  - 正则: 1996911.0
  - LLM: 1996911000
  - 最终: 1996911000
  - 选择理由: LLM selected (complex field)
- **revenue**:
  - 正则: 2.0
  - LLM: 33134000
  - 最终: 2.0
  - 选择理由: Regex selected (simple field)
- **net_profit**:
  - 正则: -97755.0
  - LLM: -97755000
  - 最终: -97755000
  - 选择理由: LLM selected (complex field)

## 成功提取示例
- **Airstarbank** (2019): 4/4 字段成功提取
- **Airstarbank** (2021): 4/4 字段成功提取
