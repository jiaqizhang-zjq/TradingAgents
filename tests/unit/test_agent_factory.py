"""
测试Agent工厂模式
"""

import pytest
from tradingagents.agents.factory import (
    AgentFactory,
    get_agent_factory,
    create_agent
)


class TestAgentFactory:
    """测试AgentFactory类"""
    
    def test_initialization(self):
        """测试工厂初始化"""
        factory = AgentFactory()
        assert factory is not None
        assert len(factory.list_available_agents()) > 0
    
    def test_builtin_agents_registered(self):
        """测试内置Agent已注册"""
        factory = AgentFactory()
        
        # 验证Bull和Bear Researcher已注册
        assert factory.has_agent("bull")
        assert factory.has_agent("bear")
    
    def test_list_available_agents(self):
        """测试列出可用Agent"""
        factory = AgentFactory()
        agents = factory.list_available_agents()
        
        assert isinstance(agents, list)
        assert "bull" in agents
        assert "bear" in agents
    
    def test_has_agent(self):
        """测试检查Agent是否存在"""
        factory = AgentFactory()
        
        assert factory.has_agent("bull") is True
        assert factory.has_agent("bear") is True
        assert factory.has_agent("nonexistent") is False
    
    def test_create_unknown_agent_raises_error(self):
        """测试创建未知Agent抛出异常"""
        factory = AgentFactory()
        
        with pytest.raises(ValueError, match="Unknown agent type"):
            factory.create("unknown_agent_type", None, None)
    
    def test_register_custom_agent(self):
        """测试注册自定义Agent"""
        factory = AgentFactory()
        
        def custom_agent_creator(llm, memory, **kwargs):
            return lambda state: {"custom": "agent"}
        
        # 注册自定义Agent
        factory.register("custom", custom_agent_creator)
        
        # 验证已注册
        assert factory.has_agent("custom")
        assert "custom" in factory.list_available_agents()
    
    def test_create_custom_agent(self):
        """测试创建自定义Agent"""
        factory = AgentFactory()
        
        def custom_agent_creator(llm, memory, **kwargs):
            def agent_func(state):
                return {"custom": "result"}
            return agent_func
        
        factory.register("test_agent", custom_agent_creator)
        
        # 创建Agent
        agent = factory.create("test_agent", None, None)
        assert callable(agent)
        
        # 调用Agent
        result = agent({"test": "state"})
        assert result == {"custom": "result"}


class TestGlobalFactory:
    """测试全局工厂函数"""
    
    def test_get_agent_factory_returns_singleton(self):
        """测试全局工厂是单例"""
        factory1 = get_agent_factory()
        factory2 = get_agent_factory()
        
        assert factory1 is factory2, "应该返回同一个实例"
    
    def test_create_agent_shortcut(self):
        """测试快捷创建Agent函数"""
        # 注册一个测试用Agent
        factory = get_agent_factory()
        
        def test_creator(llm, memory, **kwargs):
            return lambda state: state
        
        factory.register("shortcut_test", test_creator)
        
        # 使用快捷函数创建
        agent = create_agent("shortcut_test", None, None)
        assert callable(agent)


class TestAgentFactoryIntegration:
    """集成测试：与实际Agent的交互"""
    
    def test_can_import_bull_researcher(self):
        """测试可以导入Bull Researcher"""
        from tradingagents.agents.researchers.bull_researcher import create_bull_researcher
        assert callable(create_bull_researcher)
    
    def test_can_import_bear_researcher(self):
        """测试可以导入Bear Researcher"""
        from tradingagents.agents.researchers.bear_researcher import create_bear_researcher
        assert callable(create_bear_researcher)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
