#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用DeepSeek大语言模型分析ZA Bank财报表现
专为中文财务分析优化
"""

import json
import os
import sys
import time
from datetime import datetime
import requests
from typing import Dict, Any, Optional

class DeepSeekFinancialAnalyzer:
    """DeepSeek财务数据分析器"""
    
    def __init__(self):
        """初始化分析器"""
        self.api_url = "https://api.deepseek.com/v1/chat/completions"
        self.model_name = "deepseek-chat"
        self.api_key = os.getenv("DEEPSEEK_API_KEY", "")
        
        if not self.api_key:
            print("❌ 请设置DEEPSEEK_API_KEY环境变量")
            print("💡 设置方法: export DEEPSEEK_API_KEY='your-api-key'")
            print("🔑 获取API密钥: https://platform.deepseek.com/api_keys")
            sys.exit(1)
    
    def load_financial_data(self, json_file_path: str) -> Dict[str, Any]:
        """加载财务数据JSON文件"""
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ 加载数据文件失败: {e}")
            return {}
    
    def prepare_financial_summary(self, data: Dict[str, Any]) -> str:
        """准备财务数据摘要用于DeepSeek分析"""
        if not data:
            return ""
        
        summary = f"""
# ZA Bank Limited 财务表现分析数据 (2020-2024)

## 基本信息
- 公司名称: {data.get('company_name', 'N/A')}
- 分析期间: {data.get('data_period', 'N/A')}

## 关键财务指标增长分析
"""
        
        growth_analysis = data.get('summary', {}).get('growth_analysis', {})
        for metric, values in growth_analysis.items():
            if isinstance(values, dict):
                start_val = values.get('start_value', 0)
                end_val = values.get('end_value', 0)
                growth_rate = values.get('growth_rate_percent', 0)
                
                if metric == 'Total Assets':
                    summary += f"- 总资产: {start_val/1000000:.1f}亿港币 → {end_val/1000000:.1f}亿港币 (增长{growth_rate:.1f}%)\n"
                elif metric == 'Total Liabilities':
                    summary += f"- 总负债: {start_val/1000000:.1f}亿港币 → {end_val/1000000:.1f}亿港币 (增长{growth_rate:.1f}%)\n"
                elif metric == 'Total Equity':
                    summary += f"- 股东权益: {start_val/1000000:.1f}亿港币 → {end_val/1000000:.1f}亿港币 (增长{growth_rate:.1f}%)\n"
        
        summary += "\n## 年度关键指标\n"
        key_metrics = data.get('summary', {}).get('key_metrics', {})
        for year, metrics in key_metrics.items():
            if isinstance(metrics, dict):
                assets = metrics.get('total_assets_billion_hkd', 0)
                asset_ratio = metrics.get('asset_liability_ratio', 0)
                equity_ratio = metrics.get('equity_ratio', 0)
                summary += f"- {year}年: 总资产{assets:.1f}亿港币, 资产负债率{asset_ratio:.1f}%, 权益比率{equity_ratio:.1f}%\n"
        
        # 添加损益表关键数据
        latest_year_data = data.get('yearly_data', {}).get('2024', {})
        if latest_year_data:
            income_data = latest_year_data.get('income_statement', {}).get('data', [])
            summary += "\n## 2024年损益表关键项目\n"
            for item in income_data:
                if item.get('Item') in ['Net interest income', 'Net fee and commission income', 
                                       'Operating expenses', 'Net loss for the period']:
                    item_name = item.get('Item', '')
                    current_val = item.get('2024', 0)
                    if 'Net interest income' in item_name:
                        summary += f"- 净利息收入: {current_val/1000:.1f}万港币\n"
                    elif 'Net fee and commission income' in item_name:
                        summary += f"- 净手续费收入: {current_val/1000:.1f}万港币\n"
                    elif 'Net loss for the period' in item_name:
                        summary += f"- 净亏损: {abs(current_val)/1000:.1f}万港币\n"
        
        return summary
    
    def analyze_with_deepseek(self, financial_data: Dict[str, Any]) -> Optional[str]:
        """使用DeepSeek分析财务数据"""
        data_summary = self.prepare_financial_summary(financial_data)
        
        if not data_summary:
            print("❌ 无法准备财务数据摘要")
            return None
        
        # 构建专业的分析提示词
        prompt = f"""
As a professional banking financial analyst, provide a concise and professional analysis of ZA Bank Limited's financial data:

{data_summary}

**Constraints:**
- Report length: 400-600 words maximum
- Focus on 3-4 key insights only
- Data-driven analysis with minimal narrative
- Bullet-point format for clarity

Please analyze from the following dimensions:

1. **Financial Performance Overview** (120 words max)
   - Asset growth drivers
   - Profitability trends
   - Capital structure changes

2. **Key Risk Assessment** (120 words max)
   - Asset-liability ratio risks
   - Major financial risk factors

