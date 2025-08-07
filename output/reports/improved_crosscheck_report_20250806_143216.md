# 改进的交叉验证提取报告
生成时间: 2025-08-06 14:32:16

## 总体统计
- 处理文件数: 5
- 成功率: 100.0%
- 一致性结果: 3 (60.0%)
- 存在差异: 2 (40.0%)
- 单位转换案例: 4 (20.0%)
- 两种方法都失败: 0

## 单位转换案例
以下字段检测到单位转换（正则vs LLM）：

### Airstarbank_2020_Annual.pdf
- 正则检测单位: yuan (×1)
- **total_assets**:
  - 正则: 2,880,469
  - LLM: 2,880,469,000
  - 选择: LLM selected (unit conversion detected, ratio≈0)
- **total_liabilities**:
  - 正则: 1,677,433
  - LLM: 1,677,433,000
  - 选择: LLM selected (unit conversion detected, ratio≈0)

### Airstarbank_2021_Annual.pdf
- 正则检测单位: yuan (×1)
- **total_assets**:
  - 正则: 3,227,586
  - LLM: 3,227,586,000
  - 选择: LLM selected (unit conversion detected, ratio≈0)
- **total_liabilities**:
  - 正则: 2,266,139
  - LLM: 2,266,139,000
  - 选择: LLM selected (unit conversion detected, ratio≈0)

## 高一致性案例
- **Airstarbank** (2019): 0/4 字段高置信度
- **Airstarbank** (2020): 2/4 字段高置信度
- **Airstarbank** (2020): 2/4 字段高置信度
