# 内存系统设计文档

## 概述

本文档描述 TradingAgents 系统中的内存系统设计，包括内存的结构、工作原理、持久化机制以及与回测系统的集成。

## 内存系统架构

### 核心组件

- **FinancialSituationMemory**：内存核心类，使用 BM25 算法进行相似性匹配
- **memory_records 表**：持久化存储内存数据的数据库表
- **回测集成**：回测完成后自动更新内存

### 数据流向

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ 股票分析      │     │ 回测验证      │     │ 内存更新      │
│ (analysis_reports) │────►│ (research_records) │────►│ (memory_records) │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        ▲                         ▲                         │
        │                         │                         │
        └─────────────────────────┼─────────────────────────┘
                                  │
                          ┌─────────────────┐
                          │ 系统启动加载   │
                          └─────────────────┘
```

## 内存数据结构

### 1. 内存实例

每个角色都有独立的内存实例：

| 内存实例 | 对应角色 | 说明 |
|---------|---------|------|
| bull_memory | bull_researcher | 看涨研究员内存 |
| bear_memory | bear_researcher | 看跌研究员内存 |
| trader_memory | trader | 交易员内存 |
| invest_judge_memory | research_manager | 研究经理内存 |
| risk_manager_memory | risk_manager | 风险经理内存 |

### 2. 内存条目结构

每个内存条目包含三个核心部分：

- **Situation（情境）**：完整的市场情境描述，包含5份专家报告
  - 市场报告
  - 情绪报告
  - 新闻报告
  - 基本面报告
  - 蜡烛图报告
  - 股票代码和日期信息

- **Recommendation（建议）**：包含
  - 角色标识（如 "Bull Researcher"）
  - 预测结果（BUY/SELL/HOLD）
  - 推理过程（最多1000字）
  - 实际收益（百分比）

- **Return（收益）**：实际收益率（用于排序和学习）

## 工作流程

### 1. 初始化阶段

- 系统启动时，每个内存实例从 `memory_records` 表加载历史数据
- 构建 BM25 索引，为相似性匹配做准备

### 2. 分析阶段

- 分析师基于当前市场情境生成预测
- 预测结果保存到 `research_records` 表
- 完整市场报告保存到 `analysis_reports` 表

### 3. 回测阶段

- 回测系统验证历史预测
- 更新 `research_records` 表的 `actual_return` 和 `outcome`
- 触发内存更新：从双表关联数据学习到内存
- 内存数据保存到 `memory_records` 表

### 4. 决策阶段

- 分析师在决策时，使用内存中的历史经验
- 通过 BM25 算法找到最相似的历史情境
- 参考历史建议和收益，辅助当前决策

## 技术实现

### 1. 相似性匹配

使用 BM25 算法进行文本相似性匹配：
- 基于词频和文档长度计算相关性
- 无需 API 调用，离线运行
- 支持中文和英文文本

### 2. 持久化机制

- 内存数据自动保存到 `memory_records` 表
- 系统重启后自动加载
- 避免重复数据，确保数据一致性

### 3. 回测集成

- 回测完成后自动调用 `learn_from_research_records()`
- 从 `research_records` 和 `analysis_reports` 表关联数据
- 构建完整的（情境 + 建议 + 收益）三元组

## 配置与使用

### 配置选项

- **db_path**：数据库路径（默认：`tradingagents/db/research_tracker.db`）
- **limit**：学习记录数量限制（默认：100）

### 使用示例

```python
# 初始化内存实例
memory = FinancialSituationMemory("bull_researcher", config)

# 从数据库学习历史记录
memory.learn_from_research_records()

# 查询相似情境
current_situation = "特斯拉股票表现强劲..."
results = memory.get_memories(current_situation, n_matches=3)

# 查看结果
for result in results:
    print(f"相似性: {result['similarity_score']:.2f}")
    print(f"情境: {result['matched_situation'][:100]}...")
    print(f"建议: {result['recommendation']}")
    print(f"收益: {result['actual_return']:.2%}")
```

## 性能优化

- **增量学习**：只学习新的、未见过的记录
- **索引重建**：仅在添加新数据时重建 BM25 索引
- **内存管理**：支持清空内存和重新加载

## 扩展建议

- **多语言支持**：增加多语言分词支持
- **深度学习**：考虑使用嵌入模型替代 BM25
- **增量更新**：实现实时增量更新机制
- **记忆质量评估**：添加记忆质量评估和过滤机制

## 更新日志

- 2026-02-24：初始版本，实现基本内存系统功能
- 2026-02-24：添加数据库持久化和回测集成
- 2026-02-24：优化相似性匹配和数据结构