3. **Business Development** (120 words max)
   - Virtual banking competitive position
   - Revenue structure optimization

4. **Outlook & Recommendations** (120 words max)
   - Near-term challenges
   - Strategic recommendations

Please respond in professional English, keeping each section within the specified word limits and highlighting data insights.
"""
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model_name,
            "messages": [
                {
                    "role": "system", 
                    "content": "You are a senior banking financial analyst specializing in virtual banks and FinTech companies. You have deep financial expertise and extensive industry experience, capable of providing professional, objective, and insightful financial analysis reports in English."
                },
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 4000,
            "stream": False
        }
        
        try:
            print("🤖 正在调用DeepSeek API进行专业财务分析...")
            start_time = time.time()
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=120)
            end_time = time.time()
            
            # 显示API调用时间信息
            elapsed_time = end_time - start_time
            print(f"⏱️ API调用完成，耗时: {elapsed_time:.2f}秒")
            
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            else:
                print(f"❌ DeepSeek API调用失败: {response.status_code}")
                print(f"错误信息: {response.text}")
                return None
                
        except requests.exceptions.Timeout:
            print("❌ 请求超时，请检查网络连接")
            return None
        except requests.exceptions.ConnectionError:
            print("❌ 无法连接到DeepSeek API，请检查网络")
            return None
        except Exception as e:
            print(f"❌ 调用DeepSeek API时出错: {e}")
            return None
    
    def save_analysis_report(self, analysis: str, output_path: str = "./output") -> Optional[str]:
        """保存分析报告"""
        if not analysis:
            print("❌ 没有分析结果可保存")
            return None
        
        os.makedirs(output_path, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"ZA_Bank_DeepSeek_Analysis_{timestamp}.md"
        filepath = os.path.join(output_path, filename)
        
        # 构建完整的markdown报告
        report = f"""# ZA Bank Limited Professional Financial Analysis Report

**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Analysis Model**: DeepSeek Chat (Concise Version)  
**Data Period**: 2020-2024  
**Analysis Type**: Virtual Bank Financial Performance Analysis  
**Report Features**: 400-600 words, key insights focused

---

{analysis}

---

## Disclaimer

*This report is generated by DeepSeek LLM based on provided financial data, for reference and academic research purposes only. It does not constitute any investment advice. Investment decisions should be based on complete financial statements, market conditions, and professional advisory services.*

---

**Report Generation Tool**: Financial Analysis System | HKU Capstone Project
"""
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"✅ 分析报告已保存至: {filepath}")
            return filepath
        except Exception as e:
            print(f"❌ 保存报告失败: {e}")
            return None

def find_latest_financial_data() -> Optional[str]:
    """查找最新的财务数据文件"""
    output_dir = "./output"
    if not os.path.exists(output_dir):
        return None
        
    json_files = [f for f in os.listdir(output_dir) 
                  if f.startswith("ZA_Bank_Multi_Year_Analysis_") and f.endswith(".json")]
    
    if not json_files:
        return None
    
    # 返回最新的文件
    latest_file = sorted(json_files)[-1]
    return os.path.join(output_dir, latest_file)

def main():
    """主函数"""
    print("=" * 60)
    print("ZA Bank 财务表现 - DeepSeek AI 专业分析")
    print("=" * 60)
    
    # 查找财务数据文件
    print("📊 查找财务数据文件...")
    json_file_path = find_latest_financial_data()
    
    if not json_file_path:
        print("❌ 未找到ZA Bank财务数据文件")
        print("💡 请先运行: python3 generate_za_bank_trends.py")
        return
    
    print(f"📄 使用数据文件: {os.path.basename(json_file_path)}")
    
    # 初始化DeepSeek分析器
    try:
        analyzer = DeepSeekFinancialAnalyzer()
    except SystemExit:
        return
    
    # 加载财务数据
    print("📈 加载财务数据...")
    financial_data = analyzer.load_financial_data(json_file_path)
    
    if not financial_data:
        print("❌ 财务数据加载失败")
        return
    
    print("🧠 开始DeepSeek AI专业分析...")
    print("⏳ 这可能需要30-60秒，请耐心等待...")
    
    # 使用DeepSeek进行分析
    analysis_result = analyzer.analyze_with_deepseek(financial_data)
    
    if analysis_result:
        print("✅ 分析完成!")
        print("\n" + "="*60)
        print("📋 DeepSeek AI 专业分析结果:")
        print("="*60)
        print(analysis_result)
        
        # 保存报告
        report_path = analyzer.save_analysis_report(analysis_result)
        if report_path:
            print(f"\n📁 完整报告已保存至: {os.path.basename(report_path)}")
            
    else:
        print("❌ DeepSeek分析失败")
        print("\n💡 请检查:")
        print("1. 网络连接是否正常")
        print("2. API密钥是否正确设置")
        print("3. DeepSeek服务是否可用")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    main() 