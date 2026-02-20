#!/usr/bin/env python3
"""
验证研究员预测结果（需要在持仓期结束后运行）
"""

import sys
from datetime import datetime, timedelta
from tradingagents.dataflows.research_tracker import get_research_tracker
from tradingagents.dataflows.unified_data_manager import UnifiedDataManager
from tradingagents.default_config import DEFAULT_CONFIG

def verify_predictions(symbol: str = None, holding_days: int = 5):
    """
    验证待验证的预测
    
    Args:
        symbol: 特定股票代码，None 则验证所有
        holding_days: 持仓天数（默认5天）
    """
    print("=" * 80)
    print("🔍 研究员预测验证")
    print("=" * 80)
    
    tracker = get_research_tracker()
    data_manager = UnifiedDataManager(DEFAULT_CONFIG)
    
    # 获取待验证的预测
    try:
        with tracker._get_connection() as conn:
            cursor = conn.cursor()
            
            conditions = ["outcome = 'pending'"]
            params = []
            
            if symbol:
                conditions.append("symbol = ?")
                params.append(symbol)
            
            where_clause = " AND ".join(conditions)
            
            cursor.execute(f'''
                SELECT * FROM research_records
                WHERE {where_clause}
                ORDER BY trade_date DESC
            ''', params)
            
            rows = cursor.fetchall()
            
            if not rows:
                print("✅ 没有待验证的预测")
                return
            
            print(f"\n📋 找到 {len(rows)} 条待验证的预测\n")
            
            verified_count = 0
            for row in rows:
                record_id = row['id']
                rec_symbol = row['symbol']
                rec_trade_date = row['trade_date']
                researcher_name = row['researcher_name']
                prediction = row['prediction']
                
                print(f"────────────────────────────────────────")
                print(f"👤 {researcher_name}")
                print(f"📈 {rec_symbol} @ {rec_trade_date}")
                print(f"🔮 预测: {prediction}")
                
                # 计算验证日期
                try:
                    trade_date_obj = datetime.strptime(rec_trade_date, "%Y-%m-%d")
                    verify_date = trade_date_obj + timedelta(days=holding_days)
                    verify_date_str = verify_date.strftime("%Y-%m-%d")
                    
                    print(f"📅 验证日期: {verify_date_str}")
                    
                    # 获取实际收益
                    # 这里需要从数据源获取股票在持仓期的收益率
                    # 简化处理：实际使用时应该调用 data_manager 获取真实价格
                    
                    print("⚠️  需要真实价格数据来验证")
                    print("   提示: 请实现从数据源获取收益率的逻辑")
                    
                    # 示例：假设收益为 0，实际应该从 API 获取
                    # actual_return = get_actual_return(rec_symbol, rec_trade_date, holding_days)
                    
                except Exception as e:
                    print(f"❌ 计算验证日期失败: {e}")
                
                print()
            
            print("=" * 80)
            print(f"✅ 处理完成，共 {len(rows)} 条预测")
            print("=" * 80)
            
    except Exception as e:
        print(f"❌ 验证失败: {e}")

def get_actual_return(symbol: str, trade_date: str, holding_days: int) -> float:
    """
    获取股票的实际收益率（需要实现）
    
    Args:
        symbol: 股票代码
        trade_date: 交易日期
        holding_days: 持仓天数
        
    Returns:
        实际收益率（如 0.05 表示 5%）
    """
    # TODO: 实现从数据源获取真实价格和计算收益率
    # 示例逻辑：
    # 1. 获取 trade_date 的收盘价
    # 2. 获取 trade_date + holding_days 的收盘价
    # 3. 计算收益率 = (future_price - current_price) / current_price
    return 0.0

if __name__ == "__main__":
    symbol = sys.argv[1] if len(sys.argv) > 1 else None
    holding_days = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    
    verify_predictions(symbol, holding_days)
