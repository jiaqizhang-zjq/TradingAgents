#!/usr/bin/env python3
"""
回测脚本 - 使用最新股价验证研究员的预测收益
使用项目中已配置的数据源
"""

import sqlite3
from datetime import datetime, timedelta
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tradingagents.dataflows.interface import get_data_manager


def get_price_on_date(symbol: str, target_date: str) -> float:
    """获取指定日期的股票价格"""
    try:
        manager = get_data_manager()
        
        target_dt = datetime.strptime(target_date, "%Y-%m-%d")
        start_date = (target_dt - timedelta(days=3)).strftime("%Y-%m-%d")
        end_date = (target_dt + timedelta(days=3)).strftime("%Y-%m-%d")
        
        stock_data = manager.fetch("get_stock_data", symbol, start_date, end_date)
        
        if not stock_data or stock_data == "N/A":
            return None
        
        try:
            data = json.loads(stock_data)
            if isinstance(data, list) and len(data) > 0:
                for row in data:
                    if 'Date' in row:
                        row_date = row['Date'][:10] if isinstance(row['Date'], str) else str(row['Date'])
                        if row_date == target_date:
                            if 'Close' in row:
                                return float(row['Close'])
                    if 'Close' in row:
                        return float(row['Close'])
                    elif 'close' in row:
                        return float(row['close'])
        except:
            pass
        
        lines = stock_data.strip().split('\n')
        if len(lines) >= 2:
            last_line = lines[-1]
            parts = last_line.split(',')
            if len(parts) >= 5:
                try:
                    return float(parts[4])
                except:
                    pass
        
        return None
    except Exception as e:
        print(f"Error fetching price for {symbol} on {target_date}: {e}")
        return None


def calculate_return(buy_price: float, current_price: float) -> float:
    if buy_price is None or current_price is None:
        return None
    return (current_price - buy_price) / buy_price


def calculate_profit(buy_price: float, current_price: float, initial_capital: float = 10000) -> float:
    if buy_price is None or current_price is None:
        return None
    shares = initial_capital / buy_price
    return (current_price - buy_price) * shares


def calculate_shares(buy_price: float, initial_capital: float = 10000) -> float:
    if buy_price is None or buy_price <= 0:
        return 0
    return initial_capital / buy_price


