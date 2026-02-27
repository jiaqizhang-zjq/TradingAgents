#!/usr/bin/env python3
"""
数据流核心模块
提供Vendor管理、重试策略、统计收集等基础功能
"""

from .vendor_registry import (
    VendorRegistry,
    VendorConfig,
    VendorPriority,
    get_vendor_registry
)

from .retry_policy import (
    RetryPolicy,
    retry_on_failure,
    get_default_retry_policy
)

from .statistics_collector import (
    StatisticsCollector,
    FetchStatistics,
    get_statistics_collector
)

__all__ = [
    # Vendor管理
    'VendorRegistry',
    'VendorConfig',
    'VendorPriority',
    'get_vendor_registry',
    
    # 重试策略
    'RetryPolicy',
    'retry_on_failure',
    'get_default_retry_policy',
    
    # 统计收集
    'StatisticsCollector',
    'FetchStatistics',
    'get_statistics_collector',
]
