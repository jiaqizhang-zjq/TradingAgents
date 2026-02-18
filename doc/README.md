# TradingAgents 文档阅读指南

欢迎阅读 TradingAgents 项目文档！这里是文档的阅读顺序推荐，帮助您循序渐进地理解项目。

## 📖 推荐阅读顺序

### 第一步：了解项目整体架构

**[architecture.md](architecture.md)** - 项目框架文档

阅读这个文档可以帮助您：
- 了解项目的整体目录结构
- 熟悉各个模块的功能和职责
- 理解核心工作流程
- 掌握技术栈和扩展性

这是入门的最佳起点，让您对项目有一个宏观的认识。

---

### 第二步：理解 LLM 调用流程

**[llm_call_chain.md](llm_call_chain.md)** - LLM 相关的函数调用关系链

阅读这个文档可以帮助您：
- 了解 LLM 客户端是如何创建的
- 掌握 LLM 在系统中的使用方式
- 理解工具调用的机制
- 熟悉数据流向

在了解项目架构后，深入理解 LLM 这一核心组件的工作原理。

---

### 第三步：掌握 Agent 的使用

**[agents_guide.md](agents_guide.md)** - Agent 用法和解析指南

阅读这个文档可以帮助您：
- 理解 Agent 的创建模式
- 掌握 Prompt 的组织方式
- 学习工具调用的具体实现
- 了解 Graph 的组织方式
- 区分 Tool、Skill、MCP、SubAgent 的概念

这是最详细的实操指南，包含代码示例和最佳实践。

---

### （可选）使用长桥 API

**[longbridge_guide.md](longbridge_guide.md)** - 长桥（Longbridge）API 使用指南

如果您只有长桥接口，需要替换 Alpha Vantage 和 Yahoo Finance，请阅读此文档：
- 长桥 SDK 安装和配置
- API 凭证获取
- 如何切换数据源
- 功能说明和自定义实现

---

## 📚 文档速查表

| 文档 | 内容概览 | 难度 | 阅读时长 |
|------|---------|------|---------|
| [architecture.md](architecture.md) | 项目架构、模块说明、技术栈 | ⭐ 入门 | 10-15 分钟 |
| [llm_call_chain.md](llm_call_chain.md) | LLM 调用流程、配置参数、数据流向 | ⭐⭐ 进阶 | 15-20 分钟 |
| [agents_guide.md](agents_guide.md) | Agent 创建、Prompt 组织、工具调用、Graph 组织 | ⭐⭐⭐ 深入 | 25-35 分钟 |
| [api_config_guide.md](api_config_guide.md) | 统一 API 配置管理 | ⭐ 入门 | 5-10 分钟 |
| [longbridge_guide.md](longbridge_guide.md) | 长桥 API 配置和使用 | ⭐⭐ 进阶 | 10-15 分钟 |
| [social_media_guide.md](social_media_guide.md) | 社交媒体数据（X/Twitter、Reddit） | ⭐⭐ 进阶 | 10-15 分钟 |

## 💡 阅读建议

1. **首次阅读**：按照推荐顺序完整阅读所有文档
2. **代码开发**：根据需要查阅特定文档
3. **问题排查**：先查看对应模块的文档，再查看代码注释
4. **二次阅读**：可以直接从感兴趣的部分开始

## 🔗 相关资源

- 项目根目录的 [README.md](../README.md) - 项目概览和快速开始
- `tradingagents/default_config.py` - 配置文件说明
- `tradingagents/graph/trading_graph.py` - 核心实现代码

## 📝 备注

- 所有文档都包含中文注释，方便理解
- 关键代码位置都有标注，可直接跳转查看
- 如有疑问，欢迎查阅代码或提交 Issue

祝您阅读愉快！🎉
