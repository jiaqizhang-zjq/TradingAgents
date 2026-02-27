"""
测试BaseResearcher基类
"""

import pytest
from tradingagents.agents.researchers.base_researcher import BaseResearcher


class MockTracker:
    """模拟ResearchTracker"""
    
    def get_researcher_win_rate(self, researcher_type, symbol, default_win_rate):
        if symbol:
            return {"win_rate": 0.65, "total_predictions": 10}
        else:
            return {"win_rate": 0.55, "total_predictions": 50}


class TestBaseResearcher:
    """测试BaseResearcher类"""
    
    @pytest.fixture
    def mock_llm(self):
        """模拟LLM"""
        class MockLLM:
            def invoke(self, prompt):
                return "上涨, 中等"
        return MockLLM()
    
    @pytest.fixture
    def mock_memory(self):
        """模拟Memory"""
        class MockMemory:
            def get(self, key):
                return []
        return MockMemory()
    
    @pytest.fixture
    def researcher(self, mock_llm, mock_memory):
        """创建测试用的researcher实例"""
        system_prompts = {
            "zh": "你是一个看涨的研究员",
            "en": "You are a bullish researcher"
        }
        return BaseResearcher(
            researcher_type="bull_researcher",
            system_prompts=system_prompts,
            llm=mock_llm,
            memory=mock_memory,
            default_win_rate=0.52
        )
    
    def test_initialization(self, researcher):
        """测试初始化"""
        assert researcher.researcher_type == "bull_researcher"
        assert researcher.default_win_rate == 0.52
        assert researcher.system_prompts["zh"] == "你是一个看涨的研究员"
    
    def test_build_win_rate_string_zh(self, researcher):
        """测试构建胜率字符串（中文）"""
        tracker = MockTracker()
        result = researcher._build_win_rate_string("AAPL", "zh", tracker)
        
        assert "该股票胜率：65.0%" in result
        assert "10次" in result
        assert "平均胜率：55.0%" in result
        assert "50次" in result
    
    def test_build_win_rate_string_en(self, researcher):
        """测试构建胜率字符串（英文）"""
        tracker = MockTracker()
        result = researcher._build_win_rate_string("AAPL", "en", tracker)
        
        assert "This stock: 65.0%" in result
        assert "10 trades" in result
        assert "Average: 55.0%" in result
        assert "50 trades" in result
    
    def test_build_win_rate_string_no_history(self, researcher):
        """测试无历史数据时的胜率字符串"""
        class NoHistoryTracker:
            def get_researcher_win_rate(self, researcher_type, symbol, default_win_rate):
                if symbol:
                    return {"win_rate": default_win_rate, "total_predictions": 0}
                else:
                    return {"win_rate": 0.55, "total_predictions": 50}
        
        tracker = NoHistoryTracker()
        result_zh = researcher._build_win_rate_string("NEW", "zh", tracker)
        result_en = researcher._build_win_rate_string("NEW", "en", tracker)
        
        assert "暂无历史数据" in result_zh
        assert "No history for this stock" in result_en
    
    def test_get_stance_zh(self, researcher):
        """测试获取立场（中文）"""
        assert researcher._get_stance_zh() == "看涨"
    
    def test_get_stance_en(self, researcher):
        """测试获取立场（英文）"""
        assert researcher._get_stance_en() == "bullish"
    
    def test_parse_llm_response_exists(self, researcher):
        """测试_parse_llm_response方法存在"""
        # BaseResearcher有_parse_llm_response方法
        assert hasattr(researcher, '_parse_llm_response')
        # 该方法需要state, company_name, trade_date, language参数
        # 这里只测试方法存在性，不测试具体逻辑（逻辑在子类中实现）
    
    def test_get_stance_zh(self, researcher):
        """测试获取立场（中文）"""
        # 这个方法需要在子类中实现
        assert hasattr(researcher, '_get_stance_zh')


class TestBaseResearcherMethods:
    """测试BaseResearcher基本方法"""
    
    @pytest.fixture
    def researcher(self):
        """创建基础researcher实例"""
        return BaseResearcher(
            researcher_type="test_researcher",
            system_prompts={"zh": "测试", "en": "Test"},
            llm=None,
            memory=None,
            default_win_rate=0.50
        )
    
    def test_has_build_win_rate_string(self, researcher):
        """测试有_build_win_rate_string方法"""
        assert hasattr(researcher, '_build_win_rate_string')
        assert callable(researcher._build_win_rate_string)
    
    def test_has_build_prompt(self, researcher):
        """测试有_build_prompt方法"""
        assert hasattr(researcher, '_build_prompt')
        assert callable(researcher._build_prompt)
    
    def test_has_parse_llm_response(self, researcher):
        """测试有_parse_llm_response方法"""
        assert hasattr(researcher, '_parse_llm_response')
        assert callable(researcher._parse_llm_response)


class TestBullResearcherSpecific:
    """测试Bull Researcher特定逻辑"""
    
    def test_bull_researcher_stance(self):
        """测试Bull Researcher的立场"""
        from tradingagents.agents.researchers.bull_researcher import create_bull_researcher
        
        # 这里只测试类的存在性和基本属性
        # 实际创建需要真实的LLM和memory
        assert create_bull_researcher is not None


class TestBearResearcherSpecific:
    """测试Bear Researcher特定逻辑"""
    
    def test_bear_researcher_stance(self):
        """测试Bear Researcher的立场"""
        from tradingagents.agents.researchers.bear_researcher import create_bear_researcher
        
        # 这里只测试类的存在性和基本属性
        assert create_bear_researcher is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
