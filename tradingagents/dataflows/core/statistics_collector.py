#!/usr/bin/env python3
"""
统计收集器
收集数据获取的统计信息
"""

from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class FetchStatistics:
    """数据获取统计"""
    vendor: str
    method: str
    success_count: int = 0
    failure_count: int = 0
    total_time_seconds: float = 0.0
    last_success_time: Optional[datetime] = None
    last_failure_time: Optional[datetime] = None
    last_error: Optional[str] = None
    
    @property
    def total_count(self) -> int:
        """总请求次数"""
        return self.success_count + self.failure_count
    
    @property
    def success_rate(self) -> float:
        """成功率"""
        if self.total_count == 0:
            return 0.0
        return self.success_count / self.total_count
    
    @property
    def average_time_seconds(self) -> float:
        """平均响应时间"""
        if self.success_count == 0:
            return 0.0
        return self.total_time_seconds / self.success_count


class StatisticsCollector:
    """统计收集器"""
    
    def __init__(self):
        """初始化统计收集器"""
        self._stats: Dict[str, FetchStatistics] = {}
    
    def _get_key(self, vendor: str, method: str) -> str:
        """生成统计key"""
        return f"{vendor}::{method}"
    
    def record_success(
        self,
        vendor: str,
        method: str,
        elapsed_seconds: float
    ):
        """
        记录成功的请求
        
        Args:
            vendor: 数据供应商名称
            method: 方法名称
            elapsed_seconds: 耗时（秒）
        """
        key = self._get_key(vendor, method)
        
        if key not in self._stats:
            self._stats[key] = FetchStatistics(vendor=vendor, method=method)
        
        stats = self._stats[key]
        stats.success_count += 1
        stats.total_time_seconds += elapsed_seconds
        stats.last_success_time = datetime.now()
    
    def record_failure(
        self,
        vendor: str,
        method: str,
        error_message: str
    ):
        """
        记录失败的请求
        
        Args:
            vendor: 数据供应商名称
            method: 方法名称
            error_message: 错误信息
        """
        key = self._get_key(vendor, method)
        
        if key not in self._stats:
            self._stats[key] = FetchStatistics(vendor=vendor, method=method)
        
        stats = self._stats[key]
        stats.failure_count += 1
        stats.last_failure_time = datetime.now()
        stats.last_error = error_message
    
    def get_statistics(
        self,
        vendor: Optional[str] = None,
        method: Optional[str] = None
    ) -> List[FetchStatistics]:
        """
        获取统计信息
        
        Args:
            vendor: 可选，只返回指定vendor的统计
            method: 可选，只返回指定method的统计
            
        Returns:
            统计信息列表
        """
        results = []
        
        for stats in self._stats.values():
            if vendor and stats.vendor != vendor:
                continue
            if method and stats.method != method:
                continue
            results.append(stats)
        
        return results
    
    def get_vendor_statistics(self, vendor: str) -> List[FetchStatistics]:
        """获取指定vendor的所有统计"""
        return self.get_statistics(vendor=vendor)
    
    def get_method_statistics(self, method: str) -> List[FetchStatistics]:
        """获取指定method的所有统计"""
        return self.get_statistics(method=method)
    
    def clear_statistics(self, vendor: Optional[str] = None):
        """
        清除统计信息
        
        Args:
            vendor: 可选，只清除指定vendor的统计
        """
        if vendor:
            keys_to_remove = [
                key for key, stats in self._stats.items()
                if stats.vendor == vendor
            ]
            for key in keys_to_remove:
                del self._stats[key]
        else:
            self._stats.clear()
    
    def print_summary(self):
        """打印统计摘要"""
        print("\n========== Data Fetch Statistics ==========")
        
        for stats in self._stats.values():
            print(f"\n{stats.vendor}::{stats.method}")
            print(f"  Total: {stats.total_count}")
            print(f"  Success: {stats.success_count} ({stats.success_rate:.1%})")
            print(f"  Failure: {stats.failure_count}")
            print(f"  Avg Time: {stats.average_time_seconds:.3f}s")
            
            if stats.last_error:
                print(f"  Last Error: {stats.last_error}")
        
        print("\n" + "=" * 44)


# 全局统计收集器实例
_collector = StatisticsCollector()


def get_statistics_collector() -> StatisticsCollector:
    """获取全局统计收集器"""
    return _collector
