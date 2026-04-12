"""
回测统计报告
============
提供回测结果的统计分析和打印功能。
"""

import sqlite3
from typing import Optional

from tradingagents.utils.logger import get_logger

logger = get_logger(__name__)


def print_records(cursor, symbol: Optional[str], target_date: str, title: str):
    """打印记录列表"""
    logger.info("=== %s %s %s 的记录 ===", title, symbol or '全部', target_date)
    
    if symbol:
        cursor.execute("""
            SELECT id, researcher_name, researcher_type, symbol, trade_date, prediction, confidence, 
                   reasoning, outcome, verified_date, actual_return, holding_days, created_at, 
                   metadata, buy_price, initial_capital, shares, total_return, backtest_date, backtest_price
            FROM research_records 
            WHERE trade_date <= ? 
            AND prediction IN ('BUY', 'SELL', 'HOLD')
            AND symbol = ?
            ORDER BY symbol, trade_date, researcher_name
        """, (target_date, symbol))
    else:
        cursor.execute("""
            SELECT id, researcher_name, researcher_type, symbol, trade_date, prediction, confidence, 
                   reasoning, outcome, verified_date, actual_return, holding_days, created_at, 
                   metadata, buy_price, initial_capital, shares, total_return, backtest_date, backtest_price
            FROM research_records 
            WHERE trade_date <= ? 
            AND prediction IN ('BUY', 'SELL', 'HOLD')
            ORDER BY symbol, trade_date, researcher_name
        """, (target_date,))
    
    all_records = cursor.fetchall()
    for r in all_records:
        logger.info("ID:%s | %s | %s | %s | %s | conf:%s | outcome:%s | "
                     "buy_price:%s | shares:%s | total_return:%s | "
                     "backtest_date:%s | backtest_price:%s",
                     r[0], r[3], r[4], r[1], r[5], r[6], r[8],
                     r[14], r[16], r[17], r[18], r[19])
    logger.info("-" * 130)


def print_backtest_stats(db_path: str):
    """打印回测统计报告"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 按研究员类型统计
    cursor.execute("""
        SELECT 
            researcher_type,
            COUNT(*) as total,
            SUM(CASE WHEN outcome = 'correct' THEN 1 ELSE 0 END) as correct,
            SUM(CASE WHEN outcome = 'incorrect' THEN 1 ELSE 0 END) as incorrect,
            SUM(CASE WHEN outcome = 'partial' THEN 1 ELSE 0 END) as partial,
            AVG(actual_return) as avg_return,
            SUM(total_return) as total_profit
        FROM research_records 
        WHERE outcome != 'pending'
        GROUP BY researcher_type
    """)
    
    logger.info("按研究员类型:")
    logger.info("%-15s | %-5s | %-5s | %-5s | %-5s | %-8s | %-12s | %-14s",
                "类型", "总数", "正确", "错误", "部分", "胜率", "平均收益率", "总收益")
    logger.info("-" * 100)
    
    for row in cursor.fetchall():
        researcher_type, total, correct, incorrect, partial, avg_return, total_profit = row
        if total and total > 0:
            win_rate = (correct / total * 100)
            avg_return_str = f"{avg_return*100:+.2f}%" if avg_return else "N/A"
            profit_str = f"${total_profit:+.2f}" if total_profit else "N/A"
            logger.info("%-15s | %5d | %5d | %5d | %5d | %6.1f%% | %-12s | %-14s",
                        researcher_type, total, correct, incorrect, partial, win_rate, avg_return_str, profit_str)
    
    # 按股票统计
    cursor.execute("""
        SELECT 
            symbol,
            COUNT(*) as total,
            SUM(CASE WHEN outcome = 'correct' THEN 1 ELSE 0 END) as correct,
            AVG(actual_return) as avg_return,
            SUM(total_return) as total_profit
        FROM research_records 
        WHERE outcome != 'pending'
        GROUP BY symbol
    """)
    
    logger.info("按股票:")
    logger.info("%-8s | %-5s | %-5s | %-8s | %-12s | %-14s",
                "股票", "总数", "正确", "胜率", "平均收益率", "总收益")
    logger.info("-" * 70)
    
    for row in cursor.fetchall():
        symbol_name, total, correct, avg_return, total_profit = row
        if total and total > 0:
            win_rate = (correct / total * 100)
            avg_return_str = f"{avg_return*100:+.2f}%" if avg_return else "N/A"
            profit_str = f"${total_profit:+.2f}" if total_profit else "N/A"
            logger.info("%-8s | %5d | %5d | %6.1f%% | %-12s | %-14s",
                        symbol_name, total, correct, win_rate, avg_return_str, profit_str)
    
    # 总利润统计
    cursor.execute("""
        SELECT 
            SUM(total_return) as total_profit,
            AVG(actual_return) as avg_return
        FROM research_records 
        WHERE outcome != 'pending'
    """)
    
    row = cursor.fetchone()
    if row:
        total_profit, avg_return = row
        if total_profit:
            logger.info("总收益: $%+.2f", total_profit)
        else:
            logger.info("总收益: N/A")
        if avg_return:
            logger.info("平均收益率: %+.2f%%", avg_return * 100)
        else:
            logger.info("平均收益率: N/A")
    
    conn.close()
