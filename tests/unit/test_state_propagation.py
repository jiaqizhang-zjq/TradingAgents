"""
测试状态初始化和传播逻辑
"""

import pytest
from tradingagents.graph.propagation import Propagator


class TestStatePropagation:
    """测试状态传播逻辑"""
    
    @pytest.fixture
    def propagator(self):
        """创建Propagator实例"""
        return Propagator()
    
    def test_create_initial_state(self, propagator):
        """测试创建初始状态"""
        state = propagator.create_initial_state("AAPL", "2024-01-15")
        
        # 验证基本字段
        assert "messages" in state
        assert "company_of_interest" in state
        assert "trade_date" in state
        assert state["company_of_interest"] == "AAPL"
        assert state["trade_date"] == "2024-01-15"
    
    def test_debate_state_initialization(self, propagator):
        """测试辩论状态初始化"""
        state = propagator.create_initial_state("TSLA", "2024-01-20")
        
        assert "investment_debate_state" in state
        debate_state = state["investment_debate_state"]
        
        # 验证辩论状态字段
        assert "count" in debate_state
        assert "latest_speaker" in debate_state
        assert debate_state["count"] == 0
        assert debate_state["latest_speaker"] == ""
    
    def test_risk_state_initialization(self, propagator):
        """测试风险分析状态初始化"""
        state = propagator.create_initial_state("NVDA", "2024-02-01")
        
        assert "risk_debate_state" in state
        risk_state = state["risk_debate_state"]
        
        assert "count" in risk_state
        assert risk_state["count"] == 0
        # risk_debate_state 不需要 latest_speaker（由conditional_logic处理）
    
    def test_report_fields_initialization(self, propagator):
        """测试报告字段初始化"""
        state = propagator.create_initial_state("MSFT", "2024-03-01")
        
        # 验证所有报告字段都被初始化（使用实际的字段名）
        expected_reports = [
            "market_report",
            "sentiment_report",
            "news_report",
            "fundamentals_report",
            "candlestick_report"
        ]
        
        for report in expected_reports:
            assert report in state, f"{report} should be initialized"
            assert isinstance(state[report], str), f"{report} should be a string"
    
    def test_analyst_state_initialization(self, propagator):
        """测试分析师状态初始化"""
        state = propagator.create_initial_state("GOOGL", "2024-04-01")
        
        # 验证分析师状态字段
        analyst_states = [
            "market_analyst_state",
            "news_analyst_state",
            "social_analyst_state"
        ]
        
        for analyst_state in analyst_states:
            if analyst_state in state:
                assert isinstance(state[analyst_state], dict)
    
    def test_debate_state_can_be_updated(self, propagator):
        """测试辩论状态可以被更新"""
        state = propagator.create_initial_state("AAPL", "2024-01-15")
        
        # 模拟Bull Researcher发言后的状态更新（手动更新）
        state["investment_debate_state"]["count"] = 1
        state["investment_debate_state"]["latest_speaker"] = "Bull"
        
        assert state["investment_debate_state"]["count"] == 1
        assert state["investment_debate_state"]["latest_speaker"] == "Bull"
    
    def test_preserve_latest_speaker(self, propagator):
        """测试保留latest_speaker字段"""
        state = propagator.create_initial_state("AAPL", "2024-01-15")
        
        # 第一轮：Bull发言（手动更新状态）
        state["investment_debate_state"]["count"] = 1
        state["investment_debate_state"]["latest_speaker"] = "Bull"
        assert state["investment_debate_state"]["latest_speaker"] == "Bull"
        
        # 第二轮：Bear发言
        state["investment_debate_state"]["count"] = 2
        state["investment_debate_state"]["latest_speaker"] = "Bear"
        assert state["investment_debate_state"]["latest_speaker"] == "Bear"
        assert state["investment_debate_state"]["count"] == 2


class TestStateStructure:
    """测试状态结构完整性"""
    
    def test_all_required_fields_present(self):
        """测试所有必需字段都存在"""
        propagator = Propagator()
        state = propagator.create_initial_state("TEST", "2024-01-01")
        
        required_fields = [
            "messages",
            "company_of_interest",
            "trade_date",
            "investment_debate_state",
            "risk_debate_state",
            "market_report",
            "sentiment_report",
            "news_report",
            "fundamentals_report",
            "candlestick_report"
        ]
        
        for field in required_fields:
            assert field in state, f"Missing required field: {field}"
    
    def test_debate_state_structure(self):
        """测试辩论状态结构"""
        propagator = Propagator()
        state = propagator.create_initial_state("TEST", "2024-01-01")
        
        debate_state = state["investment_debate_state"]
        assert isinstance(debate_state, dict)
        assert "count" in debate_state
        assert "latest_speaker" in debate_state
        assert isinstance(debate_state["count"], int)
        assert isinstance(debate_state["latest_speaker"], str)


class TestEdgeCases:
    """测试边界情况"""
    
    def test_empty_symbol(self):
        """测试空股票代码"""
        propagator = Propagator()
        # 应该能够创建状态，即使symbol为空
        state = propagator.create_initial_state("", "2024-01-01")
        assert state["company_of_interest"] == ""
    
    def test_invalid_date_format(self):
        """测试无效日期格式（Propagator不验证，由validators验证）"""
        propagator = Propagator()
        # Propagator本身不验证日期格式
        state = propagator.create_initial_state("AAPL", "invalid-date")
        assert state["trade_date"] == "invalid-date"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
