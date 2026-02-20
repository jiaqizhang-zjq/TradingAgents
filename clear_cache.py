#!/usr/bin/env python3
"""清除所有数据缓存"""

from tradingagents.dataflows.data_cache import get_data_cache

def main():
    cache = get_data_cache()
    print("缓存统计信息:")
    print(cache.get_stats())
    
    print("\n正在清除所有缓存...")
    cache.clear()
    
    print("\n清除完成！新的缓存统计:")
    print(cache.get_stats())

if __name__ == "__main__":
    main()
