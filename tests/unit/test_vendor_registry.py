"""单元测试: 数据供应商注册表"""
import pytest
from tradingagents.dataflows.core.vendor_registry import VendorRegistry


class TestVendorRegistry:
    """测试供应商注册表"""
    
    @pytest.fixture
    def registry(self):
        """创建测试用注册表"""
        return VendorRegistry()
        
    def test_initialization(self, registry):
        """测试初始化 - 空注册表"""
        assert len(registry._vendors) == 0
        assert isinstance(registry._vendors, dict)
        
    def test_register_vendor(self, registry):
        """测试注册供应商"""
        from tradingagents.dataflows.core.vendor_registry import VendorConfig, VendorPriority
        config = VendorConfig(name="test_vendor", priority=VendorPriority.HIGH)
        registry.register_vendor(config)
        assert "test_vendor" in registry._vendors
        assert registry._vendors["test_vendor"].priority == VendorPriority.HIGH
        
    def test_get_vendor_config(self, registry):
        """测试获取供应商配置"""
        from tradingagents.dataflows.core.vendor_registry import VendorConfig
        config = VendorConfig(name="yfinance")
        registry.register_vendor(config)
        
        retrieved = registry.get_vendor_config("yfinance")
        assert retrieved is not None
        assert retrieved.name == "yfinance"
        
    def test_get_vendor_config_not_found(self, registry):
        """测试获取不存在的供应商"""
        config = registry.get_vendor_config("nonexistent")
        assert config is None
        
    def test_list_vendors(self, registry):
        """测试列出所有供应商"""
        from tradingagents.dataflows.core.vendor_registry import VendorConfig
        registry.register_vendor(VendorConfig(name="vendor1", enabled=True))
        registry.register_vendor(VendorConfig(name="vendor2", enabled=False))
        
        enabled = registry.list_vendors(enabled_only=True)
        assert "vendor1" in enabled
        assert "vendor2" not in enabled
        
        all_vendors = registry.list_vendors(enabled_only=False)
        assert len(all_vendors) == 2
        
    def test_unregister_vendor(self, registry):
        """测试注销供应商"""
        from tradingagents.dataflows.core.vendor_registry import VendorConfig
        registry.register_vendor(VendorConfig(name="test"))
        assert "test" in registry._vendors
        
        registry.unregister_vendor("test")
        assert "test" not in registry._vendors
