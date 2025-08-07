"""
项目配置文件
Project Configuration Settings

作者: Lin Cifeng
创建时间: 2024-08-07
"""
import os
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent

# 数据目录
DATA_DIR = PROJECT_ROOT / "data"
RAW_REPORTS_DIR = DATA_DIR / "raw_reports"
COMPANY_CSV = DATA_DIR / "Company_Financial_report.csv"

# 输出目录
OUTPUT_DIR = PROJECT_ROOT / "output"
RESULTS_DIR = OUTPUT_DIR / "results"
REPORTS_DIR = OUTPUT_DIR / "reports"
CACHE_DIR = OUTPUT_DIR / "cache"
ARCHIVE_DIR = OUTPUT_DIR / "archive"

# 确保目录存在
for dir_path in [RESULTS_DIR, REPORTS_DIR, CACHE_DIR, ARCHIVE_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# API配置
DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')

# 处理配置
BATCH_SIZE = int(os.environ.get('BATCH_SIZE', 100))
MAX_WORKERS = int(os.environ.get('MAX_WORKERS', 5))
RETRY_TIMES = int(os.environ.get('RETRY_TIMES', 2))
REQUEST_TIMEOUT = 30  # 秒

# LLM配置
LLM_MODEL = "deepseek-chat"
LLM_TEMPERATURE = 0.1
LLM_MAX_TOKENS = 4000
USE_LLM_CACHE = True

# 提取配置
EXTRACTION_FIELDS = [
    # 资产负债表
    'total_assets', 'total_liabilities', 'total_equity',
    'cash_and_equivalents', 'loans_and_advances', 'customer_deposits',
    # 损益表
    'revenue', 'net_profit', 'operating_expenses', 'ebit',
    'interest_income', 'net_interest_income', 'fee_income',
    # 现金流量表
    'operating_cash_flow', 'investing_cash_flow', 'financing_cash_flow'
]

# 核心字段（用于快速验证）
CORE_FIELDS = ['total_assets', 'total_liabilities', 'revenue', 'net_profit']

# 数据验证配置
TOLERANCE = 0.01  # 1%的容差
MIN_CONFIDENCE = 0.7  # 最小置信度

# 日志配置
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# 文件格式配置
SUPPORTED_FORMATS = ['.pdf', '.html']
OUTPUT_FORMAT = 'csv'  # 可选: csv, json, excel

# 可视化配置
PLOT_STYLE = 'seaborn'
FIGURE_SIZE = (12, 8)
DPI = 100

# 语言配置
SUPPORTED_LANGUAGES = ['zh', 'en', 'ja']
DEFAULT_LANGUAGE = 'zh'