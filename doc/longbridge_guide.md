# 长桥（Longbridge）API 使用指南

## 📋 概述

本指南介绍如何在 TradingAgents 项目中使用长桥（Longbridge）API 替换 Alpha Vantage 和 Yahoo Finance。

## 🚀 快速开始

### 1. 安装长桥 SDK

```bash
pip install longbridge
```

### 2. 获取 API 凭证

1. 访问 [长桥开放平台](https://open.longportapp.com/)
2. 注册/登录账号
3. 创建应用并获取：
   - `LONGBRIDGE_APP_KEY`
   - `LONGBRIDGE_APP_SECRET`
   - `LONGBRIDGE_ACCESS_TOKEN`

### 3. 配置环境变量

复制 `.env.example` 为 `.env` 并填写长桥凭证：

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```env
# Longbridge (长桥) API
LONGBRIDGE_APP_KEY=your_app_key
LONGBRIDGE_APP_SECRET=your_app_secret
LONGBRIDGE_ACCESS_TOKEN=your_access_token
```

### 4. 配置使用长桥 API

修改配置文件，将数据源切换为长桥：

```python
from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.graph.trading_graph import TradingAgentsGraph

config = DEFAULT_CONFIG.copy()

# 方法1: 在类别级别配置使用长桥
config["data_vendors"] = {
    "core_stock_apis": "longbridge",
    "technical_indicators": "longbridge",
    "fundamental_data": "longbridge",
    "news_data": "longbridge",
}

# 方法2: 在工具级别配置（优先级更高）
config["tool_vendors"] = {
    "get_stock_data": "longbridge",
    "get_indicators": "longbridge",
}

ta = TradingAgentsGraph(debug=True, config=config)
```

## 📊 功能说明

### 已实现的功能

| 功能 | 说明 | 状态 | 备注 |
|------|------|------|------|
| 股票数据 (OHLCV) | 获取历史K线数据 | ✅ 模拟实现 | 需要替换为真实API |
| 技术指标 | SMA、EMA、RSI、MACD、布林带等 | ✅ 本地计算 | 基于股票数据计算 |
| 基本面数据 | PE、PB、市值等 | ✅ 模拟实现 | 需要替换为真实API |
| 资产负债表 | 资产、负债等 | ✅ 模拟实现 | 需要替换为真实API |
| 现金流量表 | 经营、投资、筹资现金流 | ✅ 模拟实现 | 需要替换为真实API |
| 损益表 | 收入、利润等 | ✅ 模拟实现 | 需要替换为真实API |
| 新闻数据 | 公司新闻 | ❌ 不支持 | 自动回退到 Yahoo Finance |
| 全球新闻 | 市场新闻 | ❌ 不支持 | 自动回退到 Yahoo Finance |
| 内幕交易 | 高管交易数据 | ❌ 不支持 | 自动回退到 Yahoo Finance |

**重要说明**：长桥 API 主要提供行情数据，**不提供新闻和内幕交易数据**。这些功能会自动回退到 Yahoo Finance 或 Alpha Vantage。

### 技术指标支持

当前支持的技术指标：

- **移动平均线**：
  - `close_50_sma` - 50日简单移动平均
  - `close_200_sma` - 200日简单移动平均
  - `close_10_ema` - 10日指数移动平均

- **MACD**：
  - `macd` - MACD线
  - `macds` - 信号线
  - `macdh` - 柱状图

- **动量指标**：
  - `rsi` - 相对强弱指标

- **波动率指标**：
  - `boll` - 布林带中轨
  - `boll_ub` - 布林带上轨
  - `boll_lb` - 布林带下轨
  - `atr` - 平均真实波幅

## 🔧 自定义实现

当前实现包含模拟数据，您可以根据长桥 SDK 的实际 API 进行替换：

### 替换股票数据获取

编辑 `tradingagents/dataflows/longbridge.py`，修改 `get_stock_data` 方法：

```python
def get_stock_data(self, symbol: str, start_date: str, end_date: str) -> str:
    self._initialize()
    
    # 使用长桥SDK获取真实数据
    # 示例代码（请根据实际SDK调整）
    # from longbridge.openapi import QuoteContext
    # bars = self.quote_ctx.get_history_candlesticks(
    #     symbol=symbol,
    #     period=Period.Day,
    #     count=100
    # )
    
    # 将数据转换为CSV格式
    # data = self._convert_to_csv(bars)
    
    # 暂时使用模拟数据
    data = self._generate_mock_stock_data(symbol, start_dt, end_dt)
    return data
```

### 参考长桥 SDK 文档

- [长桥开放平台文档](https://open.longportapp.com/docs)
- [Python SDK GitHub](https://github.com/longbridgeapp/openapi-python)

## 📝 使用示例

### 完整示例

```python
from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG

# 配置使用长桥
config = DEFAULT_CONFIG.copy()
config["data_vendors"] = {
    "core_stock_apis": "longbridge",
    "technical_indicators": "longbridge",
    "fundamental_data": "longbridge",
    "news_data": "longbridge",
}

# 创建图实例
ta = TradingAgentsGraph(debug=True, config=config)

# 运行
_, decision = ta.propagate("NVDA", "2026-01-15")
print(decision)
```

## ⚠️ 注意事项

1. **模拟数据**：当前实现使用模拟数据，实际使用时需要替换为真实的长桥API调用
2. **API 限制**：注意长桥API的调用频率限制
3. **股票代码**：确保使用正确的股票代码格式（长桥可能需要特定的代码格式）
4. **错误处理**：添加适当的错误处理和重试机制

## 🆘 故障排除

### SDK 导入失败

```
ImportError: No module named 'longbridge'
```

解决方法：
```bash
pip install longbridge
```

### 环境变量未设置

```
ValueError: 请设置 LONGBRIDGE_APP_KEY, LONGBRIDGE_APP_SECRET, LONGBRIDGE_ACCESS_TOKEN 环境变量
```

解决方法：在 `.env` 文件中设置正确的凭证。

### 回退到其他数据源

如果长桥API不可用，系统会自动回退到其他可用的数据源（如 Yahoo Finance 或 Alpha Vantage）。

## 📚 相关链接

- [长桥开放平台](https://open.longportapp.com/)
- [长桥 Python SDK](https://github.com/longbridgeapp/openapi-python)
- [TradingAgents 项目文档](README.md)
