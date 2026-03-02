"""
错误检测器模块
负责识别不同类型的错误（限流、网络等）
"""
from typing import Any


class ErrorDetector:
    """错误检测器"""
    
    @staticmethod
    def is_rate_limit_error(error: Exception) -> bool:
        """
        判断是否是限流错误
        
        Args:
            error: 异常对象
        
        Returns:
            是否是限流错误
        """
        error_str = str(error).lower()
        
        rate_limit_keywords = [
            "rate limit", "ratelimit", "too many requests",
            "429", "quota", "exceeded", "throttle"
        ]
        
        for keyword in rate_limit_keywords:
            if keyword in error_str:
                return True
        
        # 检查特定异常类型
        try:
            from tradingagents.dataflows.alpha_vantage_common import AlphaVantageRateLimitError
            if isinstance(error, AlphaVantageRateLimitError):
                return True
        except ImportError:
            pass
        
        # 检查RateLimitError
        error_class_name = error.__class__.__name__
        if 'RateLimit' in error_class_name:
            return True
        
        return False
    
    @staticmethod
    def is_network_error(error: Exception) -> bool:
        """
        判断是否是网络错误
        
        Args:
            error: 异常对象
        
        Returns:
            是否是网络错误
        """
        error_str = str(error).lower()
        
        network_keywords = [
            "connection", "timeout", "network", "socket",
            "unreachable", "refused", "reset"
        ]
        
        for keyword in network_keywords:
            if keyword in error_str:
                return True
        
        return False
    
    @staticmethod
    def classify_error(error: Exception) -> str:
        """
        分类错误类型
        
        Args:
            error: 异常对象
        
        Returns:
            错误类型字符串
        """
        if ErrorDetector.is_rate_limit_error(error):
            return "rate_limit"
        elif ErrorDetector.is_network_error(error):
            return "network"
        else:
            return "unknown"
