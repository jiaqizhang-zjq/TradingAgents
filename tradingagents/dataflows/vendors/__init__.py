#!/usr/bin/env python3
"""
数据供应商（Vendors）模块

包含各个数据源的客户端实现：
- longbridge_client: 长桥API客户端
"""

from .longbridge_client import LongbridgeClient

__all__ = ["LongbridgeClient"]
