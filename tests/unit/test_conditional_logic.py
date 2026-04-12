"""
测试条件逻辑 - 辩论路由和分析器路由
"""

import pytest
from tradingagents.graph.conditional_logic import ConditionalLogic


class TestDebateRouting:
    """测试辩论路由逻辑（默认三方辩论：bull + bear + buffett）"""
    
    def test_first_round_starts_with_bull(self):
        """第1轮：应该从Bull Researcher开始"""
        logic = ConditionalLogic(max_debate_rounds=2)
        state = {
            "investment_debate_state": {
                "count": 0,
                "latest_speaker": ""
            }
        }
        result = logic.should_continue_debate(state)
        assert result == "Bull Researcher", "第1轮应该选择Bull Researcher"
    
    def test_alternates_bull_to_bear(self):
        """第2轮：Bull后应该是Bear"""
        logic = ConditionalLogic(max_debate_rounds=2)
        state = {
            "investment_debate_state": {
                "count": 1,
                "latest_speaker": "Bull"
            }
        }
        result = logic.should_continue_debate(state)
        assert result == "Bear Researcher", "Bull后应该是Bear Researcher"
    
    def test_alternates_bear_to_buffett(self):
        """第3轮：Bear后应该是Buffett（三方辩论）"""
        logic = ConditionalLogic(max_debate_rounds=2)
        state = {
            "investment_debate_state": {
                "count": 2,
                "latest_speaker": "Bear"
            }
        }
        result = logic.should_continue_debate(state)
        assert result == "Buffett Researcher", "Bear后应该是Buffett Researcher"
    
    def test_ends_after_max_rounds(self):
        """达到 3 * max_debate_rounds 后进入Research Manager"""
        logic = ConditionalLogic(max_debate_rounds=2)
        state = {
            "investment_debate_state": {
                "count": 6,  # 3 researchers * 2 rounds
                "latest_speaker": "Buffett"
            }
        }
        result = logic.should_continue_debate(state)
        assert result == "Research Manager", "达到max_rounds后应该进入Research Manager"
    
    def test_debate_sequence_complete(self):
        """测试完整的三方辩论序列（2轮）"""
        logic = ConditionalLogic(max_debate_rounds=2)
        
        sequence = [
            ({"count": 0, "latest_speaker": ""}, "Bull Researcher"),        # 第1轮 #1
            ({"count": 1, "latest_speaker": "Bull"}, "Bear Researcher"),     # 第1轮 #2
            ({"count": 2, "latest_speaker": "Bear"}, "Buffett Researcher"),  # 第1轮 #3
            ({"count": 3, "latest_speaker": "Buffett"}, "Bull Researcher"),  # 第2轮 #1
            ({"count": 4, "latest_speaker": "Bull"}, "Bear Researcher"),     # 第2轮 #2
            ({"count": 5, "latest_speaker": "Bear"}, "Buffett Researcher"),  # 第2轮 #3
            ({"count": 6, "latest_speaker": "Buffett"}, "Research Manager"), # 结束
        ]
        
        for debate_state, expected in sequence:
            state = {"investment_debate_state": debate_state}
            result = logic.should_continue_debate(state)
            assert result == expected, f"Count={debate_state['count']}, Expected={expected}, Got={result}"

    def test_two_researcher_debate(self):
        """测试双方辩论（显式指定 bull + bear）"""
        logic = ConditionalLogic(max_debate_rounds=2, selected_researchers=["bull", "bear"])
        
        sequence = [
            ({"count": 0, "latest_speaker": ""}, "Bull Researcher"),
            ({"count": 1, "latest_speaker": "Bull"}, "Bear Researcher"),
            ({"count": 2, "latest_speaker": "Bear"}, "Bull Researcher"),
            ({"count": 3, "latest_speaker": "Bull"}, "Bear Researcher"),
            ({"count": 4, "latest_speaker": "Bear"}, "Research Manager"),
        ]
        
        for debate_state, expected in sequence:
            state = {"investment_debate_state": debate_state}
            result = logic.should_continue_debate(state)
            assert result == expected, f"Count={debate_state['count']}, Expected={expected}, Got={result}"


