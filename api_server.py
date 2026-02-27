#!/usr/bin/env python3
"""Reports API Server - 提供报告数据的 REST API"""

import http.server
import socketserver
import json
import sqlite3
import os
from urllib.parse import urlparse, parse_qs

PORT = 8002
DB_PATH = os.path.join(os.path.dirname(__file__), 'tradingagents/db/research_tracker.db')
DB_PATH2 = os.path.join(os.path.dirname(__file__), 'tradingagents/db/trading_analysis.db')

class APIHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)
        
        if path == '/api/stats':
            self.send_json(self.get_stats())
        elif path == '/api/stock/:symbol':
            symbol = query.get('symbol', [''])[0]
            self.send_json(self.get_stock_history(symbol))
        elif path == '/api/tool-calls':
            symbol = query.get('symbol', [None])[0]
            self.send_json(self.get_tool_calls(symbol))
        else:
            self.send_error(404)
    
    def send_json(self, data):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode())
    
    def get_stats(self):
        """获取所有股票的统计信息"""
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
    
    def get_stock_history(self, symbol):
        """获取指定股票的历史预测记录"""
        if not symbol or not os.path.exists(DB_PATH):
            return []
        
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                trade_date,
                researcher_type,
                prediction,
                confidence,
                actual_return,
                outcome
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
    
    def get_tool_calls(self, symbol=None):
        """获取工具调用统计"""
        if not os.path.exists(DB_PATH2):
            return {'total': 0, 'by_tool': [], 'by_vendor': []}
        
        conn = sqlite3.connect(DB_PATH2)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 总调用数
        cursor.execute("SELECT COUNT(*) as total FROM tool_calls")
        total = cursor.fetchone()['total']
        
        # 按工具统计
        cursor.execute("""
            SELECT tool_name, COUNT(*) as count 
            FROM tool_calls 
            GROUP BY tool_name 
            ORDER BY count DESC
            LIMIT 20
        """)
        by_tool = [{'name': row['tool_name'], 'count': row['count']} for row in cursor.fetchall()]
        
        # 按数据源统计
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
    with socketserver.TCPServer(("", PORT), APIHandler) as httpd:
        print(f"API Server running at http://localhost:{PORT}")
        httpd.serve_forever()
