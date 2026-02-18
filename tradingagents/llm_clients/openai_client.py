import os
from typing import Any, Optional

from langchain_openai import ChatOpenAI

from .base_client import BaseLLMClient
from .validators import validate_model


class UnifiedChatOpenAI(ChatOpenAI):
    """ChatOpenAI子类，处理某些模型的不兼容参数
    
    主要用于处理推理模型（如o1、o3、gpt-5系列），这些模型不支持temperature和top_p参数
    """

    def __init__(self, **kwargs):
        """初始化UnifiedChatOpenAI
        
        Args:
            **kwargs: 传递给ChatOpenAI的参数
        """
        model = kwargs.get("model", "")
        if self._is_reasoning_model(model):
            # 推理模型不支持temperature和top_p参数，移除它们
            kwargs.pop("temperature", None)
            kwargs.pop("top_p", None)
        super().__init__(**kwargs)

    @staticmethod
    def _is_reasoning_model(model: str) -> bool:
        """检查模型是否为不支持temperature的推理模型
        
        Args:
            model: 模型名称
            
        Returns:
            如果是推理模型返回True，否则返回False
        """
        model_lower = model.lower()
        return (
            model_lower.startswith("o1")  # OpenAI o1系列
            or model_lower.startswith("o3")  # OpenAI o3系列
            or "gpt-5" in model_lower  # GPT-5系列
        )


class OpenAIClient(BaseLLMClient):
    """OpenAI、Ollama、OpenRouter和xAI提供商的客户端
    
    统一处理多个兼容OpenAI API格式的提供商
    """

    def __init__(
        self,
        model: str,
        base_url: Optional[str] = None,
        provider: str = "openai",
        **kwargs,
    ):
        """初始化OpenAIClient
        
        Args:
            model: 模型名称
            base_url: 可选的API基础URL
            provider: 提供商名称 (openai, ollama, openrouter, xai)
            **kwargs: 额外的参数
        """
        super().__init__(model, base_url, **kwargs)
        self.provider = provider.lower()

    def get_llm(self) -> Any:
        """返回配置好的ChatOpenAI实例
        
        根据提供商设置不同的base_url和API密钥
        
        Returns:
            配置好的UnifiedChatOpenAI实例
        """
        llm_kwargs = {"model": self.model}

        # 根据不同提供商设置不同的base_url和API密钥
        if self.provider == "xai":
            llm_kwargs["base_url"] = "https://api.x.ai/v1"
            api_key = os.environ.get("XAI_API_KEY")
            if api_key:
                llm_kwargs["api_key"] = api_key
        elif self.provider == "openrouter":
            llm_kwargs["base_url"] = "https://openrouter.ai/api/v1"
            api_key = os.environ.get("OPENROUTER_API_KEY")
            if api_key:
                llm_kwargs["api_key"] = api_key
        elif self.provider == "ollama":
            llm_kwargs["base_url"] = "http://localhost:11434/v1"
            llm_kwargs["api_key"] = "ollama"  # Ollama不需要认证
        elif self.base_url:
            llm_kwargs["base_url"] = self.base_url

        # 添加其他参数
        for key in ("timeout", "max_retries", "reasoning_effort", "api_key", "callbacks"):
            if key in self.kwargs:
                llm_kwargs[key] = self.kwargs[key]

        return UnifiedChatOpenAI(**llm_kwargs)

    def validate_model(self) -> bool:
        """验证提供商的模型
        
        Args:
            
        Returns:
            如果模型有效返回True，否则返回False
        """
        return validate_model(self.provider, self.model)
