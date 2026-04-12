"""
性能监控装饰器模块
提供详细的性能追踪和统计功能
"""
import time
import functools
from typing import Dict, List, Any, Callable, Optional
from dataclasses import dataclass, field
from datetime import datetime
import threading

from tradingagents.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class PerformanceMetric:
    """性能指标"""
    function_name: str
    call_count: int = 0
    total_time: float = 0.0
    min_time: float = float('inf')
    max_time: float = 0.0
    avg_time: float = 0.0
    last_call_time: Optional[datetime] = None
    errors: int = 0


class PerformanceMonitor:
    """性能监控器（单例）"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.metrics: Dict[str, PerformanceMetric] = {}
        self.detailed_logs: List[Dict[str, Any]] = []
        self.max_logs = 1000  # 最多保留1000条详细日志
        self._initialized = True
    
    def record(
        self,
        function_name: str,
        duration: float,
        success: bool = True,
        args: tuple = (),
        kwargs: dict = None,
        result: Any = None,
        error: Optional[Exception] = None
    ):
        """
        记录函数调用性能
        
        Args:
            function_name: 函数名称
            duration: 执行时间（秒）
            success: 是否成功
            args: 位置参数
            kwargs: 关键字参数
            result: 返回结果
            error: 异常对象
        """
        # 更新汇总指标
        if function_name not in self.metrics:
            self.metrics[function_name] = PerformanceMetric(function_name=function_name)
        
        metric = self.metrics[function_name]
        metric.call_count += 1
        metric.total_time += duration
        metric.min_time = min(metric.min_time, duration)
        metric.max_time = max(metric.max_time, duration)
        metric.avg_time = metric.total_time / metric.call_count
        metric.last_call_time = datetime.now()
        
        if not success:
            metric.errors += 1
        
        # 记录详细日志
        log_entry = {
            "function": function_name,
            "timestamp": datetime.now().isoformat(),
            "duration_ms": duration * 1000,
            "success": success,
            "args_count": len(args),
            "kwargs_count": len(kwargs or {}),
            "error": str(error) if error else None
        }
        
        self.detailed_logs.append(log_entry)
        
        # 限制详细日志大小
        if len(self.detailed_logs) > self.max_logs:
            self.detailed_logs = self.detailed_logs[-self.max_logs:]
    
    def get_summary(self) -> Dict[str, Any]:
        """
        获取性能摘要
        
        Returns:
            性能摘要字典
        """
        return {
            "total_functions": len(self.metrics),
            "total_calls": sum(m.call_count for m in self.metrics.values()),
            "total_time": sum(m.total_time for m in self.metrics.values()),
            "total_errors": sum(m.errors for m in self.metrics.values()),
            "functions": {
                name: {
                    "calls": m.call_count,
                    "total_time": f"{m.total_time:.3f}s",
                    "avg_time": f"{m.avg_time * 1000:.2f}ms",
                    "min_time": f"{m.min_time * 1000:.2f}ms",
                    "max_time": f"{m.max_time * 1000:.2f}ms",
                    "errors": m.errors,
                    "last_call": m.last_call_time.isoformat() if m.last_call_time else None
                }
                for name, m in sorted(
                    self.metrics.items(),
                    key=lambda x: x[1].total_time,
                    reverse=True
                )
            }
        }
    
    def get_slowest_calls(self, n: int = 10) -> List[Dict[str, Any]]:
        """
        获取最慢的N次调用
        
        Args:
            n: 返回数量
        
        Returns:
            最慢调用列表
        """
        sorted_logs = sorted(
            self.detailed_logs,
            key=lambda x: x["duration_ms"],
            reverse=True
        )
        return sorted_logs[:n]
    
    def get_recent_errors(self, n: int = 10) -> List[Dict[str, Any]]:
        """
        获取最近的错误
        
        Args:
            n: 返回数量
        
        Returns:
            最近错误列表
        """
        error_logs = [log for log in self.detailed_logs if not log["success"]]
        return error_logs[-n:]
    
    def reset(self):
        """重置所有统计数据"""
        self.metrics.clear()
        self.detailed_logs.clear()
    
    def print_report(self, top_n: int = 10):
        """
        打印性能报告
        
        Args:
            top_n: 显示前N个最慢的函数
        """
        summary = self.get_summary()
        
        logger.info("=" * 80)
        logger.info("性能监控报告")
        logger.info("=" * 80)
        logger.info("监控函数数: %d", summary['total_functions'])
        logger.info("总调用次数: %d", summary['total_calls'])
        logger.info("总执行时间: %.2fs", summary['total_time'])
        logger.info("总错误数: %d", summary['total_errors'])
        
        logger.info("-" * 80)
        logger.info("前%d个最耗时的函数:", top_n)
        logger.info("-" * 80)
        logger.info("%-40s %-10s %-15s %-10s", "函数名", "调用次数", "平均时间", "总时间")
        logger.info("-" * 80)
        
        for i, (name, data) in enumerate(list(summary['functions'].items())[:top_n], 1):
            logger.info("%-40s %-10s %-15s %-10s", name, data['calls'], data['avg_time'], data['total_time'])
        
        # 显示最慢的调用
        slowest = self.get_slowest_calls(5)
        if slowest:
            logger.info("-" * 80)
            logger.info("最慢的5次调用:")
            logger.info("-" * 80)
            for i, log in enumerate(slowest, 1):
                logger.info("%d. %s: %.2fms (%s)", i, log['function'], log['duration_ms'], log['timestamp'])
        
        # 显示最近的错误
        errors = self.get_recent_errors(5)
        if errors:
            logger.info("-" * 80)
            logger.info("最近的5个错误:")
            logger.info("-" * 80)
            for i, log in enumerate(errors, 1):
                logger.info("%d. %s: %s (%s)", i, log['function'], log['error'], log['timestamp'])
        
        logger.info("=" * 80)


# 全局监控器实例
_monitor = PerformanceMonitor()


def track_performance(func_type: Optional[str] = None) -> Callable:
    """
    性能追踪装饰器
    
    Args:
        func_type: 函数类型标签（可选，用于分类）
    
    Returns:
        装饰器函数
    
    Example:
        @track_performance("llm_call")
        def call_llm(prompt):
            ...
        
        @track_performance()
        def fetch_data(symbol):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            func_name = f"{func_type}.{func.__name__}" if func_type else func.__name__
            start_time = time.time()
            error = None
            result = None
            success = True
            
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                error = e
                raise
            finally:
                duration = time.time() - start_time
                _monitor.record(
                    function_name=func_name,
                    duration=duration,
                    success=success,
                    args=args,
                    kwargs=kwargs,
                    result=result,
                    error=error
                )
        
        return wrapper
    
    return decorator


def get_monitor() -> PerformanceMonitor:
    """获取全局性能监控器实例"""
    return _monitor


def print_performance_report(top_n: int = 10):
    """
    打印性能报告（便捷函数）
    
    Args:
        top_n: 显示前N个最慢的函数
    """
    _monitor.print_report(top_n)


def reset_performance_stats():
    """重置性能统计（便捷函数）"""
    _monitor.reset()
