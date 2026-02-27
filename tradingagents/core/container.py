#!/usr/bin/env python3
"""
依赖注入容器
提供简单的依赖注入和服务定位功能
"""

from typing import Any, Callable, Dict, Optional, TypeVar

T = TypeVar('T')


class DependencyContainer:
    """依赖注入容器"""
    
    def __init__(self):
        """初始化容器"""
        self._factories: Dict[str, Callable] = {}
        self._singletons: Dict[str, Any] = {}
        self._singleton_flags: Dict[str, bool] = {}
    
    def register(
        self,
        name: str,
        factory: Callable[[], T],
        singleton: bool = True
    ) -> 'DependencyContainer':
        """
        注册服务
        
        Args:
            name: 服务名称
            factory: 工厂函数，返回服务实例
            singleton: 是否单例模式
            
        Returns:
            self（链式调用）
            
        Examples:
            >>> container = DependencyContainer()
            >>> container.register('data_manager', lambda: DataManager(), singleton=True)
        """
        self._factories[name] = factory
        self._singleton_flags[name] = singleton
        return self
    
    def register_instance(self, name: str, instance: T) -> 'DependencyContainer':
        """
        注册实例（直接注册已创建的对象）
        
        Args:
            name: 服务名称
            instance: 服务实例
            
        Returns:
            self（链式调用）
        """
        self._singletons[name] = instance
        self._singleton_flags[name] = True
        return self
    
    def get(self, name: str) -> Any:
        """
        获取服务实例
        
        Args:
            name: 服务名称
            
        Returns:
            服务实例
            
        Raises:
            KeyError: 服务未注册
        """
        if name not in self._factories and name not in self._singletons:
            raise KeyError(f"Service '{name}' is not registered")
        
        # 如果是单例且已创建，直接返回
        if self._singleton_flags.get(name) and name in self._singletons:
            return self._singletons[name]
        
        # 如果直接注册了实例，返回实例
        if name in self._singletons:
            return self._singletons[name]
        
        # 调用工厂函数创建实例
        instance = self._factories[name]()
        
        # 如果是单例，缓存实例
        if self._singleton_flags.get(name):
            self._singletons[name] = instance
        
        return instance
    
    def has(self, name: str) -> bool:
        """
        检查服务是否已注册
        
        Args:
            name: 服务名称
            
        Returns:
            是否已注册
        """
        return name in self._factories or name in self._singletons
    
    def clear_singletons(self):
        """清除所有单例缓存"""
        self._singletons.clear()
    
    def unregister(self, name: str):
        """
        取消注册服务
        
        Args:
            name: 服务名称
        """
        if name in self._factories:
            del self._factories[name]
        if name in self._singletons:
            del self._singletons[name]
        if name in self._singleton_flags:
            del self._singleton_flags[name]


# 全局容器实例
_container = DependencyContainer()


def get_container() -> DependencyContainer:
    """获取全局依赖容器"""
    return _container


def register_service(
    name: str,
    factory: Callable[[], T],
    singleton: bool = True
) -> DependencyContainer:
    """
    注册服务（便捷函数）
    
    Args:
        name: 服务名称
        factory: 工厂函数
        singleton: 是否单例
        
    Returns:
        全局容器
    """
    return _container.register(name, factory, singleton)


def get_service(name: str) -> Any:
    """
    获取服务（便捷函数）
    
    Args:
        name: 服务名称
        
    Returns:
        服务实例
    """
    return _container.get(name)


def has_service(name: str) -> bool:
    """
    检查服务是否存在（便捷函数）
    
    Args:
        name: 服务名称
        
    Returns:
        是否存在
    """
    return _container.has(name)
