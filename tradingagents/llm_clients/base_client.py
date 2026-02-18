from abc import ABC, abstractmethod
from typing import Any, Optional


class BaseLLMClient(ABC):
    """Abstract base class for LLM clients.
    
    所有LLM客户端的基类，定义了通用接口
    """

    def __init__(self, model: str, base_url: Optional[str] = None, **kwargs):
        """初始化LLM客户端
        
        Args:
            model: 模型名称
            base_url: 可选的API基础URL
            **kwargs: 其他提供商特定的参数
        """
        self.model = model
        self.base_url = base_url
        self.kwargs = kwargs

    @abstractmethod
    def get_llm(self) -> Any:
        """返回配置好的LLM实例
        
        Returns:
            配置好的LLM实例
        """
        pass

    @abstractmethod
    def validate_model(self) -> bool:
        """验证模型是否被此客户端支持
        
        Returns:
            如果模型支持返回True，否则返回False
        """
        pass
