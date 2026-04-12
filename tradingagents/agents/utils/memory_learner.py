"""Research record learning for FinancialSituationMemory.

Extracts verified research records from the database and builds
situation-recommendation pairs with optional full analysis reports.
"""

import os
import sqlite3
from typing import List, Set, Tuple

from tradingagents.constants import DEFAULT_ANALYSIS_DB_PATH
from tradingagents.agents.utils.memory_storage import get_connection
from tradingagents.utils.logger import get_logger

logger = get_logger(__name__)


def _build_full_situation(analysis_cursor, symbol: str, trade_date: str, 
                          reasoning: str) -> str:
    """Try to build a full market situation from analysis reports.
    
    Falls back to individual researcher reasoning if analysis reports not found.
    
    Args:
        analysis_cursor: SQLite cursor for analysis database
        symbol: 股票代码
        trade_date: 交易日期
        reasoning: 研究员推理（回退值）
        
    Returns:
        Complete market situation string
    """
    try:
        analysis_cursor.execute('''
            SELECT market_report, sentiment_report, news_report, 
                   fundamentals_report, candlestick_report
            FROM analysis_reports 
            WHERE symbol = ? AND trade_date = ?
        ''', (symbol, trade_date))
        
        row = analysis_cursor.fetchone()
        
        if row:
            market_report = row[0] or ""
            sentiment_report = row[1] or ""
            news_report = row[2] or ""
            fundamentals_report = row[3] or ""
            candlestick_report = row[4] or ""
            
            return (
                f"股票: {symbol}, 日期: {trade_date}\n"
                f"--- 市场报告 ---\n{market_report}\n\n"
                f"--- 情绪报告 ---\n{sentiment_report}\n\n"
                f"--- 新闻报告 ---\n{news_report}\n\n"
                f"--- 基本面报告 ---\n{fundamentals_report}\n\n"
                f"--- 蜡烛图报告 ---\n{candlestick_report}"
            )
    except sqlite3.Error:
        pass
    
    return reasoning


def _build_recommendation(memory_name: str, prediction: str, 
                          reasoning: str, actual_return: float) -> str:
    """Build a recommendation string for a research record.
    
    Args:
        memory_name: Memory 实例名称
        prediction: 预测方向
        reasoning: 推理过程
        actual_return: 实际收益率
        
    Returns:
        Formatted recommendation string
    """
    role_name = memory_name.replace("_", " ").title()
    return (
        f"角色: {role_name}\n"
        f"预测: {prediction}\n"
        f"推理: {reasoning[:1000]}...\n"
        f"实际收益: {actual_return:.2%}"
    )


def _build_simple_recommendation(memory_name: str, prediction: str, 
                                 actual_return: float) -> str:
    """Build a simple recommendation without full reasoning.
    
    Args:
        memory_name: Memory 实例名称
        prediction: 预测方向
        actual_return: 实际收益率
        
    Returns:
        Formatted recommendation string
    """
    role_name = memory_name.replace("_", " ").title()
    return (
        f"角色: {role_name}\n"
        f"预测: {prediction}\n"
        f"实际收益: {actual_return:.2%}"
    )


def learn_from_research_records(
    db_path: str,
    memory_name: str,
    existing_documents: List[str],
    limit: int = 100,
    analysis_db_path: str = DEFAULT_ANALYSIS_DB_PATH
) -> Tuple[List[str], List[str], List[float], int]:
    """Learn from verified research records, combining with analysis reports.
    
    Args:
        db_path: research_tracker 数据库路径
        memory_name: Memory 实例名称
        existing_documents: 已有情境文档列表（用于去重）
        limit: 最大学习记录数
        analysis_db_path: analysis 数据库路径
        
    Returns:
        Tuple of (new_documents, new_recommendations, new_returns, count)
    """
    new_documents: List[str] = []
    new_recommendations: List[str] = []
    new_returns: List[float] = []
    existing_situations: Set[str] = set(existing_documents)
    count = 0
    
    try:
        # 从 research_records 表中获取已验证的记录
        with get_connection(db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT symbol, trade_date, prediction, reasoning, actual_return 
                FROM research_records 
                WHERE outcome != 'pending' 
                AND actual_return IS NOT NULL
                AND researcher_name = ?
                ORDER BY verified_date DESC
                LIMIT ?
            ''', (memory_name, limit))
            
            research_rows = cursor.fetchall()
        
        # 尝试从 analysis_reports 表获取完整报告
        if os.path.exists(analysis_db_path):
            analysis_conn = sqlite3.connect(analysis_db_path)
            analysis_conn.row_factory = sqlite3.Row
            
            try:
                analysis_cursor = analysis_conn.cursor()
                
                for row in research_rows:
                    symbol, trade_date, prediction, reasoning, actual_return = row
                    
                    if not reasoning or not reasoning.strip():
                        continue
                    
                    full_market_situation = _build_full_situation(
                        analysis_cursor, symbol, trade_date, reasoning
                    )
                    
                    if full_market_situation in existing_situations:
                        continue
                    
                    recommendation = _build_recommendation(
                        memory_name, prediction, reasoning, actual_return
                    )
                    
                    new_documents.append(full_market_situation)
                    new_recommendations.append(recommendation)
                    new_returns.append(actual_return)
                    existing_situations.add(full_market_situation)
                    count += 1
            finally:
                analysis_conn.close()
        else:
            # 没有 analysis_reports 表，只用 research_records 的数据
            for row in research_rows:
                symbol, trade_date, prediction, reasoning, actual_return = row
                
                if not reasoning or not reasoning.strip():
                    continue
                
                situation = f"股票: {symbol}, 日期: {trade_date}\n{reasoning}"
                
                if situation in existing_situations:
                    continue
                
                recommendation = _build_simple_recommendation(
                    memory_name, prediction, actual_return
                )
                
                new_documents.append(situation)
                new_recommendations.append(recommendation)
                new_returns.append(actual_return)
                existing_situations.add(situation)
                count += 1
    
    except (sqlite3.Error, KeyError, TypeError, ValueError) as e:
        logger.error("❌ 从研究记录学习失败: %s", e, exc_info=True)
    
    return new_documents, new_recommendations, new_returns, count
