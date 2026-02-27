"""单元测试: 数据统计收集器"""
import pytest
from tradingagents.dataflows.core.statistics_collector import StatisticsCollector


class TestStatisticsCollector:
    """测试统计收集器"""
    
    @pytest.fixture
    def collector(self):
        """创建测试用收集器"""
        return StatisticsCollector()
        
    def test_initialization(self, collector):
        """测试初始化"""
        assert collector._stats == {}
        assert isinstance(collector._stats, dict)
        
    def test_record_success(self, collector):
        """测试记录成功请求"""
        collector.record_success("yfinance", "get_stock", 0.5)
        collector.record_success("yfinance", "get_stock", 0.3)
        
        stats = collector.get_statistics()
        assert len(stats) == 1
        assert stats[0].vendor == "yfinance"
        assert stats[0].success_count == 2
        
    def test_record_failure(self, collector):
        """测试记录失败请求"""
        collector.record_failure("yfinance", "get_stock", "Timeout")
        
        stats = collector.get_statistics()
        assert len(stats) == 1
        assert stats[0].failure_count == 1
        assert stats[0].last_error == "Timeout"
        
    def test_success_rate(self, collector):
        """测试成功率计算"""
        collector.record_success("yfinance", "get_stock", 0.5)
        collector.record_success("yfinance", "get_stock", 0.3)
        collector.record_failure("yfinance", "get_stock", "Error")
        
        stats = collector.get_statistics()
        assert len(stats) == 1
        assert stats[0].success_rate == pytest.approx(2/3, 0.01)
        
    def test_average_time(self, collector):
        """测试平均响应时间"""
        collector.record_success("yfinance", "get_stock", 0.5)
        collector.record_success("yfinance", "get_stock", 0.3)
        
        stats = collector.get_statistics()
        assert len(stats) == 1
        assert stats[0].average_time_seconds == pytest.approx(0.4, 0.01)
        
    def test_get_statistics_comprehensive(self, collector):
        """测试获取完整统计数据"""
        collector.record_success("yfinance", "get_stock", 0.5)
        collector.record_failure("yfinance", "get_stock", "Error")
        collector.record_success("akshare", "get_data", 0.3)
        
        stats = collector.get_statistics()
        
        assert len(stats) == 2
        vendors = [s.vendor for s in stats]
        assert "yfinance" in vendors
        assert "akshare" in vendors
        
    def test_reset(self, collector):
        """测试重置统计"""
        collector.record_success("yfinance", "get_stock", 0.5)
        collector._stats.clear()
        
        stats = collector.get_statistics()
        assert len(stats) == 0
