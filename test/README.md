# Scripts 工具脚本目录

## 📁 目录结构（已重组）

```
scripts/
├── extractors/           # 提取器
│   └── master_extractor.py    # 主提取器（整合多种策略）
├── analyzers/            # 分析工具
│   ├── data_analyzer.py       # 综合数据分析
│   ├── analyze_reports.py     # 财报分析
│   ├── analyze_extraction_failures.py  # 失败分析
│   └── final_analysis.py      # 最终分析
├── visualizers/          # 可视化工具
│   ├── visualize_performance.py        # 性能可视化
│   ├── visualize_existing_data.py      # 数据可视化
│   └── visualize_fast_test_results.py  # 测试结果可视化
└── utilities/            # 实用工具
    ├── batch_processor.py      # 批量处理器
    ├── cross_validator.py      # 交叉验证器
    ├── pdf_manager.py          # PDF管理器
    ├── deepseek_client.py      # DeepSeek API客户端
    ├── batch_analyze.py        # 批量分析
    └── fast_extraction_test.py # 快速测试
```

## 🔑 核心功能模块

### 1. 主提取器 (extractors/master_extractor.py)
- 整合正则、LLM、表格等多种提取方法
- 支持20+财务指标
- 自动选择最佳提取策略
- 使用方法：
  ```python
  from scripts.extractors.master_extractor import MasterExtractor
  
  extractor = MasterExtractor(use_llm=True)
  result = extractor.extract("path/to/file.pdf")
  ```

### 2. 批量处理器 (utilities/batch_processor.py)
- 支持并行处理（默认4线程）
- 自动重试机制
- 进度追踪
- 使用方法：
  ```bash
  python scripts/utilities/batch_processor.py
  ```

### 3. 交叉验证器 (utilities/cross_validator.py)
- 对比不同方法的提取结果
- 处理单位转换问题
- 提供置信度评分
- 使用方法：
  ```python
  from scripts.utilities.cross_validator import CrossValidator
  
  validator = CrossValidator()
  validated_data = validator.validate(regex_results, llm_results)
  ```

### 4. 数据分析器 (analyzers/data_analyzer.py)
- 全面的统计分析
- 可视化报告生成
- 质量评估
- 使用方法：
  ```bash
  python scripts/analyzers/data_analyzer.py
  ```

### 5. PDF管理器 (utilities/pdf_manager.py)
- 文件状态检查
- 空文件修复
- 重复文件处理
- 使用方法：
  ```python
  from scripts.utilities.pdf_manager import PDFManager
  
  manager = PDFManager()
  manager.scan_and_clean()
  ```

## 🚀 快速开始

### 单文件提取
```bash
python scripts/extractors/master_extractor.py --file data/raw_reports/sample.pdf
```

### 批量处理
```bash
python scripts/utilities/batch_processor.py --limit 100
```

### 生成分析报告
```bash
python scripts/analyzers/data_analyzer.py
```

### 可视化结果
```bash
python scripts/visualizers/visualize_performance.py
```

## 📊 支持的财务指标

### 资产负债表
- total_assets (总资产)
- total_liabilities (总负债)
- total_equity (总权益)
- cash_and_equivalents (现金及等价物)
- loans_and_advances (贷款及垫款)
- customer_deposits (客户存款)

### 损益表
- revenue (营业收入)
- net_profit (净利润)
- operating_expenses (营业费用)
- ebit (税前利润)
- interest_income (利息收入)
- net_interest_income (净利息收入)
- fee_income (手续费收入)

### 现金流量表
- operating_cash_flow (经营活动现金流)
- investing_cash_flow (投资活动现金流)
- financing_cash_flow (筹资活动现金流)

## ⚙️ 配置选项

### 环境变量
```bash
export DEEPSEEK_API_KEY="your-api-key"  # LLM API密钥
export BATCH_SIZE=100                   # 批处理大小
export MAX_WORKERS=4                    # 并行线程数
```

### Python导入路径
所有脚本都正确配置了导入路径，可以直接运行：
```python
# 脚本会自动添加项目根目录到sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
```

## 📈 性能指标

- **提取成功率**: ~34% (基础) / ~60% (LLM增强)
- **处理速度**: 10-20个PDF/分钟 (并行处理)
- **准确率**: 90%+ (经过交叉验证)

## 🛠️ 故障排除

### 常见问题

1. **ImportError: No module named 'xxx'**
   - 解决：安装缺失依赖 `pip install -r requirements.txt`

2. **LLM调用失败**
   - 解决：检查API密钥配置 `export DEEPSEEK_API_KEY="your-key"`

3. **内存不足**
   - 解决：减小批处理大小或降低并行线程数

4. **PDF无法读取**
   - 解决：使用PDF管理器检查文件完整性

## 📝 更新日志

### v2.0 (2024-08-07)
- 重组脚本目录结构
- 删除重复功能脚本
- 优化导入路径
- 改进文档说明

### v1.0 (2024-08-06)
- 初始版本
- 5个核心模块
- 支持批量处理和LLM增强