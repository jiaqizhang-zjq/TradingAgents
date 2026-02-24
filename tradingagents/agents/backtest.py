#!/usr/bin/env python3
"""
回测脚本 - 使用最新股价验证研究员的预测收益
使用项目中已配置的数据源
"""

import os
import sqlite3
from datetime import datetime, timedelta
import sys
import json
from dotenv import load_dotenv

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(PROJECT_ROOT, "tradingagents", "db", "research_tracker.db")
sys.path.insert(0, PROJECT_ROOT)

# 加载环境变量
load_dotenv()

from tradingagents.dataflows.interface import get_data_manager


def get_price_on_date(symbol: str, target_date: str) -> float:
    """获取指定日期的股票价格"""
    try:
        target_dt = datetime.strptime(target_date, "%Y-%m-%d")
        
        # 使用统一接口，让它自动处理日期范围
        start_date = target_date
        end_date = target_date
        
        print(f"Fetching price for {symbol} on {target_date}")
        
        manager = get_data_manager()
        stock_data = manager.fetch("get_stock_data", symbol, start_date, end_date)
        
        if not stock_data or stock_data == "N/A" or (isinstance(stock_data, str) and stock_data.strip() == ""):
            print(f"No data returned for {symbol}")
            return None
        
        print(f"Data type: {type(stock_data)}, length: {len(stock_data) if isinstance(stock_data, str) else 'N/A'}")
        
        # 尝试解析JSON格式
        try:
            data = json.loads(stock_data)
            if isinstance(data, list) and len(data) > 0:
                # 按日期排序，获取最接近目标日期的数据
                sorted_data = sorted(data, key=lambda x: abs((datetime.strptime(x.get('Date', '2000-01-01')[:10], "%Y-%m-%d") - target_dt).days))
                for row in sorted_data:
                    if 'Close' in row:
                        return float(row['Close'])
                    elif 'close' in row:
                        return float(row['close'])
        except json.JSONDecodeError as e:
            pass  # 静默跳过，继续尝试CSV解析
        
        # 尝试解析CSV格式
        try:
            lines = stock_data.strip().split('\n')
            if len(lines) >= 2:
                # 跳过标题行
                header = lines[0].lower()
                print(f"Header: {header}")
                
                # 找到close列的索引
                close_index = -1
                header_parts = header.split(',')
                for i, col in enumerate(header_parts):
                    if 'close' in col:
                        close_index = i
                        break
                
                print(f"Close index: {close_index}")
                
                if close_index >= 0:
                    # 按日期排序，获取最接近目标日期的数据
                    data_rows = []
                    for line in lines[1:]:
                        if line.strip():
                            parts = line.split(',')
                            if len(parts) > close_index:
                                try:
                                    date_str = parts[0].split(' ')[0] if ' ' in parts[0] else parts[0]
                                    #print(f"Date string: {date_str}")
                                    row_date = datetime.strptime(date_str, "%Y-%m-%d")
                                    close_price = float(parts[close_index])
                                    data_rows.append((abs((row_date - target_dt).days), close_price))
                                    #print(f"Found price: {close_price} on {date_str}")
                                except Exception as e:
                                    print(f"Error parsing line: {line}, error: {e}")
                    
                    if data_rows:
                        data_rows.sort(key=lambda x: x[0])
                        # 只返回3天内的数据
                        if data_rows[0][0] <= 3:
                            print(f"Selected price: {data_rows[0][1]} (days difference: {data_rows[0][0]})")
                            return data_rows[0][1]
                        else:
                            print(f"No data within 3 days, closest is {data_rows[0][0]} days")
                            return None
                
                # 如果没有找到close列，尝试使用第5列（通常是close）
                last_line = lines[-1]
                parts = last_line.split(',')
                if len(parts) >= 5:
                    try:
                        price = float(parts[4])
                        print(f"Using last line price: {price}")
                        return price
                    except Exception as e:
                        print(f"Error parsing last line: {e}")
        except Exception as e:
            print(f"CSV parsing error: {e}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
        
        print(f"Could not parse price data for {symbol}")
        return None
    except Exception as e:
        print(f"Error fetching price for {symbol} on {target_date}: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
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


from datetime import datetime, timedelta


def is_market_open(symbol: str, target_date: str = None) -> bool:
    """通过获取股票数据判断是否开盘"""
    from tradingagents.agents.utils.agent_utils import is_market_open as check_market
    return check_market(symbol, target_date)


def run_backtest(symbol: str = None, target_date: str = None, db_path: str = DB_PATH, debug: bool = False):
    # 检查指定日期是否开盘
    if not is_market_open(symbol , target_date):
        if debug:
            print(f"⏰ {target_date or '当前'} 非开盘时间，跳过回测")
        return
    
    if not target_date:
        target_date = datetime.now().strftime("%Y-%m-%d")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 构建过滤条件
    symbol_filter = f"AND symbol = '{symbol}'" if symbol else ""
    
    # 确保表结构正确
    try:
        cursor.execute("ALTER TABLE research_records ADD COLUMN buy_price REAL")
        cursor.execute("ALTER TABLE research_records ADD COLUMN initial_capital REAL DEFAULT 10000")
        cursor.execute("ALTER TABLE research_records ADD COLUMN shares REAL")
        cursor.execute("ALTER TABLE research_records ADD COLUMN total_return REAL")
        conn.commit()
    except:
        pass
    
    # 回测前输出记录（只显示未回测的）
    print(f"\n=== 回测前 {symbol or '全部'} {target_date} 的待回测记录 ===")
    cursor.execute(f"""
        SELECT id, researcher_name, researcher_type, symbol, trade_date, prediction, confidence, 
               reasoning, outcome, verified_date, actual_return, holding_days, created_at, 
               metadata, buy_price, initial_capital, shares, total_return, backtest_date, backtest_price
        FROM research_records 
        WHERE trade_date <= '{target_date}' 
        AND prediction IN ('BUY', 'SELL', 'HOLD') {symbol_filter}
        ORDER BY symbol, trade_date, researcher_name
    """)
    all_records = cursor.fetchall()
    for r in all_records:
        print(f"ID:{r[0]} | {r[3]} | {r[4]} | {r[1]} | {r[5]} | conf:{r[6]} | outcome:{r[8]} | buy_price:{r[14]} | shares:{r[16]} | total_return:{r[17]} | backtest_date:{r[18]} | backtest_price:{r[19]}")
    print("-" * 130)
    
    # 找出目标日期的前一个有记录的 trade_date（且未回测过的）
    cursor.execute(f"""
        SELECT DISTINCT trade_date FROM research_records 
        WHERE trade_date < '{target_date}' 
        AND prediction IN ('BUY', 'SELL', 'HOLD') {symbol_filter}
        ORDER BY trade_date DESC
        LIMIT 1
    """)
    last_date_row = cursor.fetchone()
    if not last_date_row:
        print("没有可回测的历史记录")
        return
    last_date = last_date_row[0]
    
    print(f"回测日期: {last_date}")
    print("-" * 130)

    # 只获取前一个日期的记录
    cursor.execute(f"""
        SELECT id, researcher_name, researcher_type, symbol, trade_date, prediction, confidence, holding_days, buy_price, initial_capital, shares, metadata
        FROM research_records
        WHERE trade_date = '{last_date}' AND prediction IN ('BUY', 'SELL', 'HOLD') {symbol_filter}
        ORDER BY researcher_name
    """)
    pending_records = cursor.fetchall()

    print(f"找到 {len(pending_records)} 条待回测记录 (BUY/SELL/HOLD)")

    # 优化：先获取所有唯一的 (symbol, trade_date) 组合，避免重复请求 API
    unique_symbols = set()
    for record in pending_records:
        record_id, researcher_name, researcher_type, symbol, trade_date, prediction, confidence, holding_days, buy_price, initial_capital, shares, metadata = record
        if buy_price is None or buy_price == 0:
            unique_symbols.add((symbol, trade_date))

    # 批量获取价格
    price_cache = {}
    for symbol, trade_date in unique_symbols:
        price = get_price_on_date(symbol, trade_date)
        if price and price > 0:
            price_cache[(symbol, trade_date)] = price
            print(f"获取价格 {symbol} @ {trade_date}: ${price:.2f}")
        else:
            print(f"⚠️ {symbol} {trade_date}: 无法获取买入价格")

    print("-" * 130)

    # 更新记录
    for record in pending_records:
        record_id, researcher_name, researcher_type, symbol, trade_date, prediction, confidence, holding_days, buy_price, initial_capital, shares, metadata = record

        # 只回填空的买入价格
        if buy_price is None or buy_price == 0:
            buy_price = price_cache.get((symbol, trade_date))

            if buy_price is None or buy_price == 0:
                print(f"⚠️ {symbol} {trade_date}: 无法获取买入价格，跳过")
                continue

            # 设置默认初始资金和股数
            if initial_capital is None:
                initial_capital = 10000
            if shares is None or shares == 0:
                shares = calculate_shares(buy_price, initial_capital)

            # 更新买入价格和股数
            cursor.execute("""
                UPDATE research_records
                SET buy_price = ?, initial_capital = ?, shares = ?
                WHERE id = ?
            """, (buy_price, initial_capital, shares, record_id))

            print(f"回填 {symbol} {trade_date}: 买入价格 ${buy_price:.2f}, 股数 {shares:.2f}")

    conn.commit()
    updated_count = 0
    
    # 第二步：计算收益和更新 outcome
    print("\n开始计算收益...")
    print("-" * 130)

    # 获取 target_date 作为验证日期
    verify_date = target_date

    # 只获取前一个日期的记录
    cursor.execute(f"""
        SELECT id, researcher_name, researcher_type, symbol, trade_date, prediction, confidence, holding_days, buy_price, initial_capital, shares, metadata
        FROM research_records
        WHERE trade_date = '{last_date}' AND prediction IN ('BUY', 'SELL', 'HOLD') {symbol_filter}
        ORDER BY researcher_name
    """)

    records = cursor.fetchall()

    # 优化：先批量获取所有验证日期的价格，避免重复请求 API
    verify_prices = {}
    for record in records:
        record_id, researcher_name, researcher_type, symbol, trade_date, prediction, confidence, holding_days, buy_price, initial_capital, shares, metadata = record
        price = get_price_on_date(symbol, verify_date)
        if price:
            verify_prices[(symbol, verify_date)] = price

    # 计算收益
    for record in records:
        record_id, researcher_name, researcher_type, symbol, trade_date, prediction, confidence, holding_days, buy_price, initial_capital, shares, metadata = record

        # 获取验证日期的价格
        current_price = verify_prices.get((symbol, verify_date))
        if current_price is None:
            print(f"⚠️ {symbol} {verify_date}: 无法获取验证价格，跳过")
            continue

        # 计算收益率和总收益
        actual_return = calculate_return(buy_price, current_price)
        
        # SELL 预测使用做空收益计算
        if prediction == "SELL":
            short_return = (buy_price - current_price) / buy_price
            total_return = initial_capital * short_return
        else:
            total_return = calculate_profit(buy_price, current_price, initial_capital)
        
        # 判断预测是否正确
        if prediction == "HOLD":
            # HOLD 计算实际收益，share 不发生变化
            total_return = calculate_profit(buy_price, current_price, initial_capital)
            # HOLD 预测的正确性判断：如果收益在 -2% 到 2% 之间，认为是正确的
            outcome = "correct" if -0.02 <= actual_return <= 0.02 else ("incorrect" if abs(actual_return) > 0.05 else "partial")
        elif prediction == "BUY":
            outcome = "correct" if actual_return > 0 else ("incorrect" if actual_return < 0 else "partial")
        elif prediction == "SELL":
            # SELL 用做空收益率判断
            short_return = (buy_price - current_price) / buy_price
            outcome = "correct" if short_return > 0 else ("incorrect" if short_return < 0 else "partial")
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
            "verified_date": verify_date
        }
        
        # 更新数据库
        cursor.execute("""
            UPDATE research_records
            SET outcome = ?,
                actual_return = ?,
                total_return = ?,
                verified_date = ?,
                holding_days = ?,
                buy_price = ?,
                shares = ?,
                metadata = ?,
                backtest_date = ?,
                backtest_price = ?
            WHERE id = ?
        """, (outcome, actual_return, total_return, verify_date, holding_days, buy_price, shares, json.dumps(meta), verify_date, current_price, record_id))
        
        # 打印结果
        return_str = f"{actual_return*100:+.2f}%" if actual_return is not None else "N/A"
        profit_str = f"${total_return:+.2f}" if total_return is not None else "N/A"
        shares_str = f"{shares:.2f}" if shares else "0.00"
        
        print(f"{symbol:6s} | {trade_date} | {prediction:4s} | 买入: ${buy_price:.2f} | 股数: {shares_str:8s} | 当前: ${current_price:.2f} | 收益率: {return_str:10s} | 总收益: {profit_str:12s} | {outcome}")
        
        updated_count += 1
    
    conn.commit()
    conn.close()
    
    # 回测后输出记录
    print(f"\n=== 回测后 {symbol or '全部'} {target_date} 的记录 ===")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(f"""
        SELECT id, researcher_name, researcher_type, symbol, trade_date, prediction, confidence, 
               reasoning, outcome, verified_date, actual_return, holding_days, created_at, 
               metadata, buy_price, initial_capital, shares, total_return, backtest_date, backtest_price
        FROM research_records 
        WHERE trade_date <= '{target_date}' 
        AND prediction IN ('BUY', 'SELL', 'HOLD') {symbol_filter}
        ORDER BY symbol, trade_date, researcher_name
    """)
    all_records = cursor.fetchall()
    for r in all_records:
        print(f"ID:{r[0]} | {r[3]} | {r[4]} | {r[1]} | {r[5]} | conf:{r[6]} | outcome:{r[8]} | buy_price:{r[14]} | shares:{r[16]} | total_return:{r[17]} | backtest_date:{r[18]} | backtest_price:{r[19]}")
    conn.close()
    
    print("-" * 130)
    print(f"回测完成！更新了 {updated_count} 条记录")
    
    # 更新内存系统
    print("\n" + "="*50)
    print("🧠 更新内存系统...")
    print("="*50)
    
    try:
        from tradingagents.agents.utils.memory import FinancialSituationMemory
        
        # 更新各个内存系统
        memory_names = ["bull_researcher", "bear_researcher", "trader", "research_manager", "risk_manager"]
        for name in memory_names:
            memory = FinancialSituationMemory(name, {"db_path": db_path})
            memory.learn_from_research_records()
            print(f"✅ {name} 内存已更新")
    except Exception as e:
        print(f"❌ 更新内存系统失败: {e}")
        import traceback
        print(f"   错误详情: {traceback.format_exc()}")
    
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
