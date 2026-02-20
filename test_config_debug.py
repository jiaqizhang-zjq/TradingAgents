#!/usr/bin/env python3
"""
测试配置加载和调试信息
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tradingagents.dataflows.config import get_config


def test_config_loading():
    """测试配置加载"""
    print("=" * 80)
    print("Testing Config Loading...")
    print("=" * 80)
    
    config = get_config()
    print(f"Current config: {config}")
    print(f"Output language: {config.get('output_language')}")
    print(f"LLM provider: {config.get('llm_provider')}")
    print(f"Deep think LLM: {config.get('deep_think_llm')}")
    print(f"Quick think LLM: {config.get('quick_think_llm')}")
    print(f"Backend URL: {config.get('backend_url')}")
    print(f"Data vendors: {config.get('data_vendors')}")
    
    print("=" * 80)
    print("Config loading test completed!")
    print("=" * 80)


if __name__ == "__main__":
    test_config_loading()
