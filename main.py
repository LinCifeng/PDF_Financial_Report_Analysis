#!/usr/bin/env python3
"""
财务数据分析项目主入口
Financial Analysis Project Main Entry
"""

import sys
import os

# 添加scripts目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'scripts'))

# 导入并运行主程序
from main import main

if __name__ == "__main__":
    main()