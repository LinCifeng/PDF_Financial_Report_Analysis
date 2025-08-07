# Output 目录说明

## 目录结构

```
output/
├── archive/               # 历史结果存档
│   └── 2025-08-06/       # 按日期组织
│       ├── regex_results/ # 正则表达式提取结果
│       ├── llm_results/   # LLM提取结果
│       ├── hybrid_results/# 混合提取结果
│       ├── batch_results/ # 批次处理结果
│       └── reports/       # 分析报告
├── llm_cache/            # LLM缓存（避免重复调用）
├── old_extractions/      # 旧版本提取结果
├── summaries/            # 下载统计摘要
└── extractions/          # 其他提取结果
```

## 最新结果文件命名规则

- `crosscheck_extraction_[timestamp].csv` - 交叉验证提取结果
- `crosscheck_report_[timestamp].md` - 交叉验证分析报告
- `discrepancy_analysis_[timestamp].csv` - 差异分析报告

## 字段说明

### 交叉验证结果字段
- `company` - 公司名称
- `year` - 财报年份
- `file_name` - PDF文件名
- `regex_assets` - 正则提取的总资产
- `llm_assets` - LLM提取的总资产
- `final_assets` - 交叉验证后的最终值
- `assets_confidence` - 置信度（high/medium/low）
- （其他财务指标类似）
- `validation_status` - 验证状态（Consistent/Discrepancy/Partial）
- `notes` - 备注说明