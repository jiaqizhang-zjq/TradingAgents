"""
数据库模型和存储管理
用于存储 LangGraph 分析结果和工具调用数据
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from contextlib import contextmanager


@dataclass
class AnalysisReport:
    """分析报告数据结构"""
    symbol: str
    trade_date: str
    created_at: str
    
    # 各分析师报告 (Markdown 格式)
    market_report: str = ""
    fundamentals_report: str = ""
    candlestick_report: str = ""
    sentiment_report: str = ""
    news_report: str = ""
    
    # 交易决策相关
    investment_plan: str = ""
    trader_investment_plan: str = ""
    final_trade_decision: str = ""
    
    # 原始工具调用结果 (JSONL 格式)
    tool_calls_jsonl: str = ""
    
    # 元数据
    metadata: str = "{}"


class TradingDatabase:
    """交易分析数据库管理器"""
    
    def __init__(self, db_path: str = "tradingagents/db/trading_analysis.db"):
        self.db_path = db_path
        self._init_database()
    
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
            
            # 创建分析报告主表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS analysis_reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    trade_date TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    
                    -- 分析师报告 (Markdown)
                    market_report TEXT,
                    fundamentals_report TEXT,
                    candlestick_report TEXT,
                    sentiment_report TEXT,
                    news_report TEXT,
                    
                    -- 交易决策
                    investment_plan TEXT,
                    trader_investment_plan TEXT,
                    final_trade_decision TEXT,
                    
                    -- 工具调用原始数据 (JSONL)
                    tool_calls_jsonl TEXT,
                    
                    -- 元数据 (JSON)
                    metadata TEXT,
                    
                    -- 唯一约束: 股票+日期
                    UNIQUE(symbol, trade_date)
                )
            ''')
            
            # 创建工具调用详细记录表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tool_calls (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    trade_date TEXT NOT NULL,
                    tool_name TEXT NOT NULL,
                    vendor_used TEXT,
                    input_params TEXT,
                    result_preview TEXT,
                    full_result TEXT,
                    created_at TEXT NOT NULL,
                    
                    FOREIGN KEY (symbol, trade_date) 
                    REFERENCES analysis_reports(symbol, trade_date)
                )
            ''')
            
            # 创建索引
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_reports_symbol_date 
                ON analysis_reports(symbol, trade_date)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_tool_calls_symbol_date 
                ON tool_calls(symbol, trade_date)
            ''')
            
            conn.commit()
            print(f"✅ 数据库初始化完成: {self.db_path}")
    
    def save_analysis_report(self, report: AnalysisReport) -> bool:
        """
        保存分析报告
        
        Args:
            report: AnalysisReport 对象
            
        Returns:
            bool: 是否保存成功
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT OR REPLACE INTO analysis_reports (
                        symbol, trade_date, created_at,
                        market_report, fundamentals_report, candlestick_report,
                        sentiment_report, news_report,
                        investment_plan, trader_investment_plan, final_trade_decision,
                        tool_calls_jsonl, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    report.symbol,
                    report.trade_date,
                    report.created_at,
                    report.market_report,
                    report.fundamentals_report,
                    report.candlestick_report,
                    report.sentiment_report,
                    report.news_report,
                    report.investment_plan,
                    report.trader_investment_plan,
                    report.final_trade_decision,
                    report.tool_calls_jsonl,
                    report.metadata
                ))
                
                print(f"✅ 报告已保存: {report.symbol} @ {report.trade_date}")
                return True
                
        except Exception as e:
            print(f"❌ 保存报告失败: {e}")
            return False
    
    def save_tool_call(self, symbol: str, trade_date: str, 
                       tool_name: str, vendor_used: str,
                       input_params: Dict, result: str) -> bool:
        """
        保存工具调用记录
        
        Args:
            symbol: 股票代码
            trade_date: 交易日期
            tool_name: 工具名称
            vendor_used: 使用的数据源
            input_params: 输入参数
            result: 工具返回结果
            
        Returns:
            bool: 是否保存成功
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                created_at = datetime.now().isoformat()
                result_preview = result[:500] if len(result) > 500 else result
                
                cursor.execute('''
                    INSERT INTO tool_calls (
                        symbol, trade_date, tool_name, vendor_used,
                        input_params, result_preview, full_result, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    symbol, trade_date, tool_name, vendor_used,
                    json.dumps(input_params, ensure_ascii=False),
                    result_preview,
                    result,
                    created_at
                ))
                
                return True
                
        except Exception as e:
            print(f"❌ 保存工具调用失败: {e}")
            return False
    
    def get_report(self, symbol: str, trade_date: str) -> Optional[AnalysisReport]:
        """
        获取指定股票和日期的分析报告
        
        Args:
            symbol: 股票代码
            trade_date: 交易日期
            
        Returns:
            AnalysisReport 对象或 None
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM analysis_reports 
                    WHERE symbol = ? AND trade_date = ?
                ''', (symbol, trade_date))
                
                row = cursor.fetchone()
                
                if row:
                    return AnalysisReport(
                        symbol=row['symbol'],
                        trade_date=row['trade_date'],
                        created_at=row['created_at'],
                        market_report=row['market_report'] or "",
                        fundamentals_report=row['fundamentals_report'] or "",
                        candlestick_report=row['candlestick_report'] or "",
                        sentiment_report=row['sentiment_report'] or "",
                        news_report=row['news_report'] or "",
                        investment_plan=row['investment_plan'] or "",
                        trader_investment_plan=row['trader_investment_plan'] or "",
                        final_trade_decision=row['final_trade_decision'] or "",
                        tool_calls_jsonl=row['tool_calls_jsonl'] or "",
                        metadata=row['metadata'] or "{}"
                    )
                
                return None
                
        except Exception as e:
            print(f"❌ 获取报告失败: {e}")
            return None
    
    def get_tool_calls(self, symbol: str, trade_date: str) -> List[Dict]:
        """
        获取指定股票和日期的所有工具调用记录
        
        Args:
            symbol: 股票代码
            trade_date: 交易日期
            
        Returns:
            工具调用记录列表
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM tool_calls 
                    WHERE symbol = ? AND trade_date = ?
                    ORDER BY created_at
                ''', (symbol, trade_date))
                
                rows = cursor.fetchall()
                
                return [
                    {
                        'tool_name': row['tool_name'],
                        'vendor_used': row['vendor_used'],
                        'input_params': json.loads(row['input_params']),
                        'result_preview': row['result_preview'],
                        'created_at': row['created_at']
                    }
                    for row in rows
                ]
                
        except Exception as e:
            print(f"❌ 获取工具调用记录失败: {e}")
            return []
    
    def list_reports(self, symbol: Optional[str] = None, 
                     start_date: Optional[str] = None,
                     end_date: Optional[str] = None) -> List[Dict]:
        """
        列出所有报告
        
        Args:
            symbol: 可选，按股票代码筛选
            start_date: 可选，开始日期
            end_date: 可选，结束日期
            
        Returns:
            报告列表
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                query = 'SELECT symbol, trade_date, created_at FROM analysis_reports WHERE 1=1'
                params = []
                
                if symbol:
                    query += ' AND symbol = ?'
                    params.append(symbol)
                
                if start_date:
                    query += ' AND trade_date >= ?'
                    params.append(start_date)
                
                if end_date:
                    query += ' AND trade_date <= ?'
                    params.append(end_date)
                
                query += ' ORDER BY trade_date DESC, symbol'
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                return [
                    {
                        'symbol': row['symbol'],
                        'trade_date': row['trade_date'],
                        'created_at': row['created_at']
                    }
                    for row in rows
                ]
                
        except Exception as e:
            print(f"❌ 列出报告失败: {e}")
            return []
    
    def export_report_to_markdown(self, symbol: str, trade_date: str, 
                                   output_dir: str = "reports") -> str:
        """
        将报告导出为 Markdown 文件
        
        Args:
            symbol: 股票代码
            trade_date: 交易日期
            output_dir: 输出目录
            
        Returns:
            导出的文件路径
        """
        report = self.get_report(symbol, trade_date)
        
        if not report:
            print(f"❌ 未找到报告: {symbol} @ {trade_date}")
            return ""
        
        os.makedirs(output_dir, exist_ok=True)
        
        filename = f"{symbol}_{trade_date}_report.md"
        filepath = os.path.join(output_dir, filename)
        
        content = f"""# 股票分析报告: {symbol}

