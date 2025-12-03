"""
共享数据库基础设施
"""
from pathlib import Path

# 数据目录
DATA_DIR = Path(__file__).parent.parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

