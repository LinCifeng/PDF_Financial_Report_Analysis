# 项目结构说明 Project Structure

## 目录结构 Directory Structure

```
FinancialAnalysis/
├── main.py                 # 项目主入口
├── requirements.txt        # Python依赖
├── README.md              # 项目说明
├── PROJECT_STRUCTURE.md   # 本文档
│
├── config/                # 配置文件
│   └── settings.yaml     # 项目配置
│
├── data/                  # 数据目录
│   ├── raw_reports/      # 原始PDF财报
│   └── processed/        # 处理后的数据
│
├── output/               # 输出目录
│   ├── all_financial_data.csv     # 提取的财务数据
│   ├── simple_extraction_results.csv # 简化提取结果
│   └── extraction_summary.txt     # 提取总结
│
├── logs/                 # 日志文件
│
└── src/                  # 源代码
    ├── core/            # 核心模块
    │   ├── config.py    # 配置管理
    │   └── models.py    # 数据模型
    │
    ├── extractors/      # 数据提取器
    │   ├── base_extractor.py     # 基础提取器
    │   ├── pdf_extractor.py      # PDF提取器
    │   ├── table_extractor.py    # 表格提取器
    │   ├── ocr_extractor.py      # OCR提取器
    │   ├── llm_extractor.py      # LLM提取器
    │   └── improved_llm_extractor.py # 改进的LLM提取器
    │
    ├── processors/      # 批处理器
    │   └── batch_processor.py    # 批量处理
    │
    ├── scripts/         # 可执行脚本
    │   ├── simple_extract.py     # 简单提取脚本
    │   ├── extract_all_data.py  # 完整提取脚本(带LLM)
    │   └── analyze_companies.py  # 数据分析脚本
    │
    └── utils/          # 工具函数
```

## 使用方法 Usage

### 1. 简单数据提取（不使用LLM）
```bash
python main.py extract
```
- 使用正则表达式从PDF中提取财务数据
- 速度快，但提取率较低
- 结果保存到 `output/simple_extraction_results.csv`

### 2. 完整数据提取（使用LLM增强）
```bash
python main.py extract-llm
```
- 先用正则提取，然后用LLM补充缺失数据
- 需要配置DeepSeek API密钥
- 提取率更高，但速度较慢
- 结果保存到 `output/all_financial_data.csv`

### 3. 数据分析
```bash
python main.py analyze
```
- 分析已提取的财务数据
- 生成统计报告和可视化

## 主要功能模块 Main Modules

### Extractors 提取器
- **PDFExtractor**: 使用pdfplumber提取PDF文本和基本财务数据
- **TableExtractor**: 专门提取PDF中的表格数据
- **OCRExtractor**: 处理扫描版PDF（需要安装OCR依赖）
- **LLMExtractor**: 使用大语言模型提取复杂财务数据

### Scripts 脚本
- **simple_extract.py**: 快速提取，适合大批量处理
- **extract_all_data.py**: 完整提取，适合需要高质量数据的场景
- **analyze_companies.py**: 数据分析和报告生成

## 数据流程 Data Flow

1. **输入**: `data/raw_reports/` 中的PDF财报
2. **处理**: 使用不同提取器提取财务数据
3. **输出**: CSV文件保存到 `output/` 目录
4. **分析**: 生成统计报告和可视化图表

## 配置说明 Configuration

在 `config/settings.yaml` 中配置：
- API密钥（DeepSeek等）
- 提取参数
- 输出格式设置