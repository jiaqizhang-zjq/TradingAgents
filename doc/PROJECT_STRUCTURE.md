# TradingAgents 项目结构说明

## 目录结构

```
TradingAgents/
├── assets/                    # 项目资源文件
│   ├── cli/                  # CLI 截图和界面资源
│   └── *.png                 # 项目图片资源
├── cli/                       # 命令行界面模块
│   ├── static/               # CLI 静态资源
│   ├── main.py               # CLI 主入口
│   ├── models.py             # CLI 数据模型
│   ├── config.py             # CLI 配置
│   └── utils.py              # CLI 工具函数
├── doc/                       # 项目文档
│   ├── README.md             # 文档首页
│   ├── architecture.md       # 架构文档
│   ├── api_config_guide.md   # API 配置指南
│   ├── agents_guide.md       # Agent 使用指南
│   ├── llm_call_chain.md     # LLM 调用链
│   ├── longbridge_guide.md   # 长桥 API 指南
│   └── social_media_guide.md # 社交媒体指南
├── tests/                     # 测试文件目录
│   └── test_*.py             # 各类测试脚本
├── reports/                   # 生成的分析报告
├── langgraph_outputs/         # LangGraph 输出目录
├── langgraph_outputs_detailed/ # 详细日志输出
├── tradingagents/             # 核心代码包
│   ├── agents/               # 代理模块
│   │   ├── analysts/         # 分析师代理
│   │   ├── managers/         # 管理器代理
│   │   ├── researchers/      # 研究员代理
│   │   ├── risk_mgmt/        # 风险管理代理
│   │   ├── trader/           # 交易员代理
│   │   └── utils/            # 代理工具
│   ├── dataflows/            # 数据流模块
│   ├── graph/                # LangGraph 模块
│   ├── llm_clients/          # LLM 客户端
│   └── default_config.py     # 默认配置
├── .env.example               # 环境变量示例
├── .gitignore                 # Git 忽略文件
├── LICENSE                    # 许可证
├── README.md                  # 项目说明
├── main.py                    # 主入口
├── pyproject.toml             # 项目配置
├── requirements.txt           # 依赖项
├── save_to_database.py        # 数据库存储脚本
├── run_with_detailed_logging.py # 详细日志运行脚本
└── trading_analysis.db        # SQLite 数据库
```

## 核心模块详解

### 1. tradingagents/agents/ - 代理模块

代理是系统的核心组件，每个代理都有专门的角色和职责。

#### 1.1 analysts/ - 分析师团队

| 文件 | 职责 | 工具 |
|------|------|------|
| market_analyst.py | 市场趋势分析、技术指标 | get_stock_data, get_indicators |
| fundamentals_analyst.py | 财务报表分析 | get_fundamentals, get_balance_sheet |
| candlestick_analyst.py | 蜡烛图形态识别 | get_candlestick_patterns |
| news_analyst.py | 新闻情绪分析 | get_news, get_global_news |
| social_media_analyst.py | 社交媒体监控 | get_social_media_data |

#### 1.2 managers/ - 管理器

| 文件 | 职责 |
|------|------|
| research_manager.py | 协调研究员团队、整合观点 |
| risk_manager.py | 评估投资组合风险 |

#### 1.3 researchers/ - 研究员团队

| 文件 | 职责 |
|------|------|
| bull_researcher.py | 看多分析、寻找增长机会 |
| bear_researcher.py | 看空分析、识别潜在风险 |

#### 1.4 risk_mgmt/ - 风险管理

| 文件 | 职责 |
|------|------|
| aggressive_debator.py | 激进策略辩论 |
| conservative_debator.py | 保守策略辩论 |
| neutral_debator.py | 中性平衡分析 |

#### 1.5 trader/ - 交易员

| 文件 | 职责 |
|------|------|
| trader.py | 综合决策、交易执行 |

#### 1.6 utils/ - 代理工具

| 文件 | 职责 |
|------|------|
| core_stock_tools.py | 核心股票数据工具 |
| fundamental_data_tools.py | 基本面数据工具 |
| technical_indicators_tools.py | 技术指标工具 |
| news_data_tools.py | 新闻数据工具 |
| candlestick_tools.py | 蜡烛图工具 |
| agent_utils.py | 通用工具函数 |
| memory.py | 记忆管理 |
| agent_states.py | 状态管理 |

