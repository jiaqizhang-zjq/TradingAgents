"""Database storage operations for FinancialSituationMemory.

Handles SQLite persistence: table schema, CRUD operations, and connection management.
"""

import sqlite3
from datetime import datetime
from contextlib import contextmanager
from typing import List, Tuple, Optional

from tradingagents.utils.logger import get_logger

logger = get_logger(__name__)


@contextmanager
def get_connection(db_path: str):
    """获取数据库连接上下文管理器。
    
    Args:
        db_path: SQLite 数据库文件路径
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except sqlite3.Error as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def init_database(db_path: str):
    """初始化数据库表结构。
    
    Args:
        db_path: SQLite 数据库文件路径
    """
    with get_connection(db_path) as conn:
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


def save_records(db_path: str, memory_name: str, 
                 documents: List[str], recommendations: List[str], 
                 returns: List[float]):
    """Save memory records to database.
    
    Args:
        db_path: SQLite 数据库文件路径
        memory_name: Memory 实例名称
        documents: 情境文档列表
        recommendations: 建议列表
        returns: 收益率列表
    """
    try:
        with get_connection(db_path) as conn:
            cursor = conn.cursor()
            now = datetime.now().isoformat()
            
            for situation, recommendation, return_value in zip(
                documents, recommendations, returns
            ):
                cursor.execute('''
                    INSERT OR REPLACE INTO memory_records (
                        memory_name, situation, recommendation, actual_return, 
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    memory_name, situation, recommendation,
                    return_value, now, now
                ))
            
            conn.commit()
            logger.info("✅ Memory %s 已保存到数据库: %d 条记录", memory_name, len(documents))
    except sqlite3.Error as e:
        logger.error("❌ 保存内存到数据库失败: %s", e)


def load_records(db_path: str, memory_name: str) -> Tuple[List[str], List[str], List[float]]:
    """Load memory records from database.
    
    Args:
        db_path: SQLite 数据库文件路径
        memory_name: Memory 实例名称
        
    Returns:
        Tuple of (documents, recommendations, returns)
    """
    documents: List[str] = []
    recommendations: List[str] = []
    returns: List[float] = []
    
    try:
        with get_connection(db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT situation, recommendation, actual_return 
                FROM memory_records 
                WHERE memory_name = ?
                ORDER BY id
            ''', (memory_name,))
            
            rows = cursor.fetchall()
            
            for row in rows:
                documents.append(row[0])
                recommendations.append(row[1])
                returns.append(row[2] if row[2] is not None else 0.0)
            
            if documents:
                logger.info("✅ Memory %s 从数据库加载: %d 条记录", memory_name, len(documents))
    except sqlite3.Error as e:
        logger.error("❌ 从数据库加载内存失败: %s", e)
    
    return documents, recommendations, returns


def save_backtest_record(db_path: str, memory_name: str,
                         symbol: str, trade_date: str,
                         situation: str, recommendation: str, 
                         actual_return: float):
    """Save a single backtest record to database.
    
    Args:
        db_path: SQLite 数据库文件路径
        memory_name: Memory 实例名称
        symbol: 股票代码
        trade_date: 交易日期
        situation: 市场情境描述
        recommendation: 建议
        actual_return: 实际收益率
    """
    try:
        with get_connection(db_path) as conn:
            cursor = conn.cursor()
            now = datetime.now().isoformat()
            
            cursor.execute('''
                INSERT OR REPLACE INTO memory_records (
                    memory_name, situation, recommendation, actual_return, 
                    symbol, trade_date, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                memory_name, situation, recommendation,
                actual_return, symbol, trade_date, now, now
            ))
            
            conn.commit()
            logger.info("✅ Memory %s 从回测更新: %s @ %s, 收益: %.2f%%", memory_name, symbol, trade_date, actual_return * 100)
    except sqlite3.Error as e:
        logger.error("❌ 从回测更新内存失败: %s", e)


def clear_records(db_path: str, memory_name: str):
    """Clear all records for a memory instance from database.
    
    Args:
        db_path: SQLite 数据库文件路径
        memory_name: Memory 实例名称
    """
    try:
        with get_connection(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                DELETE FROM memory_records WHERE memory_name = ?
            ''', (memory_name,))
            conn.commit()
            logger.info("✅ Memory %s 已清空", memory_name)
    except sqlite3.Error as e:
        logger.error("❌ 清空内存失败: %s", e)
