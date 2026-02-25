"""Financial situation memory using BM25 for lexical similarity matching.

Uses BM25 (Best Matching 25) algorithm for retrieval - no API calls,
no token limits, works offline with any LLM provider.
"""

from rank_bm25 import BM25Okapi
from typing import List, Tuple, Optional, Dict, Any
import re
import os
import sqlite3
import json
from datetime import datetime
from contextlib import contextmanager


class FinancialSituationMemory:
    """Memory system for storing and retrieving financial situations using BM25."""

    def __init__(self, name: str, config: dict = None):
        """Initialize the memory system.

        Args:
            name: Name identifier for this memory instance
            config: Configuration dict (kept for API compatibility, not used for BM25)
        """
        self.name = name
        self.documents: List[str] = []
        self.recommendations: List[str] = []
        self.returns: List[float] = []
        self.bm25 = None
        self.db_path = "tradingagents/db/research_tracker.db"
        
        if config:
            self.db_path = config.get("db_path", self.db_path)
        
        self._init_database()
        self.load_from_db()

    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text for BM25 indexing.

        Simple whitespace + punctuation tokenization with lowercasing.
        """
        # Lowercase and split on non-alphanumeric characters
        tokens = re.findall(r'\b\w+\b', text.lower())
        return tokens

    @contextmanager
    def _get_connection(self):
        """获取数据库连接上下文管理器"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def _init_database(self):
        """初始化数据库表结构"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # 内存记录表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS memory_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    memory_name TEXT NOT NULL,
                    situation TEXT NOT NULL,
                    recommendation TEXT NOT NULL,
                    actual_return REAL,
                    symbol TEXT,
                    trade_date TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    
                    UNIQUE(memory_name, situation)
                )
            ''')
            
            # 创建索引
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_memory_records_memory_name 
                ON memory_records(memory_name)
            ''')
            
            conn.commit()

    def _rebuild_index(self):
        """Rebuild the BM25 index after adding documents."""
        if self.documents:
            tokenized_docs = [self._tokenize(doc) for doc in self.documents]
            self.bm25 = BM25Okapi(tokenized_docs)
        else:
            self.bm25 = None

    def add_situations(self, situations_and_advice: List[Tuple[str, str, float]]):
        """Add financial situations and their corresponding advice with returns.

        Args:
            situations_and_advice: List of tuples (situation, recommendation, return)
        """
        for situation, recommendation, return_value in situations_and_advice:
            self.documents.append(situation)
            self.recommendations.append(recommendation)
            self.returns.append(return_value)

        # Rebuild BM25 index with new documents
        self._rebuild_index()
        
        # 保存到数据库
        self.save_to_db()

    def get_memories(self, current_situation: str, n_matches: int = 1) -> List[dict]:
        """Find matching recommendations using BM25 similarity.

        Args:
            current_situation: The current financial situation to match against
            n_matches: Number of top matches to return

        Returns:
            List of dicts with matched_situation, recommendation, similarity_score, and actual_return
        """
        if not self.documents or self.bm25 is None:
            return []

        # Tokenize query
        query_tokens = self._tokenize(current_situation)

        # Get BM25 scores for all documents
        scores = self.bm25.get_scores(query_tokens)

        # Get top-n indices sorted by score (descending)
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:n_matches]

        # Build results
        results = []
        max_score = max(scores) if max(scores) > 0 else 1  # Normalize scores

        for idx in top_indices:
            # Normalize score to 0-1 range for consistency
            normalized_score = scores[idx] / max_score if max_score > 0 else 0
            results.append({
                "matched_situation": self.documents[idx],
                "recommendation": self.recommendations[idx],
                "similarity_score": normalized_score,
                "actual_return": self.returns[idx] if idx < len(self.returns) else None,
            })

        return results

    def save_to_db(self):
        """Save current memory data to database."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                now = datetime.now().isoformat()
                
                for i, (situation, recommendation, return_value) in enumerate(zip(
                    self.documents, 
                    self.recommendations, 
                    self.returns
                )):
                    cursor.execute('''
                        INSERT OR REPLACE INTO memory_records (
                            memory_name, situation, recommendation, actual_return, 
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        self.name,
                        situation,
                        recommendation,
                        return_value,
                        now,
                        now
                    ))
                
                conn.commit()
                print(f"✅ Memory {self.name} 已保存到数据库: {len(self.documents)} 条记录")
        except Exception as e:
            print(f"❌ 保存内存到数据库失败: {e}")

    def load_from_db(self):
        """Load memory data from database."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT situation, recommendation, actual_return 
                    FROM memory_records 
                    WHERE memory_name = ?
                    ORDER BY id
                ''', (self.name,))
                
                rows = cursor.fetchall()
                
                self.documents = []
                self.recommendations = []
                self.returns = []
                
                for row in rows:
                    self.documents.append(row[0])
                    self.recommendations.append(row[1])
                    self.returns.append(row[2] if row[2] is not None else 0.0)
                
                # Rebuild BM25 index
                self._rebuild_index()
                
                if self.documents:
                    print(f"✅ Memory {self.name} 从数据库加载: {len(self.documents)} 条记录")
        except Exception as e:
            print(f"❌ 从数据库加载内存失败: {e}")

    def update_from_backtest(self, symbol: str, trade_date: str, situation: str, 
                           recommendation: str, actual_return: float):
        """Update memory from backtest results.

        Args:
            symbol: Stock symbol
            trade_date: Trade date
            situation: Financial situation description
            recommendation: Action taken
            actual_return: Actual return achieved
        """
        # Add to in-memory storage
        self.documents.append(situation)
        self.recommendations.append(recommendation)
        self.returns.append(actual_return)
        
        # Rebuild index
        self._rebuild_index()
        
        # Save to database
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                now = datetime.now().isoformat()
                
                cursor.execute('''
                    INSERT OR REPLACE INTO memory_records (
                        memory_name, situation, recommendation, actual_return, 
                        symbol, trade_date, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    self.name,
                    situation,
                    recommendation,
                    actual_return,
                    symbol,
                    trade_date,
                    now,
                    now
                ))
                
                conn.commit()
                print(f"✅ Memory {self.name} 从回测更新: {symbol} @ {trade_date}, 收益: {actual_return:.2%}")
        except Exception as e:
            print(f"❌ 从回测更新内存失败: {e}")

    def clear(self):
        """Clear all stored memories."""
        self.documents = []
        self.recommendations = []
        self.returns = []
        self.bm25 = None
        
        # 清除数据库中的记录
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    DELETE FROM memory_records WHERE memory_name = ?
                ''', (self.name,))
                conn.commit()
                print(f"✅ Memory {self.name} 已清空")
        except Exception as e:
            print(f"❌ 清空内存失败: {e}")

    def learn_from_research_records(self, limit: int = 100):
        """Learn from verified research records in database, combining with analysis reports.
        
        Args:
            limit: Maximum number of records to learn from
        """
        try:
            import sqlite3
            
            # 先检查内存中已有的记录，避免重复
            existing_situations = set(self.documents)
            
            count = 0
            
            # 从research_records表中获取已验证的记录
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT symbol, trade_date, prediction, reasoning, actual_return 
                    FROM research_records 
                    WHERE outcome != 'pending' 
                    AND actual_return IS NOT NULL
                    AND researcher_name = ?
                    ORDER BY verified_date DESC
                    LIMIT ?
                ''', (self.name, limit))
                
                research_rows = cursor.fetchall()
            
            # 从analysis_reports表中获取完整的市场报告
            analysis_db_path = "tradingagents/db/trading_analysis.db"
            if os.path.exists(analysis_db_path):
                analysis_conn = sqlite3.connect(analysis_db_path)
                analysis_conn.row_factory = sqlite3.Row
                
                try:
                    analysis_cursor = analysis_conn.cursor()
                    
                    for row in research_rows:
                        symbol, trade_date, prediction, reasoning, actual_return = row
                        
                        if not reasoning or not reasoning.strip():
                            continue
                        
                        # 尝试从analysis_reports表获取完整市场报告
                        full_market_situation = reasoning  # 默认用单个研究员的推理
                        
                        try:
                            analysis_cursor.execute('''
                                SELECT market_report, sentiment_report, news_report, 
                                       fundamentals_report, candlestick_report
                                FROM analysis_reports 
                                WHERE symbol = ? AND trade_date = ?
                            ''', (symbol, trade_date))
                            
                            analysis_row = analysis_cursor.fetchone()
                            
                            if analysis_row:
                                # 构建完整的市场情境
                                market_report = analysis_row[0] or ""
                                sentiment_report = analysis_row[1] or ""
                                news_report = analysis_row[2] or ""
                                fundamentals_report = analysis_row[3] or ""
                                candlestick_report = analysis_row[4] or ""
                                
                                full_market_situation = (
                                    f"股票: {symbol}, 日期: {trade_date}\n"
                                    f"--- 市场报告 ---\n{market_report}\n\n"
                                    f"--- 情绪报告 ---\n{sentiment_report}\n\n"
                                    f"--- 新闻报告 ---\n{news_report}\n\n"
                                    f"--- 基本面报告 ---\n{fundamentals_report}\n\n"
                                    f"--- 蜡烛图报告 ---\n{candlestick_report}"
                                )
                        except Exception as e:
                            # 如果获取完整报告失败，就用单个研究员的推理
                            pass
                        
                        # 避免重复添加
                        if full_market_situation in existing_situations:
                            continue
                        
                        # 构建建议 - 明确标识预测者角色
                        role_name = self.name.replace("_", " ").title()
                        recommendation = (
                            f"角色: {role_name}\n"
                            f"预测: {prediction}\n"
                            f"推理: {reasoning[:1000]}...\n"
                            f"实际收益: {actual_return:.2%}"
                        )
                        
                        self.documents.append(full_market_situation)
                        self.recommendations.append(recommendation)
                        self.returns.append(actual_return)
                        existing_situations.add(full_market_situation)
                        count += 1
                
                finally:
                    analysis_conn.close()
            else:
                # 如果没有analysis_reports表，只用research_records的数据
                for row in research_rows:
                    symbol, trade_date, prediction, reasoning, actual_return = row
                    
                    if not reasoning or not reasoning.strip():
                        continue
                    
                    situation = f"股票: {symbol}, 日期: {trade_date}\n{reasoning}"
                    
                    if situation in existing_situations:
                        continue
                    
                    role_name = self.name.replace("_", " ").title()
                    recommendation = (
                        f"角色: {role_name}\n"
                        f"预测: {prediction}\n"
                        f"实际收益: {actual_return:.2%}"
                    )
                    
                    self.documents.append(situation)
                    self.recommendations.append(recommendation)
                    self.returns.append(actual_return)
                    existing_situations.add(situation)
                    count += 1
            
            # 重建BM25索引
            if count > 0:
                self._rebuild_index()
                self.save_to_db()
                print(f"✅ Memory {self.name} 从研究记录学习了 {count} 条新记录")
            else:
                print(f"⏭️  Memory {self.name} 没有新的研究记录需要学习")
        except Exception as e:
            print(f"❌ 从研究记录学习失败: {e}")
            import traceback
            print(f"   错误详情: {traceback.format_exc()}")


if __name__ == "__main__":
    # Example usage
    matcher = FinancialSituationMemory("test_memory")

    # Example data
    example_data = [
        (
            "High inflation rate with rising interest rates and declining consumer spending",
            "Consider defensive sectors like consumer staples and utilities. Review fixed-income portfolio duration.",
        ),
        (
            "Tech sector showing high volatility with increasing institutional selling pressure",
            "Reduce exposure to high-growth tech stocks. Look for value opportunities in established tech companies with strong cash flows.",
        ),
        (
            "Strong dollar affecting emerging markets with increasing forex volatility",
            "Hedge currency exposure in international positions. Consider reducing allocation to emerging market debt.",
        ),
        (
            "Market showing signs of sector rotation with rising yields",
            "Rebalance portfolio to maintain target allocations. Consider increasing exposure to sectors benefiting from higher rates.",
        ),
    ]

    # Add the example situations and recommendations
    matcher.add_situations(example_data)

    # Example query
    current_situation = """
    Market showing increased volatility in tech sector, with institutional investors
    reducing positions and rising interest rates affecting growth stock valuations
    """

    try:
        recommendations = matcher.get_memories(current_situation, n_matches=2)

        for i, rec in enumerate(recommendations, 1):
            print(f"\nMatch {i}:")
            print(f"Similarity Score: {rec['similarity_score']:.2f}")
            print(f"Matched Situation: {rec['matched_situation']}")
            print(f"Recommendation: {rec['recommendation']}")

    except Exception as e:
        print(f"Error during recommendation: {str(e)}")
