from typing import Optional

from .base_client import BaseLLMClient
from .openai_client import OpenAIClient
from .anthropic_client import AnthropicClient
from .google_client import GoogleClient


def create_llm_client(
    provider: str,
    model: str,
    base_url: Optional[str] = None,
    **kwargs,
) -> BaseLLMClient:
    """创建指定提供商的LLM客户端
    
    工厂函数，根据提供商类型创建对应的LLM客户端实例

    Args:
        provider: LLM提供商 (openai, anthropic, google, xai, ollama, openrouter)
        model: 模型名称/标识符
        base_url: API端点的可选基础URL
        **kwargs: 额外的提供商特定参数

    Returns:
        配置好的BaseLLMClient实例

    Raises:
        ValueError: 如果提供商不支持
    """
    provider_lower = provider.lower()

    # OpenAI、Ollama和OpenRouter使用相同的客户端实现
    if provider_lower in ("openai", "ollama", "openrouter"):
        return OpenAIClient(model, base_url, provider=provider_lower, **kwargs)

    # xAI也使用OpenAI客户端实现
    if provider_lower == "xai":
        return OpenAIClient(model, base_url, provider="xai", **kwargs)

    # Anthropic使用专门的客户端实现
    if provider_lower == "anthropic":
        return AnthropicClient(model, base_url, **kwargs)

    # Google使用专门的客户端实现
    if provider_lower == "google":
        return GoogleClient(model, base_url, **kwargs)

    # 不支持的提供商
    raise ValueError(f"Unsupported LLM provider: {provider}")