### 2. tradingagents/dataflows/ - 数据流模块

#### 2.1 数据源接口

| 文件 | 数据源 | 数据类型 |
|------|--------|----------|
| longbridge.py | 长桥 API | 港股美股实时数据、基本面数据 |
| alpha_vantage*.py | Alpha Vantage | 全球股票、技术指标、基本面 |
| y_finance.py | Yahoo Finance | 免费股票数据、新闻 |
| yfinance_news.py | Yahoo Finance | 新闻数据 |

#### 2.2 数据管理

| 文件 | 职责 |
|------|------|
| unified_data_manager.py | 统一数据管理、多数据源优先级 |
| interface.py | 数据接口层、路由分发 |
| database.py | SQLite 数据库存储 |
| data_cache.py | 内存缓存 |
| data_preloader.py | 数据预加载 |

#### 2.3 指标计算

| 文件 | 职责 |
|------|------|
| complete_indicators.py | 完整技术指标计算 |
| indicator_groups.py | 指标分组管理 |
| stockstats_utils.py | 股票统计工具 |

### 3. tradingagents/graph/ - LangGraph 模块

| 文件 | 职责 |
|------|------|
| trading_graph.py | 交易图主类、工作流定义 |
| setup.py | 图设置、节点配置 |
| propagation.py | 信号传播机制 |
| conditional_logic.py | 条件逻辑、状态转换 |
| signal_processing.py | 信号处理 |
| reflection.py | 反射机制 |

### 4. tradingagents/llm_clients/ - LLM 客户端

| 文件 | 职责 |
|------|------|
| base_client.py | 基础客户端接口 |
| factory.py | 客户端工厂 |
| openai_client.py | OpenAI (GPT) |
| google_client.py | Google (Gemini) |
| anthropic_client.py | Anthropic (Claude) |
| validators.py | 验证器 |

## 脚本文件说明

| 文件 | 用途 |
|------|------|
| main.py | 主程序入口 |
| save_to_database.py | 将分析结果保存到数据库 |
| run_with_detailed_logging.py | 带详细日志的运行脚本 |
| interactive_step_run.py | 交互式逐步执行 |
| interactive_run.py | 交互式运行 |

## 配置文件

| 文件 | 用途 |
|------|------|
| .env.example | 环境变量示例 |
| pyproject.toml | Python 项目配置 |
| requirements.txt | Python 依赖 |
| tradingagents/default_config.py | 系统默认配置 |

## 数据文件

| 文件/目录 | 用途 |
|-----------|------|
| trading_analysis.db | SQLite 数据库 |
| reports/ | 生成的 Markdown 报告 |
| langgraph_outputs/ | LangGraph 输出 |
| langgraph_outputs_detailed/ | 详细日志 |

## 开发规范

### 代码组织

1. **代理开发**: 在 `tradingagents/agents/` 下创建新代理
2. **数据源开发**: 在 `tradingagents/dataflows/` 下创建新数据源
3. **工具开发**: 在 `tradingagents/agents/utils/` 下创建新工具
4. **测试开发**: 在 `tests/` 下创建测试文件

### 命名规范

- 文件: 小写下划线（如 `market_analyst.py`）
- 类: 大驼峰（如 `TradingAgentsGraph`）
- 函数: 小写下划线（如 `get_stock_data`）
- 常量: 大写下划线（如 `DEFAULT_CONFIG`）

### 导入规范

```python
# 标准库
import os
import json
from datetime import datetime

# 第三方库
import pandas as pd
import numpy as np
from langchain_core.tools import tool

# 项目内部
from tradingagents.dataflows.interface import route_to_vendor
from tradingagents.agents.utils.agent_utils import get_stock_data
```

## 版本历史

### v0.2.0 (2026-02)
- 新增数据库存储功能
- 支持多数据源优先级配置
- 新增长桥 API 支持
- 新增交互式运行模式

### v0.1.0 (2025-12)
- 初始版本发布
- 基础多代理框架
- Alpha Vantage 和 Yahoo Finance 支持
