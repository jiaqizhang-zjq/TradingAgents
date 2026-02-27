#!/usr/bin/env python3
"""
统一日志系统
提供结构化日志、性能追踪、日志轮转功能
"""

import logging
import sys
from pathlib import Path
from typing import Optional
from logging.handlers import RotatingFileHandler
from functools import wraps
import time


class LoggerConfig:
    """日志配置"""
    
    # 日志级别
    LEVEL = logging.INFO
    
    # 日志格式
    FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
    
    # 日志文件配置
    LOG_DIR = Path("logs")
    LOG_FILE = "tradingagents.log"
    MAX_BYTES = 10 * 1024 * 1024  # 10MB
    BACKUP_COUNT = 5
    
    # 控制台输出
    CONSOLE_ENABLED = True
    CONSOLE_LEVEL = logging.INFO


def setup_logger(
    name: str = "tradingagents",
    level: Optional[int] = None,
    log_file: Optional[str] = None,
    console_enabled: Optional[bool] = None
) -> logging.Logger:
    """
    配置并获取logger实例
    
    Args:
        name: logger名称
        level: 日志级别
        log_file: 日志文件名
        console_enabled: 是否启用控制台输出
        
    Returns:
        配置好的logger实例
    """
    logger = logging.getLogger(name)
    
    # 避免重复配置
    if logger.handlers:
        return logger
    
    # 设置日志级别
    level = level or LoggerConfig.LEVEL
    logger.setLevel(level)
    
    # 创建格式化器
    formatter = logging.Formatter(
        fmt=LoggerConfig.FORMAT,
        datefmt=LoggerConfig.DATE_FORMAT
    )
    
    # 配置文件处理器
    if log_file is not None or LoggerConfig.LOG_FILE:
        log_file = log_file or LoggerConfig.LOG_FILE
        log_path = LoggerConfig.LOG_DIR / log_file
        
        # 确保日志目录存在
        LoggerConfig.LOG_DIR.mkdir(parents=True, exist_ok=True)
        
        file_handler = RotatingFileHandler(
            filename=log_path,
            maxBytes=LoggerConfig.MAX_BYTES,
            backupCount=LoggerConfig.BACKUP_COUNT,
            encoding='utf-8'
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # 配置控制台处理器
    console_enabled = console_enabled if console_enabled is not None else LoggerConfig.CONSOLE_ENABLED
    if console_enabled:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(LoggerConfig.CONSOLE_LEVEL)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    return logger


def get_logger(name: str = "tradingagents") -> logging.Logger:
    """
    获取logger实例（通过依赖注入容器）
    
    Args:
        name: logger名称
        
    Returns:
        logger实例
    """
    from tradingagents.core.container import get_container
    
    container = get_container()
    service_name = f'logger_{name}'
    
    if not container.has(service_name):
        container.register(
            service_name,
            lambda: setup_logger(name),
            singleton=True
        )
    
    return container.get(service_name)


def log_execution_time(logger: Optional[logging.Logger] = None):
    """
    装饰器：记录函数执行时间
    
    Args:
        logger: logger实例，None则使用默认logger
        
    Example:
        @log_execution_time()
        def my_function():
            pass
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            _logger = logger or get_logger()
            
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                elapsed = time.time() - start_time
                _logger.info(f"{func.__name__} executed in {elapsed:.3f}s")
                return result
            except Exception as e:
                elapsed = time.time() - start_time
                _logger.error(f"{func.__name__} failed after {elapsed:.3f}s: {e}")
                raise
        
        return wrapper
    return decorator


def log_function_call(logger: Optional[logging.Logger] = None, level: int = logging.DEBUG):
    """
    装饰器：记录函数调用信息
    
    Args:
        logger: logger实例
        level: 日志级别
        
    Example:
        @log_function_call()
        def my_function(a, b):
            pass
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            _logger = logger or get_logger()
            
            # 记录调用信息
            args_str = ', '.join([repr(a) for a in args])
            kwargs_str = ', '.join([f"{k}={repr(v)}" for k, v in kwargs.items()])
            all_args = ', '.join(filter(None, [args_str, kwargs_str]))
            
            _logger.log(level, f"Calling {func.__name__}({all_args})")
            
            try:
                result = func(*args, **kwargs)
                _logger.log(level, f"{func.__name__} returned: {repr(result)[:100]}")
                return result
            except Exception as e:
                _logger.error(f"{func.__name__} raised {type(e).__name__}: {e}")
                raise
        
        return wrapper
    return decorator


# 默认logger实例
_default_logger: Optional[logging.Logger] = None


def get_default_logger() -> logging.Logger:
    """获取默认logger实例"""
    global _default_logger
    if _default_logger is None:
        _default_logger = get_logger("tradingagents")
    return _default_logger
