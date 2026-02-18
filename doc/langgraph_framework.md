# TradingAgents LangGraph 框架文档

## 目录
1. [整体流程图](#整体流程图)
2. [节点详细说明](#节点详细说明)
3. [边的定义](#边的定义)

---

## 整体流程图

### 当前顺序执行模式

```
┌─────────────────────────────────────────────────────────────────────────┐
│                            START                                         │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    Market Analyst (可选)                                  │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │  [有工具调用?] ───是──→ tools_market                               │  │
│  │       │                              │                               │  │
│  │       否                              │                               │  │
│  │       │                              │                               │  │
│  │       ▼                              ▼                               │  │
│  │  Msg Clear Market ←─────────────────┘                               │  │
│  └───────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                  Social Media Analyst (可选)                              │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │  [有工具调用?] ───是──→ tools_social                              │  │
│  │       │                              │                               │  │
│  │       否                              │                               │  │
│  │       │                              │                               │  │
│  │       ▼                              ▼                               │  │
│  │  Msg Clear Social ←─────────────────┘                               │  │
│  └───────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    News Analyst (可选)                                    │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │  [有工具调用?] ───是──→ tools_news                                │  │
│  │       │                              │                               │  │
│  │       否                              │                               │  │
│  │       │                              │                               │  │
│  │       ▼                              ▼                               │  │
│  │  Msg Clear News ←───────────────────┘                               │  │
│  └───────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                  Fundamentals Analyst (可选)                              │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │  [有工具调用?] ───是──→ tools_fundamentals                        │  │
│  │       │                              │                               │  │
│  │       否                              │                               │  │
│  │       │                              │                               │  │
│  │       ▼                              ▼                               │  │
│  │  Msg Clear Fundamentals ←────────────┘                               │  │
│  └───────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                  Candlestick Analyst (可选)                               │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │  [有工具调用?] ───是──→ tools_candlestick                        │  │
│  │       │                              │                               │  │
│  │       否                              │                               │  │
│  │       │                              │                               │  │
│  │       ▼                              ▼                               │  │
│  │  Msg Clear Candlestick ←─────────────┘                               │  │
│  └───────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          Bull Researcher                                  │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │  [辩论是否继续?]                                                     │  │
│  │       │                                                             │  │
│  │       ├────是──→ Bear Researcher                                    │  │
│  │       │                                                             │  │
│  │       └────否──→ Research Manager                                   │  │
│  └───────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                          Bear Researcher                                  │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │  [辩论是否继续?]                                                     │  │
│  │       │                                                             │  │
│  │       ├────是──→ Bull Researcher                                    │  │
│  │       │                                                             │  │
│  │       └────否──→ Research Manager                                   │  │
│  └───────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        Research Manager                                   │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                            Trader                                         │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      Aggressive Analyst                                  │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │  [风险分析是否继续?]                                                  │  │
│  │       │                                                             │  │
│  │       ├────是──→ Conservative Analyst                               │  │
│  │       │                                                             │  │
│  │       └────否──→ Risk Judge                                        │  │
│  └───────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                     Conservative Analyst                                  │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │  [风险分析是否继续?]                                                  │  │
│  │       │                                                             │  │
│  │       ├────是──→ Neutral Analyst                                    │  │
│  │       │                                                             │  │
│  │       └────否──→ Risk Judge                                        │  │
│  └───────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                       Neutral Analyst                                    │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │  [风险分析是否继续?]                                                  │  │
│  │       │                                                             │  │
│  │       ├────是──→ Aggressive Analyst                                 │  │
│  │       │                                                             │  │
│  │       └────否──→ Risk Judge                                        │  │
│  └───────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          Risk Judge                                      │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                             END                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 节点详细说明

### 1. 分析师节点

#### 1.1 Market Analyst (市场分析师)

**文件位置**: `tradingagents/agents/analysts/market_analyst.py`

**功能**: 分析金融市场技术指标

**可用工具**:
- `get_stock_data`: 获取股票 OHLCV 数据
- `get_indicators`: 获取技术指标

**输出字段**: `market_report`

**Prompt 概要**:
- 选择最多 12 个最相关的技术指标
- 指标类别包括：
  - 移动平均线（SMA/EMA 5/10/20/50/100/200）
  - MACD 相关
  - 动量指标（RSI、Stochastic、StochRSI、CCI、ROC、MFI）
  - 波动率指标（Bollinger Bands、ATR、NATR）
  - 成交量指标（VWMA、Volume、OBV、AD、ADX）
  - 支撑/阻力和图表形态（Swing Highs/Lows、Fibonacci、Pivot Points）
- 分析包括：趋势分析、支撑/阻力、动量、波动率、成交量、图表形态
- 输出 Markdown 表格

---

#### 1.2 Social Media Analyst (社交媒体分析师)

**文件位置**: `tradingagents/agents/analysts/social_media_analyst.py`

**功能**: 分析社交媒体情绪和公司新闻

**可用工具**:
- `get_news`: 获取传统新闻
- `get_social_media_data`: 获取社交媒体数据（Reddit、Twitter）

**输出字段**: `sentiment_report`

**Prompt 概要**:
- 分析社交媒体帖子、公司新闻和公众情绪
- 分析指南：
  - 先使用 `get_social_media_data` 收集社交媒体情绪
  - 再使用 `get_news` 收集传统新闻
  - 分析两个来源的情绪和主题
  - 寻找模式、趋势和分歧
  - 关注可能影响市场的高影响力帖子或文章
- 输出 Markdown 表格

---

#### 1.3 News Analyst (新闻分析师)

**文件位置**: `tradingagents/agents/analysts/news_analyst.py`

**功能**: 分析近期新闻和趋势

**可用工具**:
- `get_news`: 获取公司特定或目标新闻搜索
- `get_global_news`: 获取更广泛的宏观经济新闻

**输出字段**: `news_report`

**Prompt 概要**:
- 分析过去一周的近期新闻和趋势
- 撰写与交易和宏观经济相关的世界现状综合报告
- 输出 Markdown 表格

---

#### 1.4 Fundamentals Analyst (基本面分析师)

**文件位置**: `tradingagents/agents/analysts/fundamentals_analyst.py`

**功能**: 分析公司基本面信息

**可用工具**:
- `get_fundamentals`: 综合公司分析
- `get_balance_sheet`: 资产负债表
- `get_cashflow`: 现金流量表
- `get_income_statement`: 损益表

**输出字段**: `fundamentals_report`

**Prompt 概要**:
- 分析过去一周公司的基本面信息
- 包括财务文件、公司简介、基本财务、财务历史
- 输出 Markdown 表格

---

#### 1.5 Candlestick Analyst (蜡烛图分析师)

**文件位置**: `tradingagents/agents/analysts/candlestick_analyst.py`

**功能**: 分析蜡烛图形态、价格行为和技术图表形态

**可用工具**:
- `get_stock_data`: 获取 OHLCV 数据
- `get_indicators`: 获取技术指标

**输出字段**: `candlestick_report`

**Prompt 概要**:
- 分析指南：
  1. 先用 `get_stock_data` 获取 OHLCV 数据
  2. 再用 `get_indicators` 计算关键技术指标

- **蜡烛图形态识别**:
  - 单根蜡烛：Doji（各种变体）、Hammer、Hanging Man、Inverted Hammer、Shooting Star、Spinning Top、Marubozu、Long Shadow
  - 双根蜡烛：Bullish/Bearish Engulfing、Piercing Pattern、Dark Cloud Cover、Tweezer Tops/Bottoms、Bullish/Bearish Harami、Kicker Pattern
  - 三根及以上：Morning/Evening Star、Morning/Evening Doji Star、Three White Soldiers、Three Black Crows、Three Inside Up/Down、Rising/Falling Three Methods、Abandoned Baby、Three Line Strike

- **图表形态**:
  - 反转形态：Head and Shoulders（Top/Bottom）、Double Top/Bottom、Triple Top/Bottom、Rounding Top/Bottom、Wedge（Rising/Falling）
  - 延续形态：Symmetrical/Ascending/Descending Triangle、Flag、Pennant、Rectangle、Cup and Handle、Channel Pattern

- **趋势和支撑/阻力分析**:
  - 趋势分析（上升/下降/横盘）、趋势线绘制、通道识别、Golden/Death Cross
  - 支撑/阻力：水平、动态（均线）、高低点、斐波那契、心理价位、突破确认

- **成交量分析**: 成交量峰值、成交量确认、累积/派发、成交量背离、OBV 含义

- **动量指标**: RSI、MACD、Stochastic、CCI

- **分析框架**: 趋势分析 → 支撑/阻力识别 → 图表形态识别 → 蜡烛图形态分析 → 成交量确认 → 指标融合

- 输出两个 Markdown 表格（图表形态 + 蜡烛图形态）

---

### 2. 研究团队节点

#### 2.1 Bull Researcher (多头研究员)

**文件位置**: `tradingagents/agents/researchers/bull_researcher.py`

**功能**: 主张投资该股票，构建看涨论点

**输入状态字段**:
- `market_report`: 市场分析师报告
- `sentiment_report`: 社交媒体分析师报告
- `news_report`: 新闻分析师报告
- `fundamentals_report`: 基本面分析师报告
- `candlestick_report`: 蜡烛图分析师报告
- `investment_debate_state`: 辩论状态

**输出状态字段**:
- 更新 `investment_debate_state`

**Prompt 概要**:
- 强调增长潜力、竞争优势、积极市场指标
- 关键要点：
  - 增长潜力：市场机会、收入预测、可扩展性
  - 竞争优势：独特产品、强势品牌、主导市场定位
  - 积极指标：财务健康、行业趋势、近期积极新闻
  - 反驳看跌论点：用具体数据和合理推理反驳
- 输出格式：`Bull Analyst: {content}`

---

#### 2.2 Bear Researcher (空头研究员)

**文件位置**: `tradingagents/agents/researchers/bear_researcher.py`

**功能**: 反对投资该股票，构建看跌论点

**输入状态字段**:
- `market_report`: 市场分析师报告
- `sentiment_report`: 社交媒体分析师报告
- `news_report`: 新闻分析师报告
- `fundamentals_report`: 基本面分析师报告
- `candlestick_report`: 蜡烛图分析师报告
- `investment_debate_state`: 辩论状态

**输出状态字段**:
- 更新 `investment_debate_state`

**Prompt 概要**:
- 强调风险、挑战和负面指标
- 关键要点：
  - 风险和挑战：市场饱和、财务不稳定、宏观经济威胁
  - 竞争劣势：弱势市场定位、创新下降、竞争对手威胁
  - 负面指标：财务数据、市场趋势、近期不利新闻
  - 反驳看涨论点：揭露弱点或过度乐观假设
- 输出格式：`Bear Analyst: {content}`

---

#### 2.3 Research Manager (研究经理)

**文件位置**: `tradingagents/agents/managers/research_manager.py`

**功能**: 评估辩论并做出最终决定（看涨/看跌/持有），制定投资计划

**输入状态字段**:
- `market_report`: 市场分析师报告
- `sentiment_report`: 社交媒体分析师报告
- `news_report`: 新闻分析师报告
- `fundamentals_report`: 基本面分析师报告
- `candlestick_report`: 蜡烛图分析师报告
- `investment_debate_state`: 辩论状态

**输出状态字段**:
- 更新 `investment_debate_state`
- `investment_plan`: 投资计划

**Prompt 概要**:
- 角色：投资组合经理和辩论主持人
- 目标：批判性评估辩论轮次并做出明确决定
- 决策选项：看涨/看跌/持有（持有仅在强烈理由下）
- 交付内容：
  1. 明确可操作的建议（Buy/Sell/Hold）
  2. 理由：解释论点如何导致结论
  3. 战略行动：实施建议的具体步骤
- 考虑过去类似情况的错误，从中学习改进
- 简明总结双方关键要点，聚焦最有说服力的证据或推理

---

### 3. 交易员节点

#### 3.1 Trader (交易员)

**文件位置**: `tradingagents/agents/trader/trader.py`

**功能**: 根据投资计划做出交易决策

**输入状态字段**:
- `market_report`: 市场分析师报告
- `sentiment_report`: 社交媒体分析师报告
- `news_report`: 新闻分析师报告
- `fundamentals_report`: 基本面分析师报告
- `candlestick_report`: 蜡烛图分析师报告
- `investment_plan`: 投资计划

**输出状态字段**:
- `trader_investment_plan`: 交易员投资计划

**Prompt 概要**:
- 角色：分析市场数据做出投资决策的交易代理
- 基于研究经理的投资计划，提供具体的 Buy/Sell/Hold 建议
- 必须以 `FINAL TRANSACTION PROPOSAL: **BUY/HOLD/SELL**` 结尾
- 利用过去决策的教训从中学习

---

### 4. 风险分析团队节点

#### 4.1 Aggressive Analyst (激进风险分析师)

**文件位置**: `tradingagents/agents/risk_mgmt/aggressive_debator.py`

**功能**: 倡导高回报、高风险机会

**输入状态字段**:
- `market_report`: 市场分析师报告
- `sentiment_report`: 社交媒体分析师报告
- `news_report`: 新闻分析师报告
- `fundamentals_report`: 基本面分析师报告
- `candlestick_report`: 蜡烛图分析师报告
- `trader_investment_plan`: 交易员投资计划
- `risk_debate_state`: 风险辩论状态

**输出状态字段**:
- 更新 `risk_debate_state`

**Prompt 概要**:
- 积极倡导高回报、高风险机会
- 强调大胆策略和竞争优势
- 评估交易员决策时专注于潜在上行、增长潜力和创新收益
- 直接回应保守和中性分析师的每一点，用数据驱动的反驳和有说服力的推理
- 强调谨慎可能错失关键机会或假设可能过于保守
- 输出格式：`Aggressive Analyst: {content}`

---

#### 4.2 Conservative Analyst (保守风险分析师)

**文件位置**: `tradingagents/agents/risk_mgmt/conservative_debator.py`

**功能**: 保护资产、最小化波动、确保稳定可靠增长

**输入状态字段**:
- `market_report`: 市场分析师报告
- `sentiment_report`: 社交媒体分析师报告
- `news_report`: 新闻分析师报告
- `fundamentals_report`: 基本面分析师报告
- `candlestick_report`: 蜡烛图分析师报告
- `trader_investment_plan`: 交易员投资计划
- `risk_debate_state`: 风险辩论状态

**输出状态字段**:
- 更新 `risk_debate_state`

**Prompt 概要**:
- 首要目标：保护资产、最小化波动、确保稳定可靠增长
- 优先考虑稳定性、安全性和风险缓解
- 仔细评估潜在损失、经济衰退和市场波动
- 评估交易员决策时批判性检查高风险元素
- 积极反驳激进和中性分析师的论点
- 强调他们的观点可能忽视潜在威胁或未能优先考虑可持续性
- 输出格式：`Conservative Analyst: {content}`

---

#### 4.3 Neutral Analyst (中性风险分析师)

**文件位置**: `tradingagents/agents/risk_mgmt/neutral_debator.py`

**功能**: 提供平衡视角，权衡交易员决策的潜在收益和风险

**输入状态字段**:
- `market_report`: 市场分析师报告
- `sentiment_report`: 社交媒体分析师报告
- `news_report`: 新闻分析师报告
- `fundamentals_report`: 基本面分析师报告
- `candlestick_report`: 蜡烛图分析师报告
- `trader_investment_plan`: 交易员投资计划
- `risk_debate_state`: 风险辩论状态

**输出状态字段**:
- 更新 `risk_debate_state`

**Prompt 概要**:
- 提供平衡视角，权衡交易员决策的潜在收益和风险
- 优先考虑全面方法，评估上行和下行，同时考虑更广泛的市场趋势、潜在经济转变和多样化策略
- 挑战激进和保守分析师，指出每个视角可能过于乐观或过于谨慎
- 支持适度、可持续策略来调整交易员决策
- 输出格式：`Neutral Analyst: {content}`

---

#### 4.4 Risk Judge (风险法官)

**文件位置**: `tradingagents/agents/managers/risk_manager.py`

**功能**: 评估三个风险分析师之间的辩论，确定交易员的最佳行动方案

**输入状态字段**:
- `market_report`: 市场分析师报告
- `sentiment_report`: 社交媒体分析师报告
- `news_report`: 新闻分析师报告
- `fundamentals_report`: 基本面分析师报告
- `candlestick_report`: 蜡烛图分析师报告
- `investment_plan`: 投资计划
- `risk_debate_state`: 风险辩论状态

**输出状态字段**:
- 更新 `risk_debate_state`
- `final_trade_decision`: 最终交易决策

**Prompt 概要**:
- 角色：风险管理法官和辩论主持人
- 目标：评估三个风险分析师（激进、中性、保守）之间的辩论，确定交易员的最佳行动方案
- 决策必须导致明确的建议：Buy、Sell 或 Hold
- 仅在有特定论点强烈理由时选择 Hold，而不是在所有方面似乎有效时作为后备
- 决策指南：
  1. 总结关键论点：提取每个分析师的最强点，聚焦与上下文的相关性
  2. 提供理由：用辩论中的直接引语和反驳支持建议
  3. 改进交易员计划：从交易员的原始计划开始，根据分析师的见解进行调整
  4. 从过去错误学习：使用过去反思中的教训来解决先前误判并改进当前决策
- 交付内容：明确可操作的建议 + 基于辩论和过去反思的详细推理

---

### 5. 工具节点和消息清除节点

每个分析师都有对应的工具节点和消息清除节点：

#### 5.1 工具节点 (tools_{analyst_type})

**功能**: 执行分析师请求的工具调用

**节点名称**:
- `tools_market`
- `tools_social`
- `tools_news`
- `tools_fundamentals`
- `tools_candlestick`

**边**:
- 从工具节点 → 回到对应分析师节点

---

#### 5.2 消息清除节点 (Msg Clear {analyst_type})

**功能**: 清除分析师的消息，为下一个分析师或下一步做准备

**节点名称**:
- `Msg Clear Market`
- `Msg Clear Social`
- `Msg Clear News`
- `Msg Clear Fundamentals`
- `Msg Clear Candlestick`

**实现**: `tradingagents/agents/utils/agent_utils.py` 中的 `create_msg_delete()`

**功能**:
- 移除所有消息
- 添加最小化的占位符消息（`HumanMessage(content="Continue")`）

---

## 边的定义

### 1. 分析师相关边

#### 1.1 START → 第一个分析师
- **类型**: `add_edge` (固定边)
- **源**: `START`
- **目标**: `{first_analyst_type} Analyst`
- **说明**: 从第一个选定的分析师开始

---

#### 1.2 分析师 → 条件边
- **类型**: `add_conditional_edges` (条件边)
- **源**: `{analyst_type} Analyst`
- **条件函数**: `should_continue_{analyst_type}` (来自 `ConditionalLogic` 类)
- **目标**:
  - 如果有工具调用 → `tools_{analyst_type}`
  - 如果没有工具调用 → `Msg Clear {analyst_type}`
- **说明**: 根据分析师是否需要调用工具来决定下一步

---

#### 1.3 工具节点 → 分析师
- **类型**: `add_edge` (固定边)
- **源**: `tools_{analyst_type}`
- **目标**: `{analyst_type} Analyst`
- **说明**: 工具执行完后回到分析师继续处理

---

#### 1.4 消息清除节点 → 下一个分析师 / Bull Researcher
- **类型**: `add_edge` (固定边)
- **源**: `Msg Clear {analyst_type}`
- **目标**:
  - 如果不是最后一个分析师 → `{next_analyst_type} Analyst`
  - 如果是最后一个分析师 → `Bull Researcher`
- **说明**: 连接到下一个分析师，或进入研究辩论阶段

---

### 2. 研究辩论相关边

#### 2.1 Bull Researcher → 条件边
- **类型**: `add_conditional_edges` (条件边)
- **源**: `Bull Researcher`
- **条件函数**: `should_continue_debate` (来自 `ConditionalLogic` 类)
- **目标**:
  - 如果辩论继续 → `Bear Researcher`
  - 如果辩论结束 → `Research Manager`
- **说明**: 根据辩论轮数决定下一步

---

#### 2.2 Bear Researcher → 条件边
- **类型**: `add_conditional_edges` (条件边)
- **源**: `Bear Researcher`
- **条件函数**: `should_continue_debate` (来自 `ConditionalLogic` 类)
- **目标**:
  - 如果辩论继续 → `Bull Researcher`
  - 如果辩论结束 → `Research Manager`
- **说明**: 根据辩论轮数决定下一步

---

#### 2.3 Research Manager → Trader
- **类型**: `add_edge` (固定边)
- **源**: `Research Manager`
- **目标**: `Trader`
- **说明**: 研究经理完成后进入交易员阶段

---

### 3. 风险分析相关边

#### 3.1 Trader → Aggressive Analyst
- **类型**: `add_edge` (固定边)
- **源**: `Trader`
- **目标**: `Aggressive Analyst`
- **说明**: 交易员完成后进入风险分析阶段，从激进分析师开始

---

#### 3.2 Aggressive Analyst → 条件边
- **类型**: `add_conditional_edges` (条件边)
- **源**: `Aggressive Analyst`
- **条件函数**: `should_continue_risk_analysis` (来自 `ConditionalLogic` 类)
- **目标**:
  - 如果风险分析继续 → `Conservative Analyst`
  - 如果风险分析结束 → `Risk Judge`
- **说明**: 根据风险分析轮数决定下一步

---

#### 3.3 Conservative Analyst → 条件边
- **类型**: `add_conditional_edges` (条件边)
- **源**: `Conservative Analyst`
- **条件函数**: `should_continue_risk_analysis` (来自 `ConditionalLogic` 类)
- **目标**:
  - 如果风险分析继续 → `Neutral Analyst`
  - 如果风险分析结束 → `Risk Judge`
- **说明**: 根据风险分析轮数决定下一步

---

#### 3.4 Neutral Analyst → 条件边
- **类型**: `add_conditional_edges` (条件边)
- **源**: `Neutral Analyst`
- **条件函数**: `should_continue_risk_analysis` (来自 `ConditionalLogic` 类)
- **目标**:
  - 如果风险分析继续 → `Aggressive Analyst`
  - 如果风险分析结束 → `Risk Judge`
- **说明**: 根据风险分析轮数决定下一步

---

#### 3.5 Risk Judge → END
- **类型**: `add_edge` (固定边)
- **源**: `Risk Judge`
- **目标**: `END`
- **说明**: 风险法官完成后结束整个流程

---

## 条件判断逻辑

### ConditionalLogic 类

**文件位置**: `tradingagents/graph/conditional_logic.py`

#### 1. should_continue_{analyst_type}
判断分析师是否需要继续调用工具

**逻辑**:
```python
if last_message.tool_calls:
    return "tools_{analyst_type}"
return "Msg Clear {analyst_type}"
```

#### 2. should_continue_debate
判断研究辩论是否继续

**逻辑**:
```python
if count >= 2 * max_debate_rounds:
    return "Research Manager"
if current_response starts with "Bull":
    return "Bear Researcher"
return "Bull Researcher"
```

**默认配置**: `max_debate_rounds = 1` (即 2 轮来回)

#### 3. should_continue_risk_analysis
判断风险分析是否继续

**逻辑**:
```python
if count >= 3 * max_risk_discuss_rounds:
    return "Risk Judge"
if latest_speaker starts with "Aggressive":
    return "Conservative Analyst"
if latest_speaker starts with "Conservative":
    return "Neutral Analyst"
return "Aggressive Analyst"
```

**默认配置**: `max_risk_discuss_rounds = 1` (即 3 轮来回)

---

## AgentState 状态定义

**文件位置**: `tradingagents/agents/utils/agent_states.py`

### 主要字段

```python
{
    # 基础信息
    "messages": [...],                    # 消息历史
    "company_of_interest": "...",         # 关注的公司
    "trade_date": "...",                  # 交易日期
    "sender": "...",                       # 发送者
    
    # 分析师报告
    "market_report": "...",               # 市场分析师报告
    "sentiment_report": "...",            # 社交媒体分析师报告
    "news_report": "...",                 # 新闻分析师报告
    "fundamentals_report": "...",          # 基本面分析师报告
    "candlestick_report": "...",          # 蜡烛图分析师报告
    
    # 研究辩论状态
    "investment_debate_state": {
        "history": "...",                  # 辩论历史
        "bull_history": "...",             # 多头历史
        "bear_history": "...",             # 空头历史
        "current_response": "...",         # 当前响应
        "judge_decision": "...",           # 法官决策
        "count": 0                         # 计数
    },
    
    # 投资计划
    "investment_plan": "...",              # 投资计划
    "trader_investment_plan": "...",       # 交易员投资计划
    
    # 风险辩论状态
    "risk_debate_state": {
        "history": "...",                  # 辩论历史
        "aggressive_history": "...",       # 激进历史
        "conservative_history": "...",     # 保守历史
        "neutral_history": "...",          # 中性历史
        "latest_speaker": "...",           # 最新发言者
        "current_aggressive_response": "...",
        "current_conservative_response": "...",
        "current_neutral_response": "...",
        "count": 0                         # 计数
    },
    
    # 最终决策
    "final_trade_decision": "..."          # 最终交易决策
}
```

---

## 配置

### 可选分析师列表

在 `setup_graph(selected_analysts=[...])` 中配置：

```python
selected_analysts = [
    "market",        # 市场分析师
    "social",        # 社交媒体分析师
    "news",          # 新闻分析师
    "fundamentals",  # 基本面分析师
    "candlestick"    # 蜡烛图分析师（新增）
]
```

**默认值**: 所有 5 个分析师都启用

---

## 总结

这个 LangGraph 框架实现了一个多代理交易决策系统，包含：

1. **5 个专业分析师**，各自独立分析不同维度
2. **2 个研究员**进行多空辩论
3. **1 个研究经理**做出投资决策
4. **1 个交易员**制定交易计划
5. **3 个风险分析师**从不同风险角度评估
6. **1 个风险法官**做出最终交易决策

整个流程从分析师收集信息开始，经过研究辩论、交易计划、风险评估，最终做出明确的 Buy/Sell/Hold 决策。
