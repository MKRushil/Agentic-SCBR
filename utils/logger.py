"""日誌工具"""
import logging
import sys
from pathlib import Path

def setup_logger(name: str = "TCM-CBR", level: str = "INFO") -> logging.Logger:
    """設置日誌器"""
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))

    # 避免重複添加處理器
    if logger.handlers:
        return logger

    # 控制台處理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)

    # 格式化
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)

    logger.addHandler(console_handler)

    return logger

logger = setup_logger()
