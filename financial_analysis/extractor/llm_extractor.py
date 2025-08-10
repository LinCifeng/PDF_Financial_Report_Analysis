#!/usr/bin/env python3
"""
DeepSeek API 客户端
DeepSeek API Client for Financial Data Extraction
"""
import os
import json
import time
from typing import Dict, List, Optional
import requests
from pathlib import Path

# 尝试加载环境变量
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # 如果没有dotenv，直接从.env文件读取
    env_path = Path(__file__).parent.parent.parent / '.env'
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value


class DeepSeekClient:
    """DeepSeek API 客户端"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        初始化客户端
        
        Args:
            api_key: API密钥，如果不提供则从环境变量读取
        """
        self.api_key = api_key or os.getenv('DEEPSEEK_API_KEY')
        if not self.api_key:
            raise ValueError("未找到DeepSeek API密钥。请设置DEEPSEEK_API_KEY环境变量或传入api_key参数。")
        
        self.base_url = "https://api.deepseek.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # 缓存目录
        self.cache_dir = Path("output/llm_cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_cache_key(self, content: str, prompt: str) -> str:
        """生成缓存键"""
        import hashlib
        combined = f"{content[:100]}_{prompt[:50]}"
        return hashlib.md5(combined.encode()).hexdigest()
    
    def _check_cache(self, cache_key: str) -> Optional[Dict]:
        """检查缓存"""
        cache_file = self.cache_dir / f"{cache_key}.json"
        if cache_file.exists():
            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    
    def _save_cache(self, cache_key: str, result: Dict):
        """保存缓存"""
        cache_file = self.cache_dir / f"{cache_key}.json"
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
    
    def extract_financial_data(self, text: str, company_name: str = "", year: int = None) -> Dict:
        """
        使用LLM提取财务数据
        
        Args:
            text: PDF提取的文本内容
            company_name: 公司名称（可选）
            year: 年份（可选）
            
        Returns:
            提取的财务数据字典
        """
        # 构建系统提示词
        system_prompt = """你是一个专业的财务数据提取助手。你的任务是从财务报表文本中准确提取以下四个关键指标：
1. 总资产 (Total Assets)
2. 总负债 (Total Liabilities) 
3. 营业收入 (Revenue/Operating Income)
4. 净利润 (Net Profit/Loss)

请注意：
- 数字可能包含逗号分隔符，如 1,234,567
- 负数可能用括号表示，如 (123,456) 表示 -123,456
- 单位可能是千元、百万元等，请转换为实际数值
- 如果找不到某个指标，返回null

请以JSON格式返回结果，格式如下：
{
    "total_assets": 数值或null,
    "total_liabilities": 数值或null,
    "revenue": 数值或null,
    "net_profit": 数值或null,
    "confidence": "high/medium/low",
    "notes": "任何重要说明"
}"""
        
        # 构建用户提示词
        user_prompt = f"""请从以下财务报表文本中提取数据：

公司：{company_name if company_name else '未知'}
年份：{year if year else '未知'}

文本内容：
{text[:3000]}  # 限制文本长度以控制成本

请提取总资产、总负债、营业收入和净利润的数值。"""
        
        # 检查缓存
        cache_key = self._get_cache_key(text, user_prompt)
        cached_result = self._check_cache(cache_key)
        if cached_result:
            return cached_result
        
        # 调用API
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json={
                    "model": "deepseek-chat",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "temperature": 0.1,  # 低温度以提高准确性
                    "max_tokens": 500
                },
                timeout=30
            )
            
            response.raise_for_status()
            result = response.json()
            
            # 解析响应
            content = result['choices'][0]['message']['content']
            
            # 尝试解析JSON
            try:
                # 查找JSON部分
                import re
                json_match = re.search(r'\{[\s\S]*\}', content)
                if json_match:
                    extracted_data = json.loads(json_match.group())
                else:
                    # 如果没有找到JSON，尝试解析文本
                    extracted_data = self._parse_text_response(content)
            except:
                extracted_data = self._parse_text_response(content)
            
            # 保存缓存
            self._save_cache(cache_key, extracted_data)
            
            return extracted_data
            
        except requests.exceptions.RequestException as e:
            print(f"API请求失败: {e}")
            return {
                "total_assets": None,
                "total_liabilities": None,
                "revenue": None,
                "net_profit": None,
                "error": str(e)
            }
        except Exception as e:
            print(f"处理响应时出错: {e}")
            return {
                "total_assets": None,
                "total_liabilities": None,
                "revenue": None,
                "net_profit": None,
                "error": str(e)
            }
    
    def _parse_text_response(self, text: str) -> Dict:
        """解析文本格式的响应"""
        import re
        
        result = {
            "total_assets": None,
            "total_liabilities": None,
            "revenue": None,
            "net_profit": None,
            "confidence": "low",
            "notes": "Parsed from text response"
        }
        
        # 定义模式
        patterns = {
            "total_assets": [
                r'总资产[:：]\s*([0-9,]+)',
                r'[Tt]otal\s+[Aa]ssets?[:：]\s*([0-9,]+)'
            ],
            "total_liabilities": [
                r'总负债[:：]\s*([0-9,]+)',
                r'[Tt]otal\s+[Ll]iabilities?[:：]\s*([0-9,]+)'
            ],
            "revenue": [
                r'营业收入[:：]\s*([0-9,]+)',
                r'[Rr]evenue[:：]\s*([0-9,]+)'
            ],
            "net_profit": [
                r'净利润[:：]\s*\(?([0-9,]+)\)?',
                r'[Nn]et\s+[Pp]rofit[:：]\s*\(?([0-9,]+)\)?'
            ]
        }
        
        # 尝试匹配
        for field, pattern_list in patterns.items():
            for pattern in pattern_list:
                match = re.search(pattern, text)
                if match:
                    try:
                        value = float(match.group(1).replace(',', ''))
                        result[field] = value
                        break
                    except:
                        pass
        
        return result
    
    def estimate_cost(self, text_length: int, num_calls: int = 1) -> float:
        """
        估算API调用成本
        
        Args:
            text_length: 文本长度
            num_calls: 调用次数
            
        Returns:
            预估成本（美元）
        """
        # DeepSeek定价：约 $0.14 / 1M tokens (输入) + $0.28 / 1M tokens (输出)
        # 估算：1个字符约等于0.5个token
        input_tokens = (text_length * 0.5 + 500) / 1000000  # 包括提示词
        output_tokens = 0.0005  # 输出约500 tokens
        
        cost_per_call = input_tokens * 0.14 + output_tokens * 0.28
        return cost_per_call * num_calls


if __name__ == "__main__":
    # 测试客户端
    client = DeepSeekClient()
    
    # 测试文本
    test_text = """
    Financial Statement 2023
    
    Total Assets: $1,234,567,890
    Total Liabilities: $987,654,321
    Revenue: $456,789,012
    Net Profit: ($12,345,678)
    """
    
    result = client.extract_financial_data(test_text, "TestCompany", 2023)
    print("提取结果:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    # 估算成本
    cost = client.estimate_cost(len(test_text))
    print(f"\n预估成本: ${cost:.4f}")