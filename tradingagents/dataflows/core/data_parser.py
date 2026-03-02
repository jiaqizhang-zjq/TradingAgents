"""
数据解析器模块
负责解析各种格式的数据（CSV、JSON等）
"""
import pandas as pd
from typing import Optional


class DataParser:
    """数据解析器"""
    
    @staticmethod
    def parse_stock_data(stock_data_str: str) -> Optional[pd.DataFrame]:
        """
        解析股票数据字符串为DataFrame
        
        Args:
            stock_data_str: CSV格式的股票数据字符串
        
        Returns:
            DataFrame或None
        """
        try:
            lines = stock_data_str.strip().split('\n')
            if len(lines) < 2:
                return None
            
            header = [col.strip() for col in lines[0].split(',')]
            data = []
            
            for line in lines[1:]:
                if line.strip():
                    row = [col.strip() for col in line.split(',')]
                    if len(row) == len(header):
                        data.append(row)
            
            if not data:
                return None
            
            df = pd.DataFrame(data, columns=header)
            
            # 转换数值列
            numeric_cols = ['open', 'high', 'low', 'close', 'volume']
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # 转换日期列
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
                df = df.set_index('date').sort_index()
            
            return df
        except Exception:
            return None
    
    @staticmethod
    def reverse_sort_by_date(data_str: str, max_lines: int = 20) -> str:
        """
        按日期逆序排列数据并返回最新N条
        
        Args:
            data_str: 数据字符串
            max_lines: 最大返回行数
        
        Returns:
            逆序排列后的数据字符串
        """
        try:
            lines = data_str.split('\n')
            if len(lines) <= 2:
                return data_str
            
            header = lines[0]
            data_lines = lines[1:]
            data_lines.reverse()
            return header + '\n' + '\n'.join(data_lines[:max_lines])
        except Exception:
            return data_str[:500]
