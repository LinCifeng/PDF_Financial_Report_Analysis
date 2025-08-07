# 财务数据提取优化方案 - 最终报告

生成时间: 2025-08-06

## 一、当前状况分析

### 1.1 提取率现状

基于50个样本文件的分析：

| 指标 | 正则提取率 | LLM提取率 | 综合提取率 | 目标 |
|------|-----------|-----------|------------|------|
| **总资产** | 20% | 48% | 68% | 95% |
| **总负债** | 20% | 46% | 66% | 95% |
| **营业收入** | 2% | 24% | 26% | 75% |
| **净利润** | 0% | 48% | 48% | 85% |

### 1.2 主要问题

1. **扫描版PDF（24%）**
   - 12个文件无法提取文本
   - 主要影响Livi银行的早期报告

2. **收入提取率低（74%失败）**
   - 正则模式覆盖不足
   - 银行收入项目名称多样化
   - 未识别利息收入、手续费收入等

3. **公司特定问题**
   - Livi银行：63.2%平均失败率
   - Fusion银行：特殊格式需要专门处理

4. **净利润识别（52%失败）**
   - 负数/亏损识别不足
   - 括号表示法处理不当

## 二、优化方案

### 2.1 立即可实施的改进

#### A. 增强正则表达式库

```python
# 收入识别模式扩展
revenue_patterns = [
    # 通用收入
    r'(?:营业|營業|经营|經營)?(?:总|總)?收入',
    r'(?:Total\s+)?(?:Operating\s+)?(?:Revenue|Income)s?',
    
    # 银行特有
    r'利息收入|Interest\s+Income',
    r'净利息收入|Net\s+Interest\s+Income',
    r'手续费及佣金收入|Fee\s+and\s+Commission\s+Income',
    r'非利息收入|Non-interest\s+Income',
    
    # 其他行业
    r'销售收入|Sales\s+Revenue',
    r'服务收入|Service\s+Income',
    r'营业额|Turnover',
]

# 净利润识别模式扩展
net_profit_patterns = [
    # 利润
    r'净利润|淨利潤|Net\s+Profit',
    r'本期利润|Profit\s+for\s+the\s+Period',
    r'年度利润|Annual\s+Profit',
    r'综合收益总额|Total\s+Comprehensive\s+Income',
    
    # 亏损（带负号处理）
    r'净亏损|淨虧損|Net\s+Loss',
    r'本期亏损|Loss\s+for\s+the\s+Period',
    r'\(([0-9,]+)\)',  # 括号表示负数
]
```

#### B. 智能单位检测

```python
def smart_unit_detection(text, numbers):
    """智能单位检测 - 通过上下文和数字大小推断"""
    # 1. 显式单位标记
    if '千元' in text or "in thousands" in text:
        return 1000
    
    # 2. 通过数字规模推断
    avg_size = calculate_average_number_size(numbers)
    if avg_size < 10000:
        return 1000  # 可能是千元
    
    # 3. 通过行业特征推断
    if is_bank_report(text) and avg_size < 1000000:
        return 1000  # 银行通常用千元
    
    return 1
```

#### C. 多策略融合提取

```python
def multi_strategy_extraction(pdf):
    """多策略融合提取"""
    results = {}
    
    # 策略1: 快速正则扫描
    regex_results = enhanced_regex_extraction(pdf)
    
    # 策略2: 智能表格提取
    table_results = smart_table_extraction(pdf)
    
    # 策略3: 上下文感知提取
    context_results = context_aware_extraction(pdf)
    
    # 策略4: 模糊匹配
    if len(results) < 4:
        fuzzy_results = fuzzy_matching_extraction(pdf)
    
    # 智能融合结果
    return intelligent_merge(results)
```

### 2.2 中期改进措施

#### A. OCR集成（处理扫描版PDF）

```python
# 集成 PaddleOCR 或 Tesseract
def ocr_extraction(pdf_path):
    """OCR提取扫描版PDF"""
    # 1. 检测是否为扫描版
    if is_scanned_pdf(pdf_path):
        # 2. 转换为图片
        images = pdf_to_images(pdf_path)
        
        # 3. OCR识别
        text = ocr_recognize(images)
        
        # 4. 应用常规提取
        return extract_from_text(text)
```

#### B. 公司专属模板系统

```python
# 为高失败率公司建立模板
company_templates = {
    'Livi': {
        'balance_sheet_page': [15, 20],  # 资产负债表通常在15-20页
        'income_statement_keywords': ['综合收益表', 'Statement of Comprehensive Income'],
        'special_patterns': {
            'revenue': r'营业收入.*?(\d+)',
            'net_profit': r'本期亏损.*?\((\d+)\)'  # Livi经常亏损
        }
    },
    'Fusion': {
        'table_first': True,  # 优先使用表格提取
        'unit': 1000,  # 固定使用千元
    }
}
```

#### C. LLM优化提示词

```python
enhanced_llm_prompt = """
你是一个专业的财务数据提取助手。请从以下财务报告中提取数据。

特别注意：
1. 对于银行类公司：
   - 收入 = 利息收入 + 非利息收入（手续费、佣金等）
   - 如果没有"营业收入"，请计算"净利息收入 + 手续费收入"

2. 识别负数的方式：
   - 括号：(123,456) = -123456
   - 负号：-123,456
   - 文字：亏损、Loss = 负数

3. 单位识别：
   - "千元"、"in thousands" = 数字×1000
   - 没有明确单位时，通过数字大小判断

4. 优先级：
   - 优先提取最近年份的数据
   - 优先提取合并报表而非母公司报表

请返回JSON格式，包含提取的数据和置信度。
"""
```

### 2.3 长期优化方向

1. **机器学习模型**
   - 训练专门的财务报表识别模型
   - 使用标注数据提升准确率

2. **知识图谱**
   - 构建财务术语知识图谱
   - 支持同义词识别和推理

3. **自动化反馈**
   - 建立人工审核机制
   - 持续优化提取规则

## 三、预期效果

### 3.1 短期改进（1周内）

通过实施增强的正则表达式和智能融合策略：

| 指标 | 当前 | 预期 | 提升 |
|------|------|------|------|
| **营业收入** | 26% | 55% | +29% |
| **净利润** | 48% | 70% | +22% |
| **整体完整率** | 22% | 40% | +18% |

### 3.2 中期改进（1个月）

加入OCR和公司模板后：

| 指标 | 短期 | 中期 | 提升 |
|------|------|------|------|
| **总资产** | 68% | 85% | +17% |
| **营业收入** | 55% | 75% | +20% |
| **净利润** | 70% | 85% | +15% |
| **整体完整率** | 40% | 65% | +25% |

## 四、实施计划

### 第一阶段：立即执行
1. 更新 `master_extractor.py` 添加增强模式
2. 实现智能单位检测
3. 优化收入和净利润的识别规则

### 第二阶段：本周完成
1. 集成OCR功能处理扫描版PDF
2. 为Livi和Fusion创建专属模板
3. 优化LLM提示词

### 第三阶段：持续改进
1. 收集更多失败案例
2. 不断优化提取规则
3. 建立自动化测试体系

## 五、关键成功因素

1. **数据质量**
   - 修复空PDF文件
   - 获取更多电子版报告

2. **技术实施**
   - 正确处理单位转换
   - 准确识别负数/亏损

3. **持续优化**
   - 建立反馈机制
   - 定期更新规则库

通过这些优化措施，预计可将整体数据完整提取率从22%提升到65%以上，为香港虚拟银行财务分析提供更全面的数据支持。

---

*本方案基于实际失败案例分析和技术可行性评估制定*