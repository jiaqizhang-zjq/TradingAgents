# TradingAgents/dataflows/api_config.py
"""
统一API配置管理
集中管理所有API密钥和配置
"""

import os
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class APIConfig:
    """API配置数据类"""
    # LLM Providers
    openai_api_key: Optional[str] = None
    google_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    xai_api_key: Optional[str] = None
    openrouter_api_key: Optional[str] = None
    
    # Data Providers
    alpha_vantage_api_key: Optional[str] = None
    
    # Longbridge
    longbridge_app_key: Optional[str] = None
    longbridge_app_secret: Optional[str] = None
    longbridge_access_token: Optional[str] = None
    
    # Social Media
    reddit_client_id: Optional[str] = None
    reddit_client_secret: Optional[str] = None
    reddit_user_agent: Optional[str] = None
    twitter_bearer_token: Optional[str] = None


# 全局配置实例
_config: Optional[APIConfig] = None


def get_api_config() -> APIConfig:
    """
    获取API配置（单例）
    
    Returns:
        APIConfig实例
    """
    global _config
    if _config is None:
        _config = load_config_from_env()
    return _config


def load_config_from_env() -> APIConfig:
    """
    从环境变量加载配置
    
    Returns:
        APIConfig实例
    """
    return APIConfig(
        # LLM Providers
        openai_api_key=os.environ.get("OPENAI_API_KEY"),
        google_api_key=os.environ.get("GOOGLE_API_KEY"),
        anthropic_api_key=os.environ.get("ANTHROPIC_API_KEY"),
        xai_api_key=os.environ.get("XAI_API_KEY"),
        openrouter_api_key=os.environ.get("OPENROUTER_API_KEY"),
        
        # Data Providers
        alpha_vantage_api_key=os.environ.get("ALPHA_VANTAGE_API_KEY"),
        
        # Longbridge
        longbridge_app_key=os.environ.get("LONGBRIDGE_APP_KEY"),
        longbridge_app_secret=os.environ.get("LONGBRIDGE_APP_SECRET"),
        longbridge_access_token=os.environ.get("LONGBRIDGE_ACCESS_TOKEN"),
        
        # Social Media
        reddit_client_id=os.environ.get("REDDIT_CLIENT_ID"),
        reddit_client_secret=os.environ.get("REDDIT_CLIENT_SECRET"),
        reddit_user_agent=os.environ.get("REDDIT_USER_AGENT", "TradingAgents/1.0"),
        twitter_bearer_token=os.environ.get("TWITTER_BEARER_TOKEN"),
    )


def reload_config() -> None:
    """重新加载配置"""
    global _config
    _config = None


def get_config_summary() -> Dict[str, bool]:
    """
    获取配置摘要（只显示是否已配置，不显示密钥）
    
    Returns:
        配置摘要字典
    """
    config = get_api_config()
    return {
        # LLM Providers
        "openai": bool(config.openai_api_key),
        "google": bool(config.google_api_key),
        "anthropic": bool(config.anthropic_api_key),
        "xai": bool(config.xai_api_key),
        "openrouter": bool(config.openrouter_api_key),
        
        # Data Providers
        "alpha_vantage": bool(config.alpha_vantage_api_key),
        
        # Longbridge
        "longbridge": all([
            config.longbridge_app_key,
            config.longbridge_app_secret,
            config.longbridge_access_token
        ]),
        
        # Social Media
        "reddit": all([
            config.reddit_client_id,
            config.reddit_client_secret
        ]),
        "twitter": bool(config.twitter_bearer_token),
    }


def print_config_summary() -> None:
    """打印配置摘要"""
    summary = get_config_summary()
    print("=" * 50)
    print("API 配置摘要")
    print("=" * 50)
    
    categories = [
        ("LLM 提供商", ["openai", "google", "anthropic", "xai", "openrouter"]),
        ("数据提供商", ["alpha_vantage", "longbridge"]),
        ("社交媒体", ["reddit", "twitter"]),
    ]
    
    for category, keys in categories:
        print(f"\n{category}:")
        for key in keys:
            status = "✅ 已配置" if summary[key] else "❌ 未配置"
            print(f"  - {key}: {status}")
    
    print("\n" + "=" * 50)


def check_required_config(required_keys: list) -> bool:
    """
    检查必需的配置是否存在
    
    Args:
        required_keys: 必需的配置键列表
        
    Returns:
        如果所有必需配置都存在返回True，否则返回False
    """
    summary = get_config_summary()
    missing = [key for key in required_keys if not summary.get(key, False)]
    
    if missing:
        print(f"错误: 缺少必需的配置: {', '.join(missing)}")
        return False
    
    return True
