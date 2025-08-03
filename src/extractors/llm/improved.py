"""
Improved LLM Extractor with Better Prompts
改进的LLM提取器，优化提示词
"""

import json
import logging
import os
from pathlib import Path
from typing import Optional, Dict, Any, List
import requests
from datetime import datetime

from .base_extractor import BaseExtractor
from ..core.models import FinancialData, FinancialReport, ExtractionResult, DataStatus


class ImprovedLLMExtractor(BaseExtractor):
    """Improved extractor with better prompts for net profit extraction."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize improved LLM extractor."""
        super().__init__(config)
        
        # API configuration
        self.api_key = os.environ.get('DEEPSEEK_API_KEY')
        if not self.api_key and config:
            self.api_key = config.get('apis', {}).get('deepseek', {}).get('api_key')
            
        if not self.api_key:
            raise ValueError("DeepSeek API key not found.")
        
        self.api_url = "https://api.deepseek.com/v1/chat/completions"
        self.model = "deepseek-chat"
        self.max_tokens = 3000
        
        # Enhanced system prompt
        self.system_prompt = """你是一个专业的财务数据提取专家，特别擅长从财务报告中准确提取净利润数据。

重要提取规则：
1. 净利润可能出现的名称：净利润、净收益、本年利润、当期损益、净损失（负数）、年度利润、利润总额、Net Profit、Net Income、Net Loss
2. 注意区分：毛利润、营业利润、税前利润都不是净利润
3. 如果是亏损，必须返回负数
4. 优先查找损益表、利润表、综合收益表
5. 如果找到多个年份，只返回指定年份的数据

请始终返回准确的JSON格式。"""

        # Improved extraction prompt
        self.extraction_prompt_template = """请从以下财务报告中精确提取财务数据。

公司：{company_name}
年份：{fiscal_year}

文本内容（请仔细查找净利润相关数据）：
{text_content}

已提取数据（供参考）：
{regex_results}

重点任务：
1. 查找净利润/净收益/净损失 - 通常在损益表最下方
2. 注意单位转换：如果是"百万"转为"千"（×1000），如果是"亿"转为"千"（×100000）
3. 负数表示亏损，必须保留负号
4. 查找关键词：
   - 中文：本公司拥有人应占利润、股东应占净利润、归属于母公司所有者的净利润
   - 英文：Net profit attributable to shareholders, Profit for the year

请返回JSON格式：
{{
  "total_assets": 总资产（千元）或null,
  "total_liabilities": 总负债（千元）或null,
  "total_equity": 总权益（千元）或null,
  "revenue": 营业收入（千元）或null,
  "net_profit": 净利润（千元，亏损为负）或null,
  "operating_cash_flow": 经营现金流（千元）或null,
  "found_profit_description": "找到净利润的具体描述文字",
  "currency": "HKD/CNY/USD",
  "unit": "thousand",
  "confidence": 0.0-1.0,
  "notes": "提取说明"
}}"""

    def can_handle(self, file_path: Path) -> bool:
        """LLM extractor doesn't directly handle files."""
        return False
    
    def extract_with_improved_prompt(self, 
                                   text_content: str,
                                   company_name: str,
                                   fiscal_year: int,
                                   regex_results: Optional[Dict[str, Any]] = None,
                                   table_results: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Extract with improved prompts focusing on net profit."""
        
        # Focus on relevant sections
        profit_keywords = [
            '净利润', '净收益', '净损失', '本年利润', '年度利润', 
            'net profit', 'net income', 'net loss', 'profit for the year',
            '本公司拥有人应占', '股东应占', '归属于母公司'
        ]
        
        # Extract relevant text sections
        relevant_sections = []
        lines = text_content.split('\n')
        for i, line in enumerate(lines):
            if any(keyword.lower() in line.lower() for keyword in profit_keywords):
                # Get context: 3 lines before and after
                start = max(0, i-3)
                end = min(len(lines), i+4)
                relevant_sections.append('\n'.join(lines[start:end]))
        
        # If found relevant sections, prioritize them
        if relevant_sections:
            focused_text = '\n\n---相关段落---\n\n'.join(relevant_sections)
            text_to_analyze = focused_text + '\n\n---完整文本---\n\n' + text_content[:5000]
        else:
            text_to_analyze = text_content[:8000]
        
        # Prepare the prompt
        prompt = self.extraction_prompt_template.format(
            company_name=company_name,
            fiscal_year=fiscal_year,
            text_content=text_to_analyze,
            regex_results=json.dumps(regex_results or {}, ensure_ascii=False, indent=2),
            table_results=json.dumps(table_results or {}, ensure_ascii=False, indent=2)
        )
        
        # Call LLM API
        try:
            response = self._call_deepseek_api(prompt)
            
            if response:
                return self._parse_llm_response(response)
            else:
                self.logger.error("Empty response from LLM")
                return {}
                
        except Exception as e:
            self.logger.error(f"Error calling LLM API: {str(e)}")
            return {}
    
    def _call_deepseek_api(self, prompt: str) -> str:
        """Call DeepSeek API with improved error handling."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": self.max_tokens,
            "temperature": 0.1,
            "response_format": {"type": "json_object"}
        }
        
        try:
            response = requests.post(
                self.api_url,
                headers=headers,
                json=data,
                timeout=45
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('choices', [{}])[0].get('message', {}).get('content', '')
            else:
                self.logger.error(f"API error: {response.status_code} - {response.text}")
                return ""
                
        except requests.exceptions.Timeout:
            self.logger.error("API request timeout")
            return ""
        except Exception as e:
            self.logger.error(f"API request failed: {str(e)}")
            return ""
    
    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response with better error handling."""
        try:
            data = json.loads(response)
            
            # Log if net profit was found
            if data.get('net_profit') is not None:
                self.logger.info(f"Successfully extracted net profit: {data['net_profit']}")
                if data.get('found_profit_description'):
                    self.logger.info(f"Found in text: {data['found_profit_description']}")
            
            # Clean and validate data
            cleaned_data = {}
            numeric_fields = [
                'total_assets', 'total_liabilities', 'total_equity',
                'revenue', 'net_profit', 'operating_cash_flow'
            ]
            
            for field in numeric_fields:
                if field in data and data[field] is not None:
                    try:
                        value = float(data[field])
                        # Validate reasonable ranges
                        if field == 'net_profit' and abs(value) > 1e12:  # > 1 trillion
                            self.logger.warning(f"Suspiciously large net profit: {value}")
                        cleaned_data[field] = value
                    except (ValueError, TypeError):
                        self.logger.warning(f"Invalid numeric value for {field}: {data[field]}")
            
            # Add metadata
            cleaned_data['currency'] = data.get('currency', 'HKD')
            cleaned_data['unit'] = data.get('unit', 'thousand')
            cleaned_data['confidence'] = float(data.get('confidence', 0.5))
            cleaned_data['llm_notes'] = data.get('notes', '')
            if data.get('found_profit_description'):
                cleaned_data['profit_source'] = data['found_profit_description']
            
            return cleaned_data
            
        except json.JSONDecodeError:
            self.logger.error(f"Failed to parse LLM response as JSON: {response[:200]}")
            return {}
        except Exception as e:
            self.logger.error(f"Error parsing LLM response: {str(e)}")
            return {}
    
    def extract(self, file_path: Path, report: FinancialReport) -> ExtractionResult:
        """Not used directly."""
        return ExtractionResult(
            report=report,
            error="Use SmartFinancialExtractor instead"
        )