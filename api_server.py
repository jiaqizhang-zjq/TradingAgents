#!/usr/bin/env python3
"""Reports Server - HTTP + API 在同一个端口"""

import http.server
import socketserver
import json
import sqlite3
import os
from urllib.parse import urlparse, parse_qs

PORT = 8001
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'tradingagents/db/research_tracker.db')
DB_PATH2 = os.path.join(BASE_DIR, 'tradingagents/db/trading_analysis.db')

class ReportsHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)
        
        # API 路由
        if path == '/api/stats':
            self.send_json(self.get_stats())
        elif path == '/api/stock-history':
            symbol = query.get('symbol', [''])[0]
            self.send_json(self.get_stock_history(symbol))
        elif path == '/api/stock-chart':
            symbol = query.get('symbol', [''])[0]
            self.send_json(self.get_stock_chart(symbol))
        elif path == '/api/analyst-records':
            symbol = query.get('symbol', [''])[0]
            date = query.get('date', [''])[0]
            self.send_json(self.get_analyst_records(symbol, date))
        elif path == '/api/tool-calls':
            self.send_json(self.get_tool_calls())
        else:
            # 其他请求交给默认处理
            super().do_GET()
    
    def send_json(self, data):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode())
    
    def get_stats(self):
        if not os.path.exists(DB_PATH):
            return []
        
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                symbol,
                COUNT(*) as total,
                SUM(CASE WHEN outcome = 'correct' THEN 1 ELSE 0 END) as correct,
                SUM(CASE WHEN outcome = 'incorrect' THEN 1 ELSE 0 END) as incorrect,
                SUM(CASE WHEN outcome = 'partial' THEN 1 ELSE 0 END) as partial,
                AVG(actual_return) as avg_return,
                MAX(trade_date) as latest_date
            FROM research_records 
            WHERE actual_return IS NOT NULL
            GROUP BY symbol
            ORDER BY total DESC
        """)
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'symbol': row['symbol'],
                'total': row['total'],
                'correct': row['correct'],
                'incorrect': row['incorrect'],
                'partial': row['partial'],
                'win_rate': round(row['correct'] / row['total'] * 100, 1) if row['total'] > 0 else 0,
                'avg_return': round(row['avg_return'] * 100, 2) if row['avg_return'] else 0,
                'latest_date': row['latest_date']
            })
        
        conn.close()
        return results
    
    def get_stock_chart(self, symbol):
        """获取股票价格数据（用于K线图）"""
        print(f"DEBUG: get_stock_chart called with symbol={symbol}, DB_PATH2={DB_PATH2}, exists={os.path.exists(DB_PATH2)}")
        
        if not symbol or not os.path.exists(DB_PATH2):
            print(f"DEBUG: DB not exists or no symbol")
            return []
        
        conn = sqlite3.connect(DB_PATH2)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 获取最新的价格数据
        cursor.execute("""
            SELECT result_preview, created_at 
            FROM tool_calls 
            WHERE tool_name = 'get_stock_data' AND symbol = ?
            ORDER BY created_at DESC
            LIMIT 1
        """, (symbol,))
        
        row = cursor.fetchone()
        print(f"DEBUG: row = {row}")
        if not row or not row['result_preview']:
            print(f"DEBUG: no row or no preview")
            conn.close()
            return []
        
        # 解析CSV数据
        import csv
        from io import StringIO
        
        try:
            lines = row['result_preview'].strip().split('\n')
            if len(lines) < 2:
                conn.close()
                return []
            
            reader = csv.DictReader(lines)
            data = []
            for r in reader:
                data.append({
                    'date': r.get('timestamp', '')[:10],
                    'open': float(r.get('open', 0)),
                    'high': float(r.get('high', 0)),
                    'low': float(r.get('low', 0)),
                    'close': float(r.get('close', 0)),
                    'volume': int(r.get('volume', 0))
                })
            
            # 只返回最近60天
            conn.close()
            return data[-60:] if len(data) > 60 else data
            
        except Exception as e:
            conn.close()
            return []
    
    def get_analyst_records(self, symbol, date=''):
        """获取指定股票的所有分析师预测记录"""
        if not symbol or not os.path.exists(DB_PATH):
            return []
        
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if date:
            cursor.execute("""
                SELECT 
                    trade_date,
                    researcher_type,
                    prediction,
                    confidence,
                    reasoning,
                    actual_return,
                    outcome
                FROM research_records 
                WHERE symbol = ? AND trade_date = ?
                ORDER BY researcher_type
            """, (symbol, date))
        else:
            cursor.execute("""
                SELECT 
                    trade_date,
                    researcher_type,
                    prediction,
                    confidence,
                    reasoning,
                    actual_return,
                    outcome
                FROM research_records 
                WHERE symbol = ? AND actual_return IS NOT NULL
                ORDER BY trade_date DESC, researcher_type
                LIMIT 50
            """, (symbol,))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'date': row['trade_date'],
                'analyst': row['researcher_type'],
                'prediction': row['prediction'],
                'confidence': row['confidence'],
                'reasoning': row['reasoning'][:300] if row['reasoning'] else '',
                'return': round(row['actual_return'] * 100, 2) if row['actual_return'] else 0,
                'outcome': row['outcome']
            })
        
        conn.close()
        return results
    
    def get_stock_history(self, symbol):
        if not symbol or not os.path.exists(DB_PATH):
            return []
        
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT trade_date, researcher_type, prediction, confidence, actual_return, outcome
            FROM research_records 
            WHERE symbol = ? AND actual_return IS NOT NULL
            ORDER BY trade_date DESC, researcher_type
        """, (symbol,))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'date': row['trade_date'],
                'type': row['researcher_type'],
                'prediction': row['prediction'],
                'confidence': row['confidence'],
                'return': round(row['actual_return'] * 100, 2) if row['actual_return'] else 0,
                'outcome': row['outcome']
            })
        
        conn.close()
        return results
    
    def get_tool_calls(self):
        if not os.path.exists(DB_PATH2):
            return {'total': 0, 'by_tool': [], 'by_vendor': []}
        
        conn = sqlite3.connect(DB_PATH2)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) as total FROM tool_calls")
        total = cursor.fetchone()['total']
        
        cursor.execute("""
            SELECT tool_name, COUNT(*) as count 
            FROM tool_calls 
            GROUP BY tool_name 
            ORDER BY count DESC
            LIMIT 20
        """)
        by_tool = [{'name': row['tool_name'], 'count': row['count']} for row in cursor.fetchall()]
        
        cursor.execute("""
            SELECT vendor_used, COUNT(*) as count 
            FROM tool_calls 
            GROUP BY vendor_used 
            ORDER BY count DESC
        """)
        by_vendor = [{'name': row['vendor_used'], 'count': row['count']} for row in cursor.fetchall()]
        
        conn.close()
        
        return {'total': total, 'by_tool': by_tool, 'by_vendor': by_vendor}

if __name__ == '__main__':
    os.chdir(BASE_DIR)
    with socketserver.TCPServer(("", PORT), ReportsHandler) as httpd:
        print(f"Server running at http://localhost:{PORT}")
        print(f"Reports: http://localhost:{PORT}/reports.html")
        print(f"API: http://localhost:{PORT}/api/stats")
        httpd.serve_forever()
