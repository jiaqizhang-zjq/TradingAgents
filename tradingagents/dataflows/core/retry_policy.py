#!/usr/bin/env python3
"""
重试策略
提供统一的重试逻辑
"""

import time
from functools import wraps
from typing import Callable, TypeVar, Any, Optional
from tradingagents.constants import MAX_RETRY_ATTEMPTS, RETRY_DELAY_SECONDS
from tradingagents.exceptions import DataFetchError
from tradingagents.utils.logger import get_logger

logger = get_logger(__name__)

T = TypeVar('T')


class RetryPolicy:
    """重试策略"""
    
    def __init__(
        self,
        max_attempts: int = MAX_RETRY_ATTEMPTS,
        delay_seconds: int = RETRY_DELAY_SECONDS,
        backoff_multiplier: float = 2.0
    ):
        """
        初始化重试策略
        
        Args:
            max_attempts: 最大重试次数
            delay_seconds: 初始延迟秒数
            backoff_multiplier: 退避乘数（每次重试延迟翻倍）
        """
        self.max_attempts = max_attempts
        self.delay_seconds = delay_seconds
        self.backoff_multiplier = backoff_multiplier
    
    def execute(
        self,
        func: Callable[..., T],
        *args,
        **kwargs
    ) -> T:
        """
        执行函数，失败时重试
        
        Args:
            func: 要执行的函数
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            函数执行结果
            
        Raises:
            最后一次执行的异常
        """
        last_exception = None
        current_delay = self.delay_seconds
        
        for attempt in range(1, self.max_attempts + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                
                if attempt < self.max_attempts:
                    logger.warning("⚠️ Attempt %d/%d failed: %s", attempt, self.max_attempts, e)
                    logger.info("⏳ Retrying in %ss...", current_delay)
                    time.sleep(current_delay)
                    current_delay *= self.backoff_multiplier
                else:
                    logger.error("❌ All %d attempts failed", self.max_attempts)
        
        raise last_exception
    
    def with_decorator(self) -> Callable:
        """
        返回装饰器函数
        
        Returns:
            重试装饰器
        """
        def decorator(func: Callable[..., T]) -> Callable[..., T]:
            @wraps(func)
            def wrapper(*args, **kwargs) -> T:
                return self.execute(func, *args, **kwargs)
            return wrapper
        return decorator


def retry_on_failure(
    max_attempts: int = MAX_RETRY_ATTEMPTS,
    delay_seconds: int = RETRY_DELAY_SECONDS,
    backoff_multiplier: float = 2.0
):
    """
    重试装饰器（便捷函数）
    
    Args:
        max_attempts: 最大重试次数
        delay_seconds: 初始延迟秒数
        backoff_multiplier: 退避乘数
        
    Returns:
        装饰器函数
        
    Examples:
        >>> @retry_on_failure(max_attempts=3, delay_seconds=1)
        >>> def fetch_data():
        >>>     return api.get_data()
    """
    policy = RetryPolicy(max_attempts, delay_seconds, backoff_multiplier)
    return policy.with_decorator()


# 默认重试策略实例
_default_policy = RetryPolicy()


def get_default_retry_policy() -> RetryPolicy:
    """获取默认重试策略"""
    return _default_policy
