# API 配置管理指南

## 📋 概述

TradingAgents 使用统一的 API 配置管理系统，集中管理所有 API 密钥和配置。

## 🚀 快速开始

### 1. 配置环境变量

复制 `.env.example` 为 `.env`：

```bash
cp .env.example .env
```

编辑 `.env` 文件，填入您的 API 密钥：

```env
# LLM Providers
OPENAI_API_KEY=your_openai_key
GOOGLE_API_KEY=your_google_key
ANTHROPIC_API_KEY=your_anthropic_key

# Data Providers
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key

# Longbridge
LONGBRIDGE_APP_KEY=your_app_key
LONGBRIDGE_APP_SECRET=your_app_secret
LONGBRIDGE_ACCESS_TOKEN=your_access_token

# Social Media
REDDIT_CLIENT_ID=your_reddit_id
REDDIT_CLIENT_SECRET=your_reddit_secret
TWITTER_BEARER_TOKEN=your_twitter_token
```

### 2. 检查配置状态

```python
from tradingagents.dataflows.api_config import print_config_summary

print_config_summary()
```

输出示例：
```
==================================================
API 配置摘要
==================================================

LLM 提供商:
  - openai: ✅ 已配置
  - google: ❌ 未配置
  - anthropic: ❌ 未配置
  - xai: ❌ 未配置
  - openrouter: ❌ 未配置

数据提供商:
  - alpha_vantage: ✅ 已配置
  - longbridge: ✅ 已配置

社交媒体:
  - reddit: ✅ 已配置
  - twitter: ❌ 未配置

==================================================
```

## 📊 API 配置类

### APIConfig 数据类

```python
from tradingagents.dataflows.api_config import get_api_config

config = get_api_config()

# 访问配置
print(config.openai_api_key)
print(config.longbridge_app_key)
print(config.reddit_client_id)
```

## 🔧 配置管理函数

### 获取配置
```python
from tradingagents.dataflows.api_config import get_api_config, reload_config

# 获取配置（单例）
config = get_api_config()

# 重新加载配置（修改 .env 后）
reload_config()
config = get_api_config()
```

### 检查配置
```python
from tradingagents.dataflows.api_config import (
    get_config_summary,
    print_config_summary,
    check_required_config
)

# 获取配置摘要字典
summary = get_config_summary()
print(summary["openai"])  # True/False

# 打印配置摘要
print_config_summary()

# 检查必需配置
required = ["openai", "longbridge"]
if check_required_config(required):
    print("所有必需配置已就绪！")
```

## 📝 配置类别

### LLM 提供商
| 配置项 | 说明 |
|--------|------|
| openai_api_key | OpenAI API 密钥 |
| google_api_key | Google API 密钥 |
| anthropic_api_key | Anthropic API 密钥 |
| xai_api_key | xAI (Grok) API 密钥 |
| openrouter_api_key | OpenRouter API 密钥 |

### 数据提供商
| 配置项 | 说明 |
|--------|------|
| alpha_vantage_api_key | Alpha Vantage API 密钥 |
| longbridge_app_key | 长桥 App Key |
| longbridge_app_secret | 长桥 App Secret |
| longbridge_access_token | 长桥 Access Token |

### 社交媒体
| 配置项 | 说明 |
|--------|------|
| reddit_client_id | Reddit Client ID |
| reddit_client_secret | Reddit Client Secret |
| reddit_user_agent | Reddit User Agent |
| twitter_bearer_token | X (Twitter) Bearer Token |

## 🔒 安全建议

1. **不要提交 .env 文件到版本控制**
   - `.gitignore` 已包含 `.env`

2. **使用环境变量**
   - 生产环境建议使用系统环境变量
   - 或者使用密钥管理服务

3. **定期轮换密钥**
   - 定期更新 API 密钥
   - 撤销不再使用的密钥

4. **最小权限原则**
   - 只申请需要的 API 权限
   - 不要使用管理员账号

## 📚 相关文档

- [长桥 API 使用指南](longbridge_guide.md)
- [社交媒体数据指南](social_media_guide.md)