def run_backtest(db_path: str = "research_tracker.db"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 确保表结构正确
    try:
        cursor.execute("ALTER TABLE research_records ADD COLUMN buy_price REAL")
        cursor.execute("ALTER TABLE research_records ADD COLUMN initial_capital REAL DEFAULT 10000")
        cursor.execute("ALTER TABLE research_records ADD COLUMN shares REAL")
        cursor.execute("ALTER TABLE research_records ADD COLUMN total_return REAL")
        conn.commit()
    except:
        pass
    
    # 获取所有 pending 的记录
    cursor.execute("""
        SELECT id, researcher_name, researcher_type, symbol, trade_date, prediction, confidence, holding_days, buy_price, initial_capital, shares, metadata
        FROM research_records 
        WHERE outcome = 'pending'
        ORDER BY trade_date
    """)
    
    pending_records = cursor.fetchall()
    
    print(f"找到 {len(pending_records)} 条待回测记录")
    print("-" * 130)
    
    updated_count = 0
    
    for record in pending_records:
        record_id, researcher_name, researcher_type, symbol, trade_date, prediction, confidence, holding_days, buy_price, initial_capital, shares, metadata = record
        
        # 获取交易日期的价格
        if buy_price is None:
            buy_price = get_price_on_date(symbol, trade_date)
        
        if buy_price is None:
            print(f"⚠️ {symbol} {trade_date}: 无法获取买入价格，跳过")
            continue
        
        # 设置默认初始资金
        if initial_capital is None:
            initial_capital = 10000
        
        # 计算头寸数量
        if shares is None or shares == 0:
            shares = calculate_shares(buy_price, initial_capital)
        
        # 获取当前价格
        current_price = get_price_on_date(symbol, datetime.now().strftime("%Y-%m-%d"))
        if current_price is None:
            current_price = buy_price
        
        # 计算收益率和总收益
        actual_return = calculate_return(buy_price, current_price)
        total_return = calculate_profit(buy_price, current_price, initial_capital)
        
        # 判断预测是否正确
        if prediction == "BUY":
            outcome = "correct" if actual_return > 0 else ("incorrect" if actual_return < 0 else "partial")
        elif prediction == "SELL":
            outcome = "correct" if actual_return < 0 else ("incorrect" if actual_return > 0 else "partial")
        else:
            outcome = "correct" if -0.02 <= actual_return <= 0.02 else "partial"
        
        # 更新 metadata
        meta = {}
        if metadata:
            try:
                meta = json.loads(metadata) if isinstance(metadata, str) else metadata
            except:
                pass
        
        meta["position_change"] = {
            "action": prediction,
            "shares": shares,
            "buy_price": buy_price,
            "current_price": current_price,
            "total_return": total_return,
            "verified_date": datetime.now().strftime("%Y-%m-%d")
        }
        
        # 更新数据库
        verified_date = datetime.now().strftime("%Y-%m-%d")
        cursor.execute("""
            UPDATE research_records
            SET outcome = ?,
                actual_return = ?,
                total_return = ?,
                verified_date = ?,
                holding_days = ?,
                buy_price = ?,
                shares = ?,
                metadata = ?
            WHERE id = ?
        """, (outcome, actual_return, total_return, verified_date, holding_days, buy_price, shares, json.dumps(meta), record_id))
        
        # 打印结果
        return_str = f"{actual_return*100:+.2f}%" if actual_return is not None else "N/A"
        profit_str = f"${total_return:+.2f}" if total_return is not None else "N/A"
        shares_str = f"{shares:.2f}" if shares else "0.00"
        
        print(f"{symbol:6s} | {trade_date} | {prediction:4s} | 买入: ${buy_price:.2f} | 股数: {shares_str:8s} | 当前: ${current_price:.2f} | 收益率: {return_str:10s} | 总收益: {profit_str:12s} | {outcome}")
        
        updated_count += 1
    
    conn.commit()
    conn.close()
    
    print("-" * 130)
    print(f"回测完成！更新了 {updated_count} 条记录")
    
    # 打印统计
    print("\n=== 回测统计 ===")
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
    
    print("\n按研究员类型:")
    print(f"{'类型':15s} | {'总数':5s} | {'正确':5s} | {'错误':5s} | {'部分':5s} | {'胜率':8s} | {'平均收益率':12s} | {'总收益':14s}")
    print("-" * 100)
    
    for row in cursor.fetchall():
        researcher_type, total, correct, incorrect, partial, avg_return, total_profit = row
        if total and total > 0:
            win_rate = (correct / total * 100)
            avg_return_str = f"{avg_return*100:+.2f}%" if avg_return else "N/A"
            profit_str = f"${total_profit:+.2f}" if total_profit else "N/A"
            print(f"{researcher_type:15s} | {total:5d} | {correct:5d} | {incorrect:5d} | {partial:5d} | {win_rate:7.1f}% | {avg_return_str:12s} | {profit_str:14s}")
    
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
    
    print("\n按股票:")
    print(f"{'股票':8s} | {'总数':5s} | {'正确':5s} | {'胜率':8s} | {'平均收益率':12s} | {'总收益':14s}")
    print("-" * 70)
    
    for row in cursor.fetchall():
        symbol, total, correct, avg_return, total_profit = row
        if total and total > 0:
            win_rate = (correct / total * 100)
            avg_return_str = f"{avg_return*100:+.2f}%" if avg_return else "N/A"
            profit_str = f"${total_profit:+.2f}" if total_profit else "N/A"
            print(f"{symbol:8s} | {total:5d} | {correct:5d} | {win_rate:7.1f}% | {avg_return_str:12s} | {profit_str:14s}")
    
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
        print(f"\n总收益: ${total_profit:+.2f}" if total_profit else "\n总收益: N/A")
        print(f"平均收益率: {avg_return*100:+.2f}%" if avg_return else "平均收益率: N/A")
    
    conn.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="回测研究员的预测收益")
    parser.add_argument("--db", default="research_tracker.db", help="数据库路径")
    
    args = parser.parse_args()
    
    run_backtest(args.db)
