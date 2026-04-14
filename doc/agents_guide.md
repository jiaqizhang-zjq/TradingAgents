# Agent 用法和解析指南

## 概述

TradingAgents 框架采用多代理设计，每个代理都有专门的角色和职责。代理通过 LangGraph 框架进行通信和协作，共同完成交易决策。

## Agent 架构

### 1. Agent 创建模式

每个 Agent 都遵循工厂函数模式，返回一个状态图节点函数：

```python
def create_agent_name(llm, [other_params]):
    def agent_node(state):
        # 1. 从状态中获取数据
        # 2. 定义工具
        # 3. 选择中/英文 prompt
        # 4. 创建 LLM 链
        # 5. 执行链并返回结果
        return {"messages": [result], "state_key": value}
    return agent_node
```

### 2. Agent 类型

#### 2.1 分析师代理 (Analysts) — 5 种

| 代理 | 文件 | 职责 |
|------|------|------|
| 市场分析师 | `analysts/market_analyst.py` | 技术指标、市场趋势分析 |
| 基本面分析师 | `analysts/fundamentals_analyst.py` | 财务报表、资产负债表分析 |
| 新闻分析师 | `analysts/news_analyst.py` | 新闻事件、宏观经济分析 |
| 社交媒体分析师 | `analysts/social_media_analyst.py` | Reddit/Twitter 情绪分析 |
| K线分析师 | `analysts/candlestick_analyst.py` | K线形态、价格行为分析 |

分析师之间**并行执行**，各自独立获取数据并生成报告。

#### 2.2 研究员代理 (Researchers) — 9 种风格

所有研究员继承自 `base_researcher.py` 抽象基类，通过 `RESEARCHER_REGISTRY`（定义于 `constants.py`）动态注册。

**初阶分析师（Junior）— 预设立场：**

| 代理 | 文件 | 风格 |
|------|------|------|
| 看多研究员 | `researchers/bull_researcher.py` | 预设看多立场，识别机会和增长潜力 |
| 看空研究员 | `researchers/bear_researcher.py` | 预设看空立场，识别风险和危险信号 |

**高级分析师（Senior/Master）— 独立判断：**

| 代理 | 文件 | 风格 |
|------|------|------|
| 巴菲特研究员 | `researchers/buffett_researcher.py` | 价值投资、安全边际、护城河、FCF |
| Cathie Wood 研究员 | `researchers/cathie_wood_researcher.py` | 颠覆式创新、ARK 风格 |
| Peter Lynch 研究员 | `researchers/peter_lynch_researcher.py` | GARP 成长合理价 |
| Charlie Munger 研究员 | `researchers/charlie_munger_researcher.py` | 逆向思维、能力圈、检查清单 |
| Ray Dalio 研究员 | `researchers/dalio_researcher.py` | 全天候策略、宏观周期、风险平价 |
| Jesse Livermore 研究员 | `researchers/livermore_researcher.py` | 趋势跟踪、关键点位、资金管理 |
| George Soros 研究员 | `researchers/soros_researcher.py` | 反身性理论、宏观对冲 |

**推荐组合：**
- 默认：`["bull", "bear", "buffett"]` — 经典多空 + 价值锚定
- 大师：`["buffett", "charlie_munger", "soros"]` — 价值 + 逆向 + 宏观
- 全面：`["bull", "bear", "buffett", "soros", "dalio"]` — 5 人深度辩论

**管理层：**

| 代理 | 文件 | 职责 |
|------|------|------|
| 研究管理器 | `managers/research_manager.py` | 组织 N-way 多轮辩论，追踪历史胜率 |

#### 2.3 交易员代理 (Trader)

| 代理 | 文件 | 职责 |
|------|------|------|
| 交易员 | `trader/trader.py` | 综合所有分析报告，做出 BUY/SELL/HOLD + 仓位决策 |

#### 2.4 风险管理代理 (Risk Management)

使用 `base_risk_debator.py` 基类消除三方辩论代码重复。

