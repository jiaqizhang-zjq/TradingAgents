"""
统一日志系统 - 增强版
"""

import logging
import sys
import re
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional


class SensitiveDataFilter(logging.Filter):
    """敏感数据过滤器 - 自动脱敏API密钥等敏感信息"""
    
    PATTERNS = [
        (re.compile(r'(api[_-]?key\s*[=:]\s*)["\']?([a-zA-Z0-9\-_]{10,})["\']?', re.IGNORECASE), r'\1***'),
        (re.compile(r'(token\s*[=:]\s*)["\']?([a-zA-Z0-9\-_]{10,})["\']?', re.IGNORECASE), r'\1***'),
        (re.compile(r'(password\s*[=:]\s*)["\']?([^\s"\']+)["\']?', re.IGNORECASE), r'\1***'),
        (re.compile(r'(secret\s*[=:]\s*)["\']?([^\s"\']+)["\']?', re.IGNORECASE), r'\1***'),
    ]
    
    def filter(self, record: logging.LogRecord) -> bool:
        """过滤敏感信息"""
        if isinstance(record.msg, str):
            for pattern, replacement in self.PATTERNS:
                record.msg = pattern.sub(replacement, record.msg)
        return True


class ColoredFormatter(logging.Formatter):
    """彩色日志格式化器（终端输出）"""
    
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'
    }
    
    def format(self, record: logging.LogRecord) -> str:
        """格式化日志，添加颜色"""
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{self.COLORS['RESET']}"
        return super().format(record)


def setup_logger(
    name: str,
    level: str = "INFO",
    log_file: Optional[str] = None,
    console_output: bool = True,
    colored: bool = True,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> logging.Logger:
    """
    设置日志记录器
    
    Args:
        name: 日志记录器名称（通常使用 __name__）
        level: 日志级别 (DEBUG/INFO/WARNING/ERROR/CRITICAL)
        log_file: 日志文件路径，None则不写文件
        console_output: 是否输出到控制台
        colored: 控制台输出是否使用颜色
        max_bytes: 单个日志文件最大字节数
        backup_count: 保留的日志文件备份数量
        
    Returns:
        配置好的Logger实例
        
    Example:
        >>> logger = setup_logger(__name__)
        >>> logger.info("Processing stock %s", "AAPL")
        >>> logger.error("Failed to fetch data: %s", error)
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # 避免重复添加handler
    if logger.handlers:
        return logger
    
    # 添加敏感数据过滤器
    logger.addFilter(SensitiveDataFilter())
    
    # 格式定义
    detailed_format = '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
    simple_format = '%(asctime)s - %(levelname)s - %(message)s'
    
    # 控制台Handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, level.upper()))
        
        if colored:
            formatter = ColoredFormatter(simple_format, datefmt='%H:%M:%S')
        else:
            formatter = logging.Formatter(simple_format, datefmt='%H:%M:%S')
        
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # 文件Handler
    if log_file:
        # 确保日志目录存在
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)  # 文件记录所有级别
        file_formatter = logging.Formatter(detailed_format, datefmt='%Y-%m-%d %H:%M:%S')
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    获取已配置的Logger（如果未配置则使用默认配置）
    
    Args:
        name: Logger名称
        
    Returns:
        Logger实例
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        # 如果没有配置过，使用默认配置
        return setup_logger(name)
    return logger


def disable_external_loggers(level: str = "WARNING") -> None:
    """
    禁用/降低外部库的日志级别
    
    Args:
        level: 外部日志的最低级别
    """
    external_loggers = [
        'urllib3',
        'requests',
        'httpx',
        'openai',
        'anthropic',
        'google',
        'langchain',
        'langgraph',
    ]
    
    for logger_name in external_loggers:
        logging.getLogger(logger_name).setLevel(getattr(logging, level.upper()))


# 创建默认的应用日志记录器
def get_app_logger() -> logging.Logger:
    """
    获取应用级别的默认Logger
    
    Returns:
        应用Logger
    """
    return setup_logger(
        'tradingagents',
        level='INFO',
        log_file='logs/tradingagents.log',
        console_output=True,
        colored=True
    )


if __name__ == "__main__":
    # 测试日志系统
    logger = setup_logger(__name__, level="DEBUG")
    
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")
    
    # 测试敏感信息脱敏
    logger.info("api_key=sk-1234567890abcdef")
    logger.info("password=secret123")
