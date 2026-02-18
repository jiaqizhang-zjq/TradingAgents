# TradingAgents/dataflows/data_cache.py
"""
数据缓存模块
避免重复API调用，提高性能
"""

import json
import hashlib
from datetime import datetime, timedelta
from typing import Any, Optional, Dict
from pathlib import Path
import os


class DataCache:
    """数据缓存类"""
    
    def __init__(self, cache_dir: Optional[str] = None, ttl_hours: int = 24):
        """
        初始化缓存
        
        Args:
            cache_dir: 缓存目录
            ttl_hours: 缓存有效期（小时）
        """
        if cache_dir is None:
            cache_dir = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "data_cache"
            )
        
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl = timedelta(hours=ttl_hours)
        
        # 内存缓存
        self.memory_cache: Dict[str, Dict[str, Any]] = {}
    
    def _get_cache_key(self, func_name: str, *args, **kwargs) -> str:
        """
        生成缓存键
        
        Args:
            func_name: 函数名
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            缓存键字符串
        """
        key_data = {
            "func": func_name,
            "args": args,
            "kwargs": sorted(kwargs.items())
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def _get_cache_file_path(self, cache_key: str) -> Path:
        """获取缓存文件路径"""
        return self.cache_dir / f"{cache_key}.json"
    
    def get(self, func_name: str, *args, **kwargs) -> Optional[Any]:
        """
        获取缓存数据
        
        Args:
            func_name: 函数名
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            缓存的数据，如果没有或已过期返回None
        """
        cache_key = self._get_cache_key(func_name, *args, **kwargs)
        
        # 先查内存缓存
        if cache_key in self.memory_cache:
            cache_data = self.memory_cache[cache_key]
            cached_at = datetime.fromisoformat(cache_data["cached_at"])
            
            if datetime.now() - cached_at < self.ttl:
                return cache_data["data"]
            else:
                del self.memory_cache[cache_key]
        
        # 再查文件缓存
        cache_file = self._get_cache_file_path(cache_key)
        
        if cache_file.exists():
            try:
                with open(cache_file, "r") as f:
                    cache_data = json.load(f)
                
                cached_at = datetime.fromisoformat(cache_data["cached_at"])
                
                if datetime.now() - cached_at < self.ttl:
                    # 同步到内存缓存
                    self.memory_cache[cache_key] = cache_data
                    return cache_data["data"]
                else:
                    cache_file.unlink()
            except Exception:
                pass
        
        return None
    
    def set(self, func_name: str, data: Any, *args, **kwargs) -> None:
        """
        设置缓存数据
        
        Args:
            func_name: 函数名
            data: 要缓存的数据
            *args: 位置参数
            **kwargs: 关键字参数
        """
        cache_key = self._get_cache_key(func_name, *args, **kwargs)
        
        cache_data = {
            "data": data,
            "cached_at": datetime.now().isoformat(),
            "func_name": func_name
        }
        
        # 存储到内存缓存
        self.memory_cache[cache_key] = cache_data
        
        # 存储到文件缓存
        cache_file = self._get_cache_file_path(cache_key)
        
        try:
            with open(cache_file, "w") as f:
                json.dump(cache_data, f, indent=2)
        except Exception:
            pass
    
    def clear(self, func_name: Optional[str] = None) -> None:
        """
        清除缓存
        
        Args:
            func_name: 函数名，如果为None则清除所有缓存
        """
        if func_name:
            # 清除特定函数的缓存
            keys_to_delete = [
                key for key, data in self.memory_cache.items()
                if data["func_name"] == func_name
            ]
            
            for key in keys_to_delete:
                del self.memory_cache[key]
            
            # 清除文件缓存
            for cache_file in self.cache_dir.glob("*.json"):
                try:
                    with open(cache_file, "r") as f:
                        cache_data = json.load(f)
                    
                    if cache_data.get("func_name") == func_name:
                        cache_file.unlink()
                except Exception:
                    pass
        else:
            # 清除所有缓存
            self.memory_cache.clear()
            
            for cache_file in self.cache_dir.glob("*.json"):
                try:
                    cache_file.unlink()
                except Exception:
                    pass
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        memory_count = len(self.memory_cache)
        file_count = len(list(self.cache_dir.glob("*.json")))
        
        return {
            "memory_cache_count": memory_count,
            "file_cache_count": file_count,
            "cache_dir": str(self.cache_dir),
            "ttl_hours": self.ttl.total_seconds() / 3600
        }


# 全局缓存实例
_cache: Optional[DataCache] = None


def get_data_cache() -> DataCache:
    """获取数据缓存实例（单例）"""
    global _cache
    if _cache is None:
        _cache = DataCache()
    return _cache


def cached(func):
    """
    缓存装饰器
    
    使用示例:
        @cached
        def my_function(arg1, arg2):
            # 实现
            return result
    """
    def wrapper(*args, **kwargs):
        cache = get_data_cache()
        
        # 尝试获取缓存
        cached_result = cache.get(func.__name__, *args, **kwargs)
        if cached_result is not None:
            return cached_result
        
        # 执行函数
        result = func(*args, **kwargs)
        
        # 存储缓存
        cache.set(func.__name__, result, *args, **kwargs)
        
        return result
    
    return wrapper
