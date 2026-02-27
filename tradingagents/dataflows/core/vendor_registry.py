#!/usr/bin/env python3
"""
Vendor注册管理器
负责数据供应商的注册、配置和管理
"""

from typing import Dict, List, Optional
from enum import Enum
from dataclasses import dataclass


class VendorPriority(Enum):
    """Vendor优先级"""
    HIGH = 1
    MEDIUM = 2
    LOW = 3


@dataclass
class VendorConfig:
    """Vendor配置"""
    name: str
    enabled: bool = True
    priority: VendorPriority = VendorPriority.MEDIUM
    timeout_seconds: int = 30
    max_retries: int = 3
    retry_delay_seconds: int = 2


class VendorRegistry:
    """Vendor注册管理器"""
    
    def __init__(self):
        """初始化注册表"""
        self._vendors: Dict[str, VendorConfig] = {}
        self._method_vendors: Dict[str, List[str]] = {}
    
    def register_vendor(self, config: VendorConfig) -> 'VendorRegistry':
        """
        注册Vendor
        
        Args:
            config: Vendor配置
            
        Returns:
            self（链式调用）
        """
        self._vendors[config.name] = config
        return self
    
    def unregister_vendor(self, name: str):
        """取消注册Vendor"""
        if name in self._vendors:
            del self._vendors[name]
    
    def get_vendor_config(self, name: str) -> Optional[VendorConfig]:
        """获取Vendor配置"""
        return self._vendors.get(name)
    
    def list_vendors(self, enabled_only: bool = True) -> List[str]:
        """
        列出所有Vendor
        
        Args:
            enabled_only: 只返回启用的Vendor
            
        Returns:
            Vendor名称列表
        """
        if enabled_only:
            return [
                name for name, config in self._vendors.items()
                if config.enabled
            ]
        return list(self._vendors.keys())
    
    def register_method(
        self,
        method_name: str,
        vendor_names: List[str]
    ) -> 'VendorRegistry':
        """
        为方法注册可用的Vendor列表
        
        Args:
            method_name: 方法名称
            vendor_names: Vendor名称列表（按优先级排序）
            
        Returns:
            self（链式调用）
        """
        self._method_vendors[method_name] = vendor_names
        return self
    
    def get_method_vendors(
        self,
        method_name: str,
        enabled_only: bool = True
    ) -> List[str]:
        """
        获取方法的Vendor列表（按优先级排序）
        
        Args:
            method_name: 方法名称
            enabled_only: 只返回启用的Vendor
            
        Returns:
            Vendor名称列表
        """
        vendors = self._method_vendors.get(method_name, [])
        
        if enabled_only:
            vendors = [
                v for v in vendors
                if self._vendors.get(v, VendorConfig(name=v)).enabled
            ]
        
        # 按优先级排序
        vendors.sort(
            key=lambda v: self._vendors.get(v, VendorConfig(name=v)).priority.value
        )
        
        return vendors
    
    def enable_vendor(self, name: str):
        """启用Vendor"""
        if name in self._vendors:
            self._vendors[name].enabled = True
    
    def disable_vendor(self, name: str):
        """禁用Vendor"""
        if name in self._vendors:
            self._vendors[name].enabled = False
    
    def set_vendor_priority(self, name: str, priority: VendorPriority):
        """设置Vendor优先级"""
        if name in self._vendors:
            self._vendors[name].priority = priority


# 全局注册表实例
_registry = VendorRegistry()


def get_vendor_registry() -> VendorRegistry:
    """获取全局Vendor注册表"""
    return _registry
