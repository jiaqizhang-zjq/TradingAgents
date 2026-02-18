# 社交媒体数据获取指南

## 📋 概述

本指南介绍如何在 TradingAgents 项目中使用社交媒体数据，包括 X（原 Twitter）和 Reddit。

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install praw tweepy
```

### 2. 获取 API 凭证

#### Reddit
1. 访问 [Reddit Apps](https://www.reddit.com/prefs/apps)
2. 点击 "Create App" 或 "Create Another App"
3. 选择 "script" 类型
4. 填写必要信息
5. 获取：
   - `REDDIT_CLIENT_ID` (应用 ID)
   - `REDDIT_CLIENT_SECRET` (密钥)

#### X (Twitter)
1. 访问 [Twitter Developer Portal](https://developer.twitter.com/)
2. 创建项目和应用
3. 获取 Bearer Token
4. 设置环境变量 `TWITTER_BEARER_TOKEN`

### 3. 配置环境变量

编辑 `.env` 文件：

```env
# Reddit API
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret
REDDIT_USER_AGENT=TradingAgents/1.0

# X (Twitter) API
TWITTER_BEARER_TOKEN=your_bearer_token
```

## 📊 使用方法

### 获取 Reddit 帖子

```python
from tradingagents.dataflows.social_media import get_reddit_posts

# 获取 wallstreetbets 的热门帖子
posts_json = get_reddit_posts(
    subreddit="wallstreetbets",
    limit=20,
    sort_by="hot"
)

# 搜索特定股票
posts_json = get_reddit_posts(
    subreddit="stocks",
    query="NVDA",
    limit=10
)
```

### 获取 X (Twitter) 推文

```python
from tradingagents.dataflows.social_media import get_twitter_tweets

# 搜索股票相关推文
tweets_json = get_twitter_tweets(
    query="$NVDA OR NVIDIA stock",
    limit=20
)
```

### 获取股票在社交媒体上的提及（推荐）

```python
from tradingagents.dataflows.social_media import get_stock_mentions

# 同时从 Reddit 和 Twitter 获取股票提及
social_data_json = get_stock_mentions(
    symbol="NVDA",
    platforms=["reddit", "twitter"],
    limit=20
)
```

## 🎯 支持的平台

### Reddit
- ✅ 获取子版块帖子
- ✅ 搜索功能
- ✅ 多种排序方式（hot, new, top, rising）
- ✅ 支持多个财经子版块：
  - wallstreetbets
  - stocks
  - investing
  - stockmarket

### X (Twitter)
- ✅ 搜索推文
- ✅ 获取用户信息
- ✅ 时间范围过滤
- ✅ 推文指标（点赞、转发、回复）

## 📝 数据格式

### Reddit 帖子数据
```json
[
  {
    "id": "post_id",
    "title": "帖子标题",
    "author": "作者",
    "score": 1234,
    "num_comments": 567,
    "created_utc": "2026-02-18T12:00:00",
    "url": "https://...",
    "selftext": "帖子内容",
    "subreddit": "wallstreetbets"
  }
]
```

### X (Twitter) 推文数据
```json
[
  {
    "id": "tweet_id",
    "text": "推文内容",
    "author_username": "username",
    "author_name": "User Name",
    "created_at": "2026-02-18T12:00:00",
    "retweet_count": 100,
    "reply_count": 50,
    "like_count": 500,
    "quote_count": 10,
    "lang": "en"
  }
]
```

## ⚠️ 注意事项

### 免费额度限制

#### Reddit
- ✅ 相对宽松的免费额度
- 建议适度使用，避免被限流

#### X (Twitter)
- ❌ 免费版限制较多
- 只能获取最近7天的推文
- 每月搜索数量有限制
- 建议申请 Elevated Access 获取更多配额

### 数据质量
- 社交媒体数据可能包含噪音
- 建议进行数据清洗和过滤
- 考虑使用情绪分析工具处理

## 🔒 安全建议

1. 不要将 API 密钥提交到版本控制
2. 使用环境变量存储凭证
3. 定期轮换 API 密钥
4. 监控 API 使用量

## 📚 相关链接

- [Reddit API 文档](https://www.reddit.com/dev/api/)
- [PRAW 文档](https://praw.readthedocs.io/)
- [Twitter API 文档](https://developer.twitter.com/en/docs)
- [Tweepy 文档](https://docs.tweepy.org/)