class TestRiskAnalysisRouting:
    """测试风险分析路由逻辑"""
    
    def test_risk_routing_aggressive_to_conservative(self):
        """Aggressive后应该是Conservative"""
        logic = ConditionalLogic(max_risk_discuss_rounds=2)
        state = {
            "risk_debate_state": {
                "count": 1,
                "latest_speaker": "Aggressive Analyst"
            }
        }
        result = logic.should_continue_risk_analysis(state)
        assert result == "Conservative Analyst"
    
    def test_risk_routing_conservative_to_neutral(self):
        """Conservative后应该是Neutral"""
        logic = ConditionalLogic(max_risk_discuss_rounds=2)
        state = {
            "risk_debate_state": {
                "count": 2,
                "latest_speaker": "Conservative Analyst"
            }
        }
        result = logic.should_continue_risk_analysis(state)
        assert result == "Neutral Analyst"
    
    def test_risk_routing_ends_after_max_rounds(self):
        """达到max_rounds后进入Risk Judge"""
        logic = ConditionalLogic(max_risk_discuss_rounds=2)
        state = {
            "risk_debate_state": {
                "count": 6,  # 3 * max_risk_discuss_rounds
                "latest_speaker": "Neutral Analyst"
            }
        }
        result = logic.should_continue_risk_analysis(state)
        assert result == "Risk Judge"


class TestAnalystRouting:
    """测试分析师路由逻辑"""
    
    @pytest.fixture
    def mock_message_with_tools(self):
        """带工具调用的消息"""
        class MockMessage:
            def __init__(self):
                self.tool_calls = [{"name": "get_stock_data"}]
        return MockMessage()
    
    @pytest.fixture
    def mock_message_without_tools(self):
        """不带工具调用的消息"""
        class MockMessage:
            def __init__(self):
                self.tool_calls = []
        return MockMessage()
    
    def test_market_analyst_with_tools(self, mock_message_with_tools):
        """Market Analyst有工具调用时路由到tools"""
        logic = ConditionalLogic()
        state = {"messages": [mock_message_with_tools]}
        result = logic.should_continue_market(state)
        assert result == "tools_market"
    
    def test_market_analyst_without_tools(self, mock_message_without_tools):
        """Market Analyst无工具调用时继续"""
        logic = ConditionalLogic()
        state = {"messages": [mock_message_without_tools]}
        result = logic.should_continue_market(state)
        assert result == "Msg Clear Market"
    
    def test_news_analyst_routing(self, mock_message_with_tools, mock_message_without_tools):
        """测试News Analyst路由"""
        logic = ConditionalLogic()
        
        state_with_tools = {"messages": [mock_message_with_tools]}
        assert logic.should_continue_news(state_with_tools) == "tools_news"
        
        state_without_tools = {"messages": [mock_message_without_tools]}
        assert logic.should_continue_news(state_without_tools) == "Msg Clear News"


class TestConditionalLogicConfiguration:
    """测试配置参数"""
    
    def test_default_max_debate_rounds(self):
        """测试默认max_debate_rounds"""
        logic = ConditionalLogic()
        assert logic.max_debate_rounds == 2
    
    def test_custom_max_debate_rounds(self):
        """测试自定义max_debate_rounds（三方辩论）"""
        logic = ConditionalLogic(max_debate_rounds=3)
        state = {
            "investment_debate_state": {
                "count": 9,  # 3 researchers * 3 rounds
                "latest_speaker": "Buffett"
            }
        }
        result = logic.should_continue_debate(state)
        assert result == "Research Manager", "自定义max_debate_rounds生效"
    
    def test_custom_risk_rounds(self):
        """测试自定义max_risk_discuss_rounds"""
        logic = ConditionalLogic(max_risk_discuss_rounds=3)
        assert logic.max_risk_discuss_rounds == 3
        
        state = {
            "risk_debate_state": {
                "count": 9,  # 3 * 3
                "latest_speaker": "Neutral Analyst"
            }
        }
        result = logic.should_continue_risk_analysis(state)
        assert result == "Risk Judge"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
