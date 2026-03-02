"""
性能监控器单元测试
"""
import pytest
import time
from tradingagents.utils.performance_monitor import (
    PerformanceMonitor,
    track_performance,
    get_monitor,
    reset_performance_stats
)


class TestPerformanceMonitor:
    """测试性能监控器"""
    
    def setup_method(self):
        """每个测试前重置"""
        reset_performance_stats()
    
    def test_singleton(self):
        """测试单例模式"""
        monitor1 = PerformanceMonitor()
        monitor2 = PerformanceMonitor()
        assert monitor1 is monitor2
    
    def test_record_success(self):
        """测试记录成功调用"""
        monitor = get_monitor()
        monitor.record("test_func", 0.1, success=True)
        
        summary = monitor.get_summary()
        assert summary["total_calls"] == 1
        assert summary["total_errors"] == 0
        assert "test_func" in summary["functions"]
    
    def test_record_error(self):
        """测试记录失败调用"""
        monitor = get_monitor()
        monitor.record("test_func", 0.1, success=False, error=Exception("test"))
        
        summary = monitor.get_summary()
        assert summary["total_errors"] == 1
    
    def test_multiple_calls(self):
        """测试多次调用"""
        monitor = get_monitor()
        monitor.record("test_func", 0.1)
        monitor.record("test_func", 0.2)
        monitor.record("test_func", 0.3)
        
        summary = monitor.get_summary()
        func_data = summary["functions"]["test_func"]
        assert func_data["calls"] == 3
    
    def test_decorator_success(self):
        """测试装饰器（成功）"""
        @track_performance()
        def test_func(x):
            time.sleep(0.01)
            return x * 2
        
        result = test_func(5)
        assert result == 10
        
        monitor = get_monitor()
        summary = monitor.get_summary()
        assert "test_func" in summary["functions"]
    
    def test_decorator_with_type(self):
        """测试带类型的装饰器"""
        @track_performance("database")
        def query_data(id):
            return {"id": id}
        
        result = query_data(123)
        assert result["id"] == 123
        
        monitor = get_monitor()
        summary = monitor.get_summary()
        assert "database.query_data" in summary["functions"]
    
    def test_decorator_error(self):
        """测试装饰器（异常）"""
        @track_performance()
        def failing_func():
            raise ValueError("test error")
        
        with pytest.raises(ValueError):
            failing_func()
        
        monitor = get_monitor()
        summary = monitor.get_summary()
        assert summary["total_errors"] == 1
    
    def test_get_slowest_calls(self):
        """测试获取最慢调用"""
        monitor = get_monitor()
        monitor.record("func1", 0.1)
        monitor.record("func2", 0.5)
        monitor.record("func3", 0.2)
        
        slowest = monitor.get_slowest_calls(2)
        assert len(slowest) == 2
        assert slowest[0]["duration_ms"] > slowest[1]["duration_ms"]
    
    def test_get_recent_errors(self):
        """测试获取最近错误"""
        monitor = get_monitor()
        monitor.record("func1", 0.1, success=False, error=Exception("error1"))
        monitor.record("func2", 0.1, success=True)
        monitor.record("func3", 0.1, success=False, error=Exception("error2"))
        
        errors = monitor.get_recent_errors(10)
        assert len(errors) == 2
        assert all(not log["success"] for log in errors)
    
    def test_reset(self):
        """测试重置"""
        monitor = get_monitor()
        monitor.record("test_func", 0.1)
        
        assert monitor.get_summary()["total_calls"] > 0
        
        monitor.reset()
        assert monitor.get_summary()["total_calls"] == 0
    
    def test_performance_metrics(self):
        """测试性能指标计算"""
        monitor = get_monitor()
        monitor.record("test_func", 0.1)
        monitor.record("test_func", 0.3)
        monitor.record("test_func", 0.2)
        
        metric = monitor.metrics["test_func"]
        assert metric.call_count == 3
        assert metric.min_time == 0.1
        assert metric.max_time == 0.3
        assert 0.19 < metric.avg_time < 0.21  # ~0.2