| 代理 | 文件 | 职责 |
|------|------|------|
| 风险辩论者基类 | `risk_mgmt/base_risk_debator.py` | `RiskDebatorConfig` + `create_risk_debator()` 工厂 |
| 激进辩论者 | `risk_mgmt/aggressive_debator.py` | 支持高风险高回报策略 |
| 保守辩论者 | `risk_mgmt/conservative_debator.py` | 支持低风险稳健策略 |
| 中性辩论者 | `risk_mgmt/neutral_debator.py` | 平衡风险和回报 |
| 风险管理器 | `managers/risk_manager.py` | 评估整体风险并做出最终判断 |

## Prompt 组织方式

### 1. 双语 Prompt 体系

所有 Agent 的 prompt 支持中/英双语，通过 `output_language` 配置切换：

```python
app_config = get_config()
language = app_config.get("output_language", "zh")
prompt = prompt_zh if language == "zh" else prompt_en
```

### 2. 研究员 Prompt 结构

研究员 prompt 定义在 `agents/prompts/perspectives.py` 中，每种投资风格包括：

- **角色定义**：投资哲学和风格描述
- **分析框架**：该风格关注的分析维度
- **输出格式**：BUY/SELL/HOLD + 置信度百分比

### 3. 提示词模板 (Prompt Template)

使用 `ChatPromptTemplate` 构建完整的提示词：

```python
prompt = ChatPromptTemplate.from_messages([
    ("system", "系统提示词内容"),
    MessagesPlaceholder(variable_name="messages"),
])
```

### 4. 部分参数 (Partial Parameters)

使用 `partial` 方法预设固定参数：

```python
prompt = prompt.partial(system_message=system_message)
prompt = prompt.partial(tool_names=", ".join([tool.name for tool in tools]))
```

## 工具调用 (Tool Calling)

### 1. 工具定义

工具使用抽象接口模式，定义在 `agents/utils/` 下：

| 工具文件 | 提供的工具 |
|----------|-----------|
| `core_stock_tools.py` | `get_stock_data` |
| `technical_indicators_tools.py` | `get_indicators` |
| `fundamental_data_tools.py` | `get_fundamentals`, `get_balance_sheet`, `get_cashflow`, `get_income_statement` |
| `news_data_tools.py` | `get_news`, `get_global_news`, `get_insider_transactions` |
| `candlestick_tools.py` | `get_candlestick_patterns` |
| `chart_patterns_tools.py` | `get_chart_patterns` |

### 2. 工具绑定

使用 `bind_tools` 将工具绑定到 LLM：

```python
chain = prompt | llm.bind_tools(tools)
```

### 3. 工具执行

LangGraph 的 `ToolNode` 负责执行工具调用：

```python
tool_node = ToolNode([get_stock_data, get_indicators])
```

## Graph 组织方式

### 1. 节点定义

每个 Agent 是图中的一个节点：

```python
workflow.add_node("Market Analyst", market_analyst_node)
workflow.add_node("tools_market", tool_node)
```

### 2. 边定义

定义节点之间的连接关系：

- 普通边：`add_edge(from_node, to_node)`
- 条件边：`add_conditional_edges(node, condition, mapping)`

### 3. 条件逻辑

使用 `ConditionalLogic` 类控制流程（定义于 `graph/conditional_logic.py`）：

```python
workflow.add_conditional_edges(
    "Market Analyst",
    conditional_logic.should_continue_market,
    ["tools_market", "Msg Clear Market"],
)
```

### 4. 研究员动态注册

研究员节点通过 `RESEARCHER_REGISTRY` 动态添加到图中（在 `graph/setup.py`）：

```python
for key in selected_researchers:
    info = RESEARCHER_REGISTRY[key]
    # 动态导入并创建研究员节点
    module = importlib.import_module(info["module"])
    factory_fn = getattr(module, info["factory"])
    node_fn = factory_fn(llm, ...)
    workflow.add_node(info["display_name"], node_fn)
```

## 状态管理

### 1. 状态定义

使用 `TypedDict` 定义状态结构（`agents/utils/agent_states.py`）：

