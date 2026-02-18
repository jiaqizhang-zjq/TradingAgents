# Agent 用法和解析指南

## 概述

TradingAgents 框架采用多代理设计，每个代理都有专门的角色和职责。代理通过 LangGraph 框架进行通信和协作，共同完成交易决策。

## Agent 架构

### 1. Agent 创建模式

每个 Agent 都遵循相同的创建模式：

```python
def create_agent_name(llm, [other_params]):
    def agent_node(state):
        # 1. 从状态中获取数据
        # 2. 定义工具
        # 3. 定义系统提示词
        # 4. 创建提示词模板
        # 5. 创建 LLM 链
        # 6. 执行链并返回结果
        return {"messages": [result], "state_key": value}
    return agent_node
```

### 2. Agent 类型

#### 2.1 分析师代理 (Analysts)

- **市场分析师 (Market Analyst)**: 分析技术指标和市场趋势
- **社交媒体分析师 (Social Media Analyst)**: 分析社交媒体情绪
- **新闻分析师 (News Analyst)**: 分析新闻和内幕信息
- **基本面分析师 (Fundamentals Analyst)**: 分析公司财务数据

#### 2.2 研究员代理 (Researchers)

- **看多研究员 (Bull Researcher)**: 从乐观角度分析投资机会
- **看空研究员 (Bear Researcher)**: 从谨慎角度分析风险
- **研究管理器 (Research Manager)**: 协调辩论并做出判断

#### 2.3 交易员代理 (Trader)

- **交易员 (Trader)**: 综合所有分析结果，做出交易决策

#### 2.4 风险管理代理 (Risk Management)

- **激进辩论者 (Aggressive Debator)**: 支持高风险高回报策略
- **保守辩论者 (Conservative Debator)**: 支持低风险策略
- **中性辩论者 (Neutral Debator)**: 平衡风险和回报
- **风险管理器 (Risk Manager)**: 评估整体风险并做出最终判断

## Prompt 组织方式

### 1. 系统提示词 (System Message)

每个 Agent 都有专门的系统提示词，定义其角色和职责。例如市场分析师的系统提示词包括：

- 角色定义
- 可用工具说明
- 具体任务要求
- 输出格式要求

### 2. 提示词模板 (Prompt Template)

使用 `ChatPromptTemplate` 构建完整的提示词：

```python
prompt = ChatPromptTemplate.from_messages([
    ("system", "系统提示词内容"),
    MessagesPlaceholder(variable_name="messages"),
])
```

### 3. 部分参数 (Partial Parameters)

使用 `partial` 方法预设固定参数：

```python
prompt = prompt.partial(system_message=system_message)
prompt = prompt.partial(tool_names=", ".join([tool.name for tool in tools]))
```

## 工具调用 (Tool Calling)

### 1. 工具定义

工具是普通的 Python 函数，使用装饰器或直接定义：

```python
@tool
def get_stock_data(ticker: str, date: str):
    """获取股票数据"""
    # 实现
```

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

使用 `ConditionalLogic` 类控制流程：

```python
workflow.add_conditional_edges(
    "Market Analyst",
    conditional_logic.should_continue_market,
    ["tools_market", "Msg Clear Market"],
)
```

## 状态管理

### 1. 状态定义

使用 `TypedDict` 定义状态结构：

```python
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    company_of_interest: str
    trade_date: str
    market_report: str
    # ... 其他字段
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
2. **分析师阶段**: 各分析师依次执行，分析不同维度的数据
3. **研究员辩论**: 看多和看空研究员进行多轮辩论
4. **研究管理器判断**: 研究管理器评估辩论结果
5. **交易员决策**: 交易员根据所有分析做出交易决策
6. **风险评估**: 风险管理团队评估风险
7. **最终决策**: 风险管理器做出最终判断

## Skill、Tool、MCP、SubAgent 的区别

### 1. Tool (工具)

**定义**: 单个可执行的函数，用于完成特定任务

**特点**:
- 简单、单一职责
- 由 LLM 直接调用
- 同步执行
- 返回结构化数据

**示例**:
```python
get_stock_data(ticker, date)  # 获取股票数据
get_indicators(ticker, indicators)  # 获取技术指标
```

### 2. Skill (技能)

**定义**: 多个 Tool 的组合，用于完成复杂任务

**特点**:
- 组合多个 Tool
- 有自己的控制流程
- 可以有内部状态
- 更高层次的抽象

**注意**: 当前 TradingAgents 项目中没有显式使用 Skill 概念，直接使用 Tool。

### 3. MCP (Model Context Protocol)

**定义**: 一种协议，用于连接 AI 助手与外部数据源和工具

**特点**:
- 标准化接口
- 跨平台兼容
- 可发现的工具和资源
- 安全的权限模型

**注意**: 当前 TradingAgents 项目中没有使用 MCP。

### 4. SubAgent (子代理)

**定义**: 在一个 Agent 内部调用另一个 Agent

**特点**:
- 模块化设计
- 递归调用
- 可以有自己的状态和工具
- 适合复杂任务分解

**注意**: 当前 TradingAgents 项目中没有显式使用 SubAgent 概念，所有 Agent 都是图中的独立节点。

## 代码示例

### 创建自定义 Agent

```python
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool

@tool
def my_custom_tool(param: str) -> str:
    """自定义工具描述"""
    return f"处理结果: {param}"

def create_my_agent(llm):
    def my_agent_node(state):
        tools = [my_custom_tool]
        
        system_message = """你是一个自定义代理..."""
        
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
    
    return my_agent_node
```

## 最佳实践

1. **单一职责**: 每个 Agent 应该专注于一个特定任务
2. **清晰的提示词**: 提供详细的角色定义和任务说明
3. **工具设计**: 工具应该简单、可组合、有良好的文档
4. **状态管理**: 明确哪些状态字段需要更新
5. **错误处理**: 在工具中添加适当的错误处理
6. **日志记录**: 记录关键决策和中间结果
7. **测试**: 独立测试每个 Agent 和工具
