"""
Agent工厂模式 - 统一Agent创建逻辑
"""

from typing import Dict, Any, Optional, Callable
from abc import ABC, abstractmethod


class BaseAgent(ABC):
    """Agent基础接口"""
    
    @abstractmethod
    def create_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        创建Agent节点
        
        Args:
            state: 当前状态
            
        Returns:
            更新后的状态
        """
        pass


class AgentFactory:
    """
    Agent工厂类
    
    提供统一的Agent创建接口，支持动态注册和扩展
    """
    
    def __init__(self):
        """初始化工厂"""
        self._creators: Dict[str, Callable] = {}
        self._register_builtin_agents()
    
    def _register_builtin_agents(self) -> None:
        """注册内置的Agent创建器（从 RESEARCHER_REGISTRY 动态加载）"""
        import importlib
        from tradingagents.constants import RESEARCHER_REGISTRY

        for key, info in RESEARCHER_REGISTRY.items():
            module = importlib.import_module(info["module"])
            factory_fn = getattr(module, info["factory"])
            self._creators[key] = factory_fn
    
    def register(self, agent_type: str, creator: Callable) -> None:
        """
        注册新的Agent创建器
        
        Args:
            agent_type: Agent类型标识
            creator: Agent创建函数
        """
        self._creators[agent_type] = creator
    
    def create(self, agent_type: str, llm: Any, memory: Any, **kwargs) -> Callable:
        """
        创建Agent
        
        Args:
            agent_type: Agent类型 ("bull", "bear", "market", "trader"等)
            llm: LLM客户端
            memory: 记忆存储
            **kwargs: 其他参数
            
        Returns:
            Agent创建函数
            
        Raises:
            ValueError: 如果agent_type未注册
        
        Example:
            >>> factory = AgentFactory()
            >>> bull_agent = factory.create("bull", llm, memory)
        """
        if agent_type not in self._creators:
            raise ValueError(
                f"Unknown agent type: {agent_type}. "
                f"Available types: {', '.join(self._creators.keys())}"
            )
        
        creator = self._creators[agent_type]
        return creator(llm, memory, **kwargs)
    
    def list_available_agents(self) -> list[str]:
        """
        列出所有可用的Agent类型
        
        Returns:
            Agent类型列表
        """
        return list(self._creators.keys())
    
    def has_agent(self, agent_type: str) -> bool:
        """
        检查是否注册了指定类型的Agent
        
        Args:
            agent_type: Agent类型
            
        Returns:
            是否已注册
        """
        return agent_type in self._creators


# 全局工厂实例（单例模式）
_factory_instance: Optional[AgentFactory] = None


def get_agent_factory() -> AgentFactory:
    """
    获取全局Agent工厂实例
    
    Returns:
        AgentFactory实例
    """
    global _factory_instance
    if _factory_instance is None:
        _factory_instance = AgentFactory()
    return _factory_instance


def create_agent(agent_type: str, llm: Any, memory: Any, **kwargs) -> Callable:
    """
    快捷创建Agent的函数
    
    Args:
        agent_type: Agent类型
        llm: LLM客户端
        memory: 记忆存储
        **kwargs: 其他参数
        
    Returns:
        Agent创建函数
    
    Example:
        >>> from tradingagents.agents.factory import create_agent
        >>> bull_agent = create_agent("bull", llm, memory)
    """
    factory = get_agent_factory()
    return factory.create(agent_type, llm, memory, **kwargs)
