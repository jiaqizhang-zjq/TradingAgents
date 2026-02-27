#!/usr/bin/env python3
"""
核心模块
提供依赖注入等基础架构功能
"""

from .container import (
    DependencyContainer,
    get_container,
    register_service,
    get_service,
    has_service
)

__all__ = [
    'DependencyContainer',
    'get_container',
    'register_service',
    'get_service',
    'has_service',
]
