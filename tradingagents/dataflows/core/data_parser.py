"""数据解析模块"""

import io
import pandas as pd
from tradingagents.utils.logger import get_logger

logger = get_logger(__name__)


def parse_stock_data(stock_data_str: str) -> pd.DataFrame | None:
    """解析股票数据字符串为DataFrame
    
    Args:
        stock_data_str: 股票数据字符串（CSV或表格格式）
        
    Returns:
        解析后的DataFrame，失败返回None
    """
    try:
        # 尝试解析CSV格式 (timestamp,open,high,low,close,volume,adjusted_close)
        if 'timestamp' in stock_data_str and 'open' in stock_data_str and 'high' in stock_data_str:
            df = pd.read_csv(io.StringIO(stock_data_str))
            
            if 'timestamp' in df.columns:
                df['Date'] = pd.to_datetime(df['timestamp'])
                df = df.set_index('Date')
                
                for col in ['open', 'high', 'low', 'close', 'volume']:
                    if col in df.columns:
                        df[col.capitalize()] = pd.to_numeric(df[col], errors='coerce')
                        df = df.drop(columns=[col])
                
                return df
        
        # 尝试解析表格格式 (| Date | Open | ... |)
        if 'Date' in stock_data_str and 'Open' in stock_data_str:
            lines = stock_data_str.strip().split('\n')
            filtered_lines = [line for line in lines if not line.strip().startswith('|-') and line.strip()]
            cleaned_data = '\n'.join(filtered_lines)
            
            df = pd.read_csv(io.StringIO(cleaned_data), sep='\\s*\\|\\s*', engine='python')
            
            df.columns = [col.strip() for col in df.columns if col.strip()]
            
            if 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'])
                df = df.set_index('Date')
                
                for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                
                return df
    except Exception as e:
        logger.error("[parse_stock_data] Error: %s", e)
        import traceback
        logger.error("[parse_stock_data] Traceback:\n%s", traceback.format_exc())
        pass
    return None


def prepare_clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """准备干净的DataFrame用于指标计算
    
    Args:
        df: 原始DataFrame
        
    Returns:
        清理后的DataFrame（小写列名）
    """
    df_clean = pd.DataFrame()
    df_clean['timestamp'] = df.index
    df_clean['open'] = df['Open']
    df_clean['high'] = df['High']
    df_clean['low'] = df['Low']
    df_clean['close'] = df['Close']
    df_clean['volume'] = df['Volume']
    return df_clean
