#!/usr/bin/env python3
"""
全局配置管理
使用Pydantic实现类型安全的配置管理，支持环境变量
"""

from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from typing import Optional, Literal
import os


class LLMConfig(BaseSettings):
    """LLM配置"""
    
    provider: Literal["openai", "anthropic", "azure", "local"] = Field(
        default="openai",
        description="LLM提供商"
    )
    
    model: str = Field(
        default="gpt-4",
        description="模型名称"
    )
    
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="生成温度"
    )
    
    max_tokens: int = Field(
        default=2000,
        gt=0,
        description="最大token数"
    )
    
    timeout: int = Field(
        default=30,
        gt=0,
        description="超时时间(秒)"
    )
    
    class Config:
        env_prefix = "LLM_"


class APIConfig(BaseSettings):
    """API密钥配置"""
    
    openai_api_key: Optional[str] = Field(
        default=None,
        description="OpenAI API密钥"
    )
    
    anthropic_api_key: Optional[str] = Field(
        default=None,
        description="Anthropic API密钥"
    )
    
    alpha_vantage_key: Optional[str] = Field(
        default=None,
        description="Alpha Vantage API密钥"
    )
    
    finnhub_key: Optional[str] = Field(
        default=None,
        description="Finnhub API密钥"
    )
    
    longbridge_app_key: Optional[str] = Field(
        default=None,
        description="LongBridge APP Key"
    )
    
    longbridge_app_secret: Optional[str] = Field(
        default=None,
        description="LongBridge APP Secret"
    )
    
    longbridge_access_token: Optional[str] = Field(
        default=None,
        description="LongBridge Access Token"
    )
    
    class Config:
        env_prefix = ""


class DataConfig(BaseSettings):
    """数据获取配置"""
    
    default_vendor: Literal["yfinance", "alpha_vantage", "longbridge", "local"] = Field(
        default="yfinance",
        description="默认数据供应商"
    )
    
    cache_ttl_hours: int = Field(
        default=24,
        gt=0,
        description="缓存有效期(小时)"
    )
    
    max_cache_size: int = Field(
        default=1000,
        gt=0,
        description="最大缓存数量"
    )
    
    max_retry_attempts: int = Field(
        default=3,
        ge=1,
        description="最大重试次数"
    )
    
    retry_delay_seconds: int = Field(
        default=2,
        ge=0,
        description="重试延迟(秒)"
    )
    
    request_timeout: int = Field(
        default=30,
        gt=0,
        description="请求超时(秒)"
    )
    
    default_lookback_days: int = Field(
        default=120,
        gt=0,
        description="默认回看天数"
    )
    
    class Config:
        env_prefix = "DATA_"


class DebateConfig(BaseSettings):
    """辩论系统配置"""
    
    max_debate_rounds: int = Field(
        default=2,
        ge=1,
        le=10,
        description="最大投资辩论轮数"
    )
    
    max_risk_rounds: int = Field(
        default=2,
        ge=1,
        le=10,
        description="最大风险辩论轮数"
    )
    
    max_recur_limit: int = Field(
        default=100,
        gt=0,
        description="最大递归限制"
    )
    
    class Config:
        env_prefix = "DEBATE_"


class DatabaseConfig(BaseSettings):
    """数据库配置"""
    
    db_path: str = Field(
        default="tradingagents/db/research_tracker.db",
        description="数据库路径"
    )
    
    timeout: int = Field(
        default=30,
        gt=0,
        description="数据库超时(秒)"
    )
    
    class Config:
        env_prefix = "DB_"


class LogConfig(BaseSettings):
    """日志配置"""
    
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="日志级别"
    )
    
    log_dir: str = Field(
        default="logs",
        description="日志目录"
    )
    
    max_bytes: int = Field(
        default=10 * 1024 * 1024,  # 10MB
        gt=0,
        description="单个日志文件最大大小(字节)"
    )
    
    backup_count: int = Field(
        default=5,
        ge=0,
        description="日志备份数量"
    )
    
    class Config:
        env_prefix = "LOG_"


class TradingConfig(BaseSettings):
    """交易系统总配置"""
    
    # 子配置
    llm: LLMConfig = Field(default_factory=LLMConfig)
    api: APIConfig = Field(default_factory=APIConfig)
    data: DataConfig = Field(default_factory=DataConfig)
    debate: DebateConfig = Field(default_factory=DebateConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    log: LogConfig = Field(default_factory=LogConfig)
    
    # 全局配置
    language: Literal["zh", "en"] = Field(
        default="zh",
        description="系统语言"
    )
    
    debug: bool = Field(
        default=False,
        description="调试模式"
    )
    
    @field_validator('language')
    @classmethod
    def validate_language(cls, v: str) -> str:
        """验证语言代码"""
        if v not in ["zh", "en"]:
            raise ValueError(f"Unsupported language: {v}")
        return v
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_nested_delimiter = "__"
    
    @classmethod
    def from_env(cls) -> "TradingConfig":
        """从环境变量加载配置"""
        return cls()


# 全局配置实例
_config: Optional[TradingConfig] = None


def get_config() -> TradingConfig:
    """
    获取全局配置实例（单例）
    
    Returns:
        配置实例
    """
    global _config
    if _config is None:
        _config = TradingConfig.from_env()
    return _config


def reload_config() -> TradingConfig:
    """
    重新加载配置
    
    Returns:
        新的配置实例
    """
    global _config
    _config = TradingConfig.from_env()
    return _config


# 便捷访问
def get_llm_config() -> LLMConfig:
    """获取LLM配置"""
    return get_config().llm


def get_api_config() -> APIConfig:
    """获取API配置"""
    return get_config().api


def get_data_config() -> DataConfig:
    """获取数据配置"""
    return get_config().data


def get_debate_config() -> DebateConfig:
    """获取辩论配置"""
    return get_config().debate


def get_db_config() -> DatabaseConfig:
    """获取数据库配置"""
    return get_config().database


def get_log_config() -> LogConfig:
    """获取日志配置"""
    return get_config().log


if __name__ == "__main__":
    # 测试配置
    config = get_config()
    print(f"LLM Provider: {config.llm.provider}")
    print(f"Default Vendor: {config.data.default_vendor}")
    print(f"Max Debate Rounds: {config.debate.max_debate_rounds}")
    print(f"Language: {config.language}")