**分析日期**: {trade_date}  
**生成时间**: {report.created_at}

---

## 📊 市场分析报告

{report.market_report}

---

## 📈 基本面分析报告

{report.fundamentals_report}

---

## 🕯️ 蜡烛图分析报告

{report.candlestick_report}

---

## 😊 情绪分析报告

{report.sentiment_report}

---

## 📰 新闻分析报告

{report.news_report}

---

## 💼 投资计划

{report.investment_plan}

---

## 🎯 交易员计划

{report.trader_investment_plan}

---

## ✅ 最终交易决策

{report.final_trade_decision}

---

*报告由 TradingAgents 系统自动生成*
"""
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ Markdown 报告已导出: {filepath}")
        return filepath
    
    def export_tool_calls_to_jsonl(self, symbol: str, trade_date: str,
                                    output_dir: str = "reports") -> str:
        """
        将工具调用记录导出为 JSONL 文件
        
        Args:
            symbol: 股票代码
            trade_date: 交易日期
            output_dir: 输出目录
            
        Returns:
            导出的文件路径
        """
        tool_calls = self.get_tool_calls(symbol, trade_date)
        
        if not tool_calls:
            print(f"⚠️ 未找到工具调用记录: {symbol} @ {trade_date}")
            return ""
        
        os.makedirs(output_dir, exist_ok=True)
        
        filename = f"{symbol}_{trade_date}_tool_calls.jsonl"
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            for call in tool_calls:
                f.write(json.dumps(call, ensure_ascii=False) + '\n')
        
        print(f"✅ JSONL 工具调用记录已导出: {filepath}")
        return filepath


# 全局数据库实例
db = TradingDatabase()


def get_db() -> TradingDatabase:
    """获取数据库实例"""
    return db
