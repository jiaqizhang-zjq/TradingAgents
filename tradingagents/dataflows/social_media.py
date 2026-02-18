# TradingAgents/dataflows/social_media.py
"""
社交媒体数据获取模块
支持 X（Twitter）和 Reddit
"""

import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from .api_config import get_api_config

try:
    import praw
    HAS_PRAW = True
except ImportError:
    HAS_PRAW = False
    print("警告: 未安装 praw，请运行: pip install praw")

try:
    import tweepy
    HAS_TWEEPY = True
except ImportError:
    HAS_TWEEPY = False
    print("警告: 未安装 tweepy，请运行: pip install tweepy")


class SocialMediaAPI:
    """社交媒体API封装类"""
    
    def __init__(self):
        self.reddit_client = None
        self.twitter_client = None
        self.initialized = False
        
    def _initialize_reddit(self):
        """初始化 Reddit 客户端"""
        if not HAS_PRAW:
            raise ImportError("praw 未安装")
            
        # 从统一配置获取
        api_config = get_api_config()
        client_id = api_config.reddit_client_id
        client_secret = api_config.reddit_client_secret
        user_agent = api_config.reddit_user_agent
        
        if not all([client_id, client_secret]):
            raise ValueError("请设置 REDDIT_CLIENT_ID 和 REDDIT_CLIENT_SECRET 环境变量")
            
        self.reddit_client = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent
        )
        
    def _initialize_twitter(self):
        """初始化 X (Twitter) 客户端"""
        if not HAS_TWEEPY:
            raise ImportError("tweepy 未安装")
            
        # 从统一配置获取
        api_config = get_api_config()
        bearer_token = api_config.twitter_bearer_token
        
        if not bearer_token:
            raise ValueError("请设置 TWITTER_BEARER_TOKEN 环境变量")
            
        self.twitter_client = tweepy.Client(bearer_token=bearer_token)
        
    def get_reddit_posts(
        self,
        subreddit: str = "wallstreetbets",
        query: Optional[str] = None,
        limit: int = 20,
        sort_by: str = "hot"
    ) -> str:
        """
        获取 Reddit 帖子
        
        Args:
            subreddit: 子版块名称
            query: 搜索关键词（可选）
            limit: 返回数量
            sort_by: 排序方式 (hot, new, top, rising)
            
        Returns:
            JSON 格式的帖子数据
        """
        self._initialize_reddit()
        
        subreddit_obj = self.reddit_client.subreddit(subreddit)
        
        posts = []
        
        if query:
            # 使用搜索
            for submission in subreddit_obj.search(query, limit=limit, sort=sort_by):
                posts.append({
                    "id": submission.id,
                    "title": submission.title,
                    "author": str(submission.author) if submission.author else None,
                    "score": submission.score,
                    "num_comments": submission.num_comments,
                    "created_utc": datetime.fromtimestamp(submission.created_utc).isoformat(),
                    "url": submission.url,
                    "selftext": submission.selftext,
                    "subreddit": subreddit
                })
        else:
            # 获取排序的帖子
            if sort_by == "hot":
                submissions = subreddit_obj.hot(limit=limit)
            elif sort_by == "new":
                submissions = subreddit_obj.new(limit=limit)
            elif sort_by == "top":
                submissions = subreddit_obj.top(limit=limit)
            elif sort_by == "rising":
                submissions = subreddit_obj.rising(limit=limit)
            else:
                submissions = subreddit_obj.hot(limit=limit)
                
            for submission in submissions:
                posts.append({
                    "id": submission.id,
                    "title": submission.title,
                    "author": str(submission.author) if submission.author else None,
                    "score": submission.score,
                    "num_comments": submission.num_comments,
                    "created_utc": datetime.fromtimestamp(submission.created_utc).isoformat(),
                    "url": submission.url,
                    "selftext": submission.selftext,
                    "subreddit": subreddit
                })
                
        return json.dumps(posts, indent=2)
    
    def get_twitter_tweets(
        self,
        query: str,
        limit: int = 20,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None
    ) -> str:
        """
        获取 X (Twitter) 推文
        
        Args:
            query: 搜索查询
            limit: 返回数量
            start_time: 开始时间 (ISO格式)
            end_time: 结束时间 (ISO格式)
            
        Returns:
            JSON 格式的推文数据
        """
        self._initialize_twitter()
        
        tweet_fields = ["created_at", "author_id", "public_metrics", "lang"]
        expansions = ["author_id"]
        user_fields = ["username", "name"]
        
        params = {
            "query": query,
            "max_results": min(limit, 100),
            "tweet.fields": tweet_fields,
            "expansions": expansions,
            "user.fields": user_fields
        }
        
        if start_time:
            params["start_time"] = start_time
        if end_time:
            params["end_time"] = end_time
            
        response = self.twitter_client.search_recent_tweets(**params)
        
        tweets = []
        if response.data:
            # 创建用户字典
            users = {u.id: u for u in response.includes.get("users", [])}
            
            for tweet in response.data:
                author = users.get(tweet.author_id)
                tweets.append({
                    "id": tweet.id,
                    "text": tweet.text,
                    "author_username": author.username if author else None,
                    "author_name": author.name if author else None,
                    "created_at": tweet.created_at.isoformat() if tweet.created_at else None,
                    "retweet_count": tweet.public_metrics.get("retweet_count", 0),
                    "reply_count": tweet.public_metrics.get("reply_count", 0),
                    "like_count": tweet.public_metrics.get("like_count", 0),
                    "quote_count": tweet.public_metrics.get("quote_count", 0),
                    "lang": tweet.lang
                })
                
        return json.dumps(tweets, indent=2)
    
    def get_stock_mentions(
        self,
        symbol: str,
        platforms: List[str] = ["reddit", "twitter"],
        limit: int = 20
    ) -> str:
        """
        获取股票在社交媒体上的提及
        
        Args:
            symbol: 股票代码
            platforms: 平台列表 (reddit, twitter)
            limit: 每个平台返回数量
            
        Returns:
            JSON 格式的社交媒体数据
        """
        results = {
            "symbol": symbol,
            "collected_at": datetime.now().isoformat(),
            "data": {}
        }
        
        if "reddit" in platforms:
            try:
                # 搜索多个相关子版块
                subreddits = ["wallstreetbets", "stocks", "investing", "stockmarket"]
                reddit_posts = []
                for subreddit in subreddits:
                    try:
                        posts_json = self.get_reddit_posts(
                            subreddit=subreddit,
                            query=symbol,
                            limit=limit // len(subreddits)
                        )
                        reddit_posts.extend(json.loads(posts_json))
                    except Exception:
                        continue
                results["data"]["reddit"] = reddit_posts
            except Exception as e:
                results["data"]["reddit"] = {"error": str(e)}
                
        if "twitter" in platforms:
            try:
                tweets_json = self.get_twitter_tweets(
                    query=f"${symbol} OR {symbol} stock",
                    limit=limit
                )
                results["data"]["twitter"] = json.loads(tweets_json)
            except Exception as e:
                results["data"]["twitter"] = {"error": str(e)}
                
        return json.dumps(results, indent=2)


# 全局实例
_social_media_api = None


def get_social_media_api() -> SocialMediaAPI:
    """获取社交媒体API实例（单例）"""
    global _social_media_api
    if _social_media_api is None:
        _social_media_api = SocialMediaAPI()
    return _social_media_api


# ==================== 导出函数 ====================

def get_reddit_posts(
    subreddit: str = "wallstreetbets",
    query: Optional[str] = None,
    limit: int = 20,
    sort_by: str = "hot"
) -> str:
    """获取 Reddit 帖子"""
    api = get_social_media_api()
    return api.get_reddit_posts(subreddit, query, limit, sort_by)


def get_twitter_tweets(
    query: str,
    limit: int = 20,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None
) -> str:
    """获取 X (Twitter) 推文"""
    api = get_social_media_api()
    return api.get_twitter_tweets(query, limit, start_time, end_time)


def get_stock_mentions(
    symbol: str,
    platforms: List[str] = ["reddit", "twitter"],
    limit: int = 20
) -> str:
    """获取股票在社交媒体上的提及"""
    api = get_social_media_api()
    return api.get_stock_mentions(symbol, platforms, limit)