```python
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    company_of_interest: str
    trade_date: str
    market_report: str
    sentiment_report: str
    news_report: str
    fundamentals_report: str
    candlestick_report: str
    # ... 其他字段

class InvestDebateState(TypedDict):
    # 研究员辩论状态
    history: str
    count: int
    # ...

class RiskDebateState(TypedDict):
    # 风险辩论状态
    history: str
    count: int
    aggressive_history: str
    conservative_history: str
    neutral_history: str
    # ...
```

### 2. 状态更新

每个 Agent 节点返回需要更新的状态字段：

```python
return {
    "messages": [result],
    "market_report": report,
}
```

## 完整工作流程

1. **初始化状态**: 创建初始状态，包含公司信息和交易日期
2. **分析师阶段**: 5 种分析师并行执行，分析不同维度的数据
3. **研究员辩论**: 选中的 N 个研究员进行 round-robin 多轮辩论
4. **研究管理器**: 汇总辩论结果，形成投资建议
5. **交易员决策**: 交易员根据所有分析做出交易计划
6. **风险辩论**: 激进/保守/中性三方进行风险评估
7. **风险管理器**: 做出最终风险评估和决策
8. **反思学习**: 记录经验到记忆系统

## 预测提取

### prediction_utils.py

通用的预测结果提取函数，支持中英文双语：

```python
from tradingagents.agents.utils.prediction_utils import extract_prediction

prediction, confidence = extract_prediction(
    response_content,
    language="zh",
    zh_pattern=r'预测[:：]\s*(买入|卖出|持有|BUY|SELL|HOLD).*?置信度[:：]\s*(\d+)%?',
    en_pattern=r'PREDICTION:\s*(BUY|SELL|HOLD).*?Confidence:\s*(\d+)%?',
    default_confidence=0.8,
)
```

### prediction_extractor.py

更复杂的预测提取策略，支持多种匹配模式和 fallback。

## 代码示例

### 创建新研究员

1. 创建研究员文件 `researchers/my_researcher.py`：

```python
from tradingagents.agents.researchers.base_researcher import BaseResearcher

class MyResearcher(BaseResearcher):
    @property
    def researcher_type(self) -> str:
        return "my_researcher"
    
    @property
    def display_name(self) -> str:
        return "My Researcher"

def create_my_researcher(llm, memory=None, research_tracker=None, **kwargs):
    researcher = MyResearcher(llm=llm, memory=memory, research_tracker=research_tracker)
    return researcher.create_node()
```

2. 在 `agents/prompts/perspectives.py` 中添加投资风格 prompt。

3. 在 `constants.py` 的 `RESEARCHER_REGISTRY` 中注册：

```python
RESEARCHER_REGISTRY = {
    # ... 现有注册项 ...
    "my_style": {
        "type": "my_researcher",
        "display_name": "My Researcher",
        "speaker_label": "MyStyle",
        "module": "tradingagents.agents.researchers.my_researcher",
        "factory": "create_my_researcher",
        "default_win_rate": DEFAULT_NEUTRAL_WIN_RATE,
    },
}
```

### 创建自定义分析师

```python
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool

@tool
def my_custom_tool(param: str) -> str:
    """自定义工具描述"""
    return f"处理结果: {param}"

def create_my_analyst(llm):
    def my_analyst_node(state):
        tools = [my_custom_tool]
        system_message = """你是一个自定义分析师..."""
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_message),
            MessagesPlaceholder(variable_name="messages"),
        ])
        chain = prompt | llm.bind_tools(tools)
        result = chain.invoke(state["messages"])
        return {
            "messages": [result],
            "my_result": result.content if not result.tool_calls else "",
        }
    return my_analyst_node
```

## 最佳实践

1. **单一职责**: 每个 Agent 应该专注于一个特定任务
2. **双语 Prompt**: 新 Agent 应同时提供中/英文 prompt
3. **工具设计**: 工具应简单、可组合、有良好的文档
4. **状态管理**: 明确哪些状态字段需要更新
5. **异常处理**: 使用自定义异常体系（`tradingagents/exceptions.py`）
6. **输入验证**: 使用 `tradingagents/utils/validators.py` 进行参数校验
7. **日志记录**: 使用 `logging_utils.py` 记录关键决策和中间结果
8. **测试**: 独立测试每个 Agent 和工具（`tests/unit/`）
