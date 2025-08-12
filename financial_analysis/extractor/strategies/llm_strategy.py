"""
LLM提取策略 - 包含DeepSeek客户端
LLM Extraction Strategy with DeepSeek Client
"""

import os
import json
import requests
import hashlib
from pathlib import Path
from typing import Any, Optional, Dict
from .base_strategy import BaseStrategy, ExtractionResult

# 尝试加载环境变量
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # 手动从.env文件加载
    env_file = Path(__file__).parent.parent.parent.parent / '.env'
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    if '=' in line:
                        key, value = line.strip().split('=', 1)
                        os.environ[key] = value


class DeepSeekClient:
    """DeepSeek API 客户端"""
    
    def __init__(self, api_key: Optional[str] = None):
        """初始化客户端"""
        self.api_key = api_key or os.getenv('DEEPSEEK_API_KEY')
        if not self.api_key:
            raise ValueError("未找到DeepSeek API密钥")
        
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
    
    def extract_financial_data(self, text: str, company_name: str = "", year: str = "") -> Dict:
        """使用LLM提取财务数据"""
        # 构建系统提示词
        system_prompt = """你是一个专业的财务数据提取助手。请从财务报表文本中准确提取以下数据：

1. 总资产 (Total Assets / Ativo Total / 总资产) - 资产负债表中的资产总计
2. 总负债 (Total Liabilities / Passivo Total / 总负债) - 资产负债表中的负债总计
3. 营业收入 (Revenue / Receita / 营业收入) - 损益表中的总收入或营业收入
4. 净利润 (Net Profit/Loss / Lucro Líquido / 净利润) - 损益表中的净利润或净亏损

注意事项：
- 请提取最新期间的数据（如有多个期间）
- 数字应该是原始值，不要进行单位转换
- 如果是负数（亏损），请保留负号
- 如果文本中有明确的TOTAL ASSETS、TOTAL LIABILITIES等标签，优先使用这些数据
- 如果发现表格数据，请提取表格中的相应数值

返回JSON格式：
{
    "total_assets": 数值或null,
    "total_liabilities": 数值或null,
    "revenue": 数值或null,
    "net_profit": 数值或null
}"""
        
        # 构建用户提示词
        user_prompt = f"""请从以下财务报表文本中提取数据：

公司：{company_name if company_name else '未知'}
年份：{year if year else '未知'}

文本内容：
{text[:8000]}  # 增加文本长度以包含更多财务数据

请仔细查找并提取：
1. TOTAL ASSETS（总资产）的数值
2. TOTAL LIABILITIES（总负债）的数值  
3. Revenue/Total Revenue（营业收入）的数值
4. Net Profit/Net Loss（净利润/净亏损）的数值

如果找到多个期间的数据，请提取最新的数据。"""
        
        # 检查缓存
        cache_key = self._get_cache_key(text, user_prompt)
        cached_result = self._check_cache(cache_key)
        if cached_result:
            return cached_result
        
        # 调用API
        try:
            print(f"      🌐 调用DeepSeek API...")
            api_payload = {
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.1,
                "max_tokens": 500
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=api_payload,
                timeout=30
            )
            
            print(f"      📡 API响应状态: {response.status_code}")
            response.raise_for_status()
            result = response.json()
            
            # 解析响应
            content = result['choices'][0]['message']['content']
            
            # 尝试解析JSON
            try:
                import re
                json_match = re.search(r'\{[\s\S]*\}', content)
                if json_match:
                    extracted_data = json.loads(json_match.group())
                else:
                    extracted_data = self._parse_text_response(content)
            except:
                extracted_data = self._parse_text_response(content)
            
            # 保存缓存
            self._save_cache(cache_key, extracted_data)
            
            return extracted_data
            
        except Exception as e:
            print(f"    ❌ API请求失败: {str(e)[:100]}")
            return {
                "total_assets": None,
                "total_liabilities": None,
                "revenue": None,
                "net_profit": None
            }
    
    def _parse_text_response(self, text: str) -> Dict:
        """解析文本格式的响应"""
        import re
        
        result = {
            "total_assets": None,
            "total_liabilities": None,
            "revenue": None,
            "net_profit": None
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


class LLMStrategy(BaseStrategy):
    """LLM提取策略"""
    
    def __init__(self, api_key: Optional[str] = None):
        """初始化LLM策略"""
        super().__init__(name="llm")
        self.client = None
        
        try:
            self.client = DeepSeekClient(api_key)
            print("  ✅ LLM策略已初始化")
        except Exception as e:
            print(f"  ⚠️ LLM策略初始化失败: {e}")
    
    def can_handle(self, content: Any) -> bool:
        """判断是否能处理"""
        return (
            self.client is not None and 
            isinstance(content, str) and 
            len(content) > 0
        )
    
    def extract(self, content: str, **kwargs) -> ExtractionResult:
        """使用LLM提取财务数据"""
        result = ExtractionResult(method="llm")
        
        if not self.client:
            print("    ❌ LLM客户端未初始化")
            return result
        
        try:
            # 限制文本长度
            text_limit = kwargs.get('text_limit', 5000)
            limited_text = content[:text_limit] if content else ""
            
            if not limited_text:
                print("    ❌ 没有文本内容可供LLM提取")
                return result
            
            print(f"    📝 准备发送 {len(limited_text)} 字符给LLM...")
            
            # 调用LLM提取
            llm_result = self.client.extract_financial_data(
                limited_text,
                company_name=kwargs.get('company_name', ''),
                year=kwargs.get('year', '')
            )
            
            if llm_result:
                print(f"    ✅ LLM返回结果: {llm_result}")
                # 转换结果
                result.total_assets = llm_result.get('total_assets')
                result.total_liabilities = llm_result.get('total_liabilities')
                result.revenue = llm_result.get('revenue')
                result.net_profit = llm_result.get('net_profit')
                result.update_confidence()
                print(f"    📊 提取到 {result.fields_count}/4 个字段")
            else:
                print("    ⚠️ LLM未返回有效结果")
                
        except Exception as e:
            print(f"    ❌ LLM提取异常: {str(e)}")
            import traceback
            traceback.print_exc()
        
        return result