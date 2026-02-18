# TradingAgents 项目框架

## 项目结构

```
TradingAgents/
├── assets/              # 项目资源文件
├── cli/                 # 命令行界面
├── tradingagents/       # 核心代码
│   ├── agents/          # 各类智能代理
│   │   ├── analysts/    # 分析师代理
│   │   ├── managers/    # 管理器代理
│   │   ├── researchers/ # 研究员代理
│   │   ├── risk_mgmt/   # 风险管理代理
│   │   ├── trader/      # 交易员代理
│   │   └── utils/       # 代理工具
│   ├── dataflows/       # 数据获取和处理
│   ├── graph/           # 代理通信图
│   └── llm_clients/     # LLM 客户端
├── .env.example         # 环境变量示例
├── .gitignore           # Git 忽略文件
├── LICENSE              # 许可证
├── README.md            # 项目说明
├── main.py              # 主入口
├── pyproject.toml       # 项目配置
├── requirements.txt     # 依赖项
└── test.py              # 测试文件
```

## 模块说明

### 1. tradingagents/agents/

#### analysts/
- `fundamentals_analyst.py`: 基本面分析师，评估公司财务状况和业绩指标
- `market_analyst.py`: 市场分析师，分析市场趋势和行业动态
- `news_analyst.py`: 新闻分析师，监控全球新闻和宏观经济指标
- `social_media_analyst.py`: 社交媒体分析师，分析社交媒体和公众情绪

#### managers/
- `research_manager.py`: 研究管理器，协调研究员团队的工作
- `risk_manager.py`: 风险管理器，评估投资组合风险

#### researchers/
- `bear_researcher.py`: 看空研究员，从风险角度评估投资机会
- `bull_researcher.py`: 看多研究员，从收益角度评估投资机会

#### risk_mgmt/
- `aggressive_debator.py`: 激进辩论者，支持高风险高回报策略
- `conservative_debator.py`: 保守辩论者，支持低风险低回报策略
- `neutral_debator.py`: 中性辩论者，平衡风险和回报

#### trader/
- `trader.py`: 交易员，根据分析师和研究员的报告做出交易决策

#### utils/
- `agent_states.py`: 代理状态管理
- `agent_utils.py`: 代理工具函数
- `core_stock_tools.py`: 核心股票工具
- `fundamental_data_tools.py`: 基本面数据工具
- `memory.py`: 代理记忆管理
- `news_data_tools.py`: 新闻数据工具
- `technical_indicators_tools.py`: 技术指标工具

### 2. tradingagents/dataflows/

- `alpha_vantage.py`: Alpha Vantage API 接口
- `alpha_vantage_common.py`: Alpha Vantage 通用工具
- `alpha_vantage_fundamentals.py`: Alpha Vantage 基本面数据
- `alpha_vantage_indicator.py`: Alpha Vantage 技术指标
- `alpha_vantage_news.py`: Alpha Vantage 新闻数据
- `alpha_vantage_stock.py`: Alpha Vantage 股票数据
- `config.py`: 数据流程配置
- `interface.py`: 数据接口
- `stockstats_utils.py`: 股票统计工具
- `utils.py`: 通用工具
- `y_finance.py`: Yahoo Finance API 接口
- `yfinance_news.py`: Yahoo Finance 新闻数据

### 3. tradingagents/graph/

- `__init__.py`: 初始化文件
- `conditional_logic.py`: 条件逻辑
- `propagation.py`: 信号传播
- `reflection.py`: 反射机制
- `setup.py`: 图设置
- `signal_processing.py`: 信号处理
- `trading_graph.py`: 交易图，核心代理通信图

### 4. tradingagents/llm_clients/

- `__init__.py`: 初始化文件
- `anthropic_client.py`: Anthropic 客户端
- `base_client.py`: 基础客户端
- `factory.py`: 客户端工厂
- `google_client.py`: Google 客户端
- `openai_client.py`: OpenAI 客户端
- `validators.py`: 验证器

## 核心流程

1. **数据获取**: 通过 dataflows 模块从 Alpha Vantage 和 Yahoo Finance 获取市场数据
2. **分析处理**: 各分析师代理分析不同维度的数据
3. **研究辩论**: 研究员团队对分析结果进行辩论
4. **风险评估**: 风险管理团队评估投资组合风险
5. **交易决策**: 交易员根据分析结果和风险评估做出交易决策
6. **执行交易**: 执行交易并监控结果

## 技术栈

- Python 3.13
- LangGraph (代理通信)
- 多种 LLM 提供商 (OpenAI, Google, Anthropic, xAI, OpenRouter, Ollama)
- Alpha Vantage API (金融数据)
- Yahoo Finance API (金融数据)
- 技术指标库
- 情绪分析库

## 配置管理

项目使用 `default_config.py` 管理默认配置，包括 LLM 提供商、模型选择、辩论轮数等参数。用户可以通过修改配置来自定义系统行为。

## 扩展性

项目设计具有良好的扩展性，支持：

1. **添加新代理**: 可以在 agents 目录下添加新的代理类型
2. **添加新数据源**: 可以在 dataflows 目录下添加新的数据源
3. **添加新 LLM 提供商**: 可以在 llm_clients 目录下添加新的 LLM 客户端
4. **修改代理通信逻辑**: 可以修改 graph 目录下的文件来调整代理通信逻辑