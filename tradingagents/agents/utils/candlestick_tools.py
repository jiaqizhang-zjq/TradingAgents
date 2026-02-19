from langchain_core.tools import tool
from typing import Annotated
import pandas as pd
import io
from tradingagents.dataflows.interface import get_data_manager
from datetime import datetime, timedelta

def identify_candlestick_patterns(df):
    """
    识别蜡烛图形态，输入是OHLCV数据的DataFrame
    包含Open, High, Low, Close, Volume列，Date作为索引
    """
    patterns_result = []
    
    # 确保列名小写并正确排序
    df = df.copy()
    df = df.sort_index()
    
    for i in range(len(df)):
        current_patterns = []
        
        if i < 1:
            continue
            
        # 获取当前和前一根K线数据
        curr = df.iloc[i]
        prev = df.iloc[i-1]
        
        curr_open = curr['Open']
        curr_high = curr['High']
        curr_low = curr['Low']
        curr_close = curr['Close']
        prev_open = prev['Open']
        prev_high = prev['High']
        prev_low = prev['Low']
        prev_close = prev['Close']
        
        # 计算实体大小、上下影线
        curr_body_size = abs(curr_close - curr_open)
        prev_body_size = abs(prev_close - prev_open)
        
        curr_upper_shadow = curr_high - max(curr_open, curr_close)
        curr_lower_shadow = min(curr_open, curr_close) - curr_low
        
        prev_upper_shadow = prev_high - max(prev_open, prev_close)
        prev_lower_shadow = min(prev_open, prev_close) - prev_low
        
        curr_range = curr_high - curr_low
        prev_range = prev_high - prev_low
        
        # 判断涨跌
        curr_bullish = curr_close > curr_open
        curr_bearish = curr_close < curr_open
        prev_bullish = prev_close > prev_open
        prev_bearish = prev_close < prev_open
        
        # 1. HAMMER (锤子线) - 下影线至少是实体的2倍，实体很小，出现在下跌趋势中
        if (curr_lower_shadow >= 2 * curr_body_size and 
            curr_upper_shadow <= 0.5 * curr_body_size and 
            curr_body_size <= 0.3 * curr_range):
            current_patterns.append("HAMMER")
        
        # 2. HANGING_MAN (上吊线) - 类似锤子线，但出现在上涨趋势中
        if (curr_lower_shadow >= 2 * curr_body_size and 
            curr_upper_shadow <= 0.5 * curr_body_size and 
            curr_body_size <= 0.3 * curr_range):
            current_patterns.append("HANGING_MAN")
        
        # 3. INVERTED_HAMMER (倒锤子线) - 上影线至少是实体的2倍
        if (curr_upper_shadow >= 2 * curr_body_size and 
            curr_lower_shadow <= 0.5 * curr_body_size and 
            curr_body_size <= 0.3 * curr_range):
            current_patterns.append("INVERTED_HAMMER")
        
        # 4. DOJI (十字星) - 实体非常小
        if curr_body_size <= 0.1 * curr_range:
            current_patterns.append("DOJI")
            if curr_upper_shadow >= 2 * curr_body_size and curr_lower_shadow >= 2 * curr_body_size:
                current_patterns.append("LONG_LEGGED_DOJI")
        
        # 5. MARUBOZU (光头光脚) - 没有上下影线
        if curr_upper_shadow <= 0.05 * curr_range and curr_lower_shadow <= 0.05 * curr_range:
            if curr_bullish:
                current_patterns.append("MARUBOZU_BULLISH")
            else:
                current_patterns.append("MARUBOZU_BEARISH")
        
        # 6. BULLISH_ENGULFING (看涨吞没)
        if i >= 1 and prev_bearish and curr_bullish:
            if curr_open <= prev_close and curr_close >= prev_open:
                if curr_body_size > prev_body_size:
                    current_patterns.append("BULLISH_ENGULFING")
        
        # 7. BEARISH_ENGULFING (看跌吞没)
        if i >= 1 and prev_bullish and curr_bearish:
            if curr_open >= prev_close and curr_close <= prev_open:
                if curr_body_size > prev_body_size:
                    current_patterns.append("BEARISH_ENGULFING")
        
        # 8. PIERCING_PATTERN (刺透形态)
        if i >= 1 and prev_bearish and curr_bullish:
            if curr_open < prev_low:
                mid_prev = (prev_open + prev_close) / 2
                if curr_close > mid_prev and curr_close < prev_open:
                    current_patterns.append("PIERCING_PATTERN")
        
        # 9. DARK_CLOUD_COVER (乌云盖顶)
        if i >= 1 and prev_bullish and curr_bearish:
            if curr_open > prev_high:
                mid_prev = (prev_open + prev_close) / 2
                if curr_close < mid_prev and curr_close > prev_close:
                    current_patterns.append("DARK_CLOUD_COVER")
        
        # 10. THREE_WHITE_SOLDIERS (三只白兵)
        if i >= 2:
            t1 = df.iloc[i-2]
            t2 = df.iloc[i-1]
            t3 = df.iloc[i]
            if (t1['Close'] > t1['Open'] and 
                t2['Close'] > t2['Open'] and 
                t3['Close'] > t3['Open'] and
                t2['Close'] > t1['Close'] and 
                t3['Close'] > t2['Close'] and
                t2['Open'] > t1['Open'] and 
                t3['Open'] > t2['Open']):
                current_patterns.append("THREE_WHITE_SOLDIERS")
        
        # 11. THREE_BLACK_CROWS (三只乌鸦)
        if i >= 2:
            t1 = df.iloc[i-2]
            t2 = df.iloc[i-1]
            t3 = df.iloc[i]
            if (t1['Close'] < t1['Open'] and 
                t2['Close'] < t2['Open'] and 
                t3['Close'] < t3['Open'] and
                t2['Close'] < t1['Close'] and 
                t3['Close'] < t2['Close'] and
                t2['Open'] < t1['Open'] and 
                t3['Open'] < t2['Open']):
                current_patterns.append("THREE_BLACK_CROWS")
        
        # 12. MORNING_STAR (早晨之星) - 需要3根K线
        if i >= 2:
            t1 = df.iloc[i-2]
            t2 = df.iloc[i-1]
            t3 = df.iloc[i]
            t1_body = abs(t1['Close'] - t1['Open'])
            t2_body = abs(t2['Close'] - t2['Open'])
            t3_body = abs(t3['Close'] - t3['Open'])
            if (t1['Close'] < t1['Open'] and 
                t2_body <= 0.3 * t1_body and
                t3['Close'] > t3['Open'] and
                t3_body > t2_body and
                t3['Close'] > (t1['Open'] + t1['Close']) / 2):
                current_patterns.append("MORNING_STAR")
        
        # 13. EVENING_STAR (黄昏之星) - 需要3根K线
        if i >= 2:
            t1 = df.iloc[i-2]
            t2 = df.iloc[i-1]
            t3 = df.iloc[i]
            t1_body = abs(t1['Close'] - t1['Open'])
            t2_body = abs(t2['Close'] - t2['Open'])
            t3_body = abs(t3['Close'] - t3['Open'])
            if (t1['Close'] > t1['Open'] and 
                t2_body <= 0.3 * t1_body and
                t3['Close'] < t3['Open'] and
                t3_body > t2_body and
                t3['Close'] < (t1['Open'] + t1['Close']) / 2):
                current_patterns.append("EVENING_STAR")
        
        # 14. CONSECUTIVE_DOWN_3 (三连跌)
        if i >= 2:
            t1 = df.iloc[i-2]
            t2 = df.iloc[i-1]
            t3 = df.iloc[i]
            if (t3['Close'] < t2['Close'] and 
                t2['Close'] < t1['Close']):
                current_patterns.append("CONSECUTIVE_DOWN_3")
        
        # 15. CONSECUTIVE_UP_3 (三连涨)
        if i >= 2:
            t1 = df.iloc[i-2]
            t2 = df.iloc[i-1]
            t3 = df.iloc[i]
            if (t3['Close'] > t2['Close'] and 
                t2['Close'] > t1['Close']):
                current_patterns.append("CONSECUTIVE_UP_3")
        
        # 16. SPINNING_TOP (陀螺线)
        if (curr_body_size <= 0.3 * curr_range and 
            curr_upper_shadow >= curr_body_size and 
            curr_lower_shadow >= curr_body_size):
            current_patterns.append("SPINNING_TOP")
        
        # 如果找到形态，添加到结果中
        if current_patterns:
            date_str = df.index[i].strftime('%Y-%m-%d')
            patterns_result.append({
                'Date': date_str,
                'Patterns': ', '.join(current_patterns),
                'Open': round(curr_open, 2),
                'High': round(curr_high, 2),
                'Low': round(curr_low, 2),
                'Close': round(curr_close, 2)
            })
    
    return patterns_result

def parse_stock_data_to_dataframe(stock_data_str):
    """
    将字符串格式的股票数据解析为DataFrame
    
    Args:
        stock_data_str: 表格格式的股票数据字符串
        
    Returns:
        DataFrame: 解析后的DataFrame，Date为索引
    """
    try:
        if 'Date' in stock_data_str and 'Open' in stock_data_str:
            # 清理数据，移除分隔线
            lines = stock_data_str.strip().split('\n')
            filtered_lines = [line for line in lines if not line.strip().startswith('|-') and line.strip()]
            cleaned_data = '\n'.join(filtered_lines)
            
            # 使用pandas读取表格
            df = pd.read_csv(io.StringIO(cleaned_data), sep='\s*\|\s*', engine='python')
            
            # 清理列名
            df.columns = [col.strip() for col in df.columns if col.strip()]
            
            # 转换日期列为datetime并设为索引
            if 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'])
                df = df.set_index('Date')
                
                # 确保OHLC列是数值类型
                for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                
                return df
    except Exception as e:
        print(f"Error parsing stock data: {e}")
    return None

def format_patterns_result(patterns, symbol, start_date, end_date):
    """
    格式化蜡烛图形态识别结果
    
    Args:
        patterns: 识别到的形态列表
        symbol: 股票代码
        start_date: 开始日期
        end_date: 结束日期
        
    Returns:
        str: 格式化的结果字符串
    """
    if patterns:
        result = f"# Candlestick Patterns for {symbol} ({start_date} to {end_date})\n\n"
        result += "| Date       | Patterns                                      | Open   | High   | Low    | Close  |\n"
        result += "|------------|-----------------------------------------------|--------|--------|--------|--------|\n"
        
        for p in patterns:
            patterns_str = p['Patterns']
            if len(patterns_str) > 45:
                patterns_str = patterns_str[:42] + "..."
            result += f"| {p['Date']} | {patterns_str:<45} | {p['Open']:>6} | {p['High']:>6} | {p['Low']:>6} | {p['Close']:>6} |\n"
        
        # 汇总所有发现的形态
        all_patterns = []
        for p in patterns:
            all_patterns.extend(p['Patterns'].split(', '))
        
        pattern_counts = {}
        for pat in all_patterns:
            pattern_counts[pat] = pattern_counts.get(pat, 0) + 1
        
        result += f"\n## Pattern Summary\n"
        result += "| Pattern                | Count |\n"
        result += "|------------------------|-------|\n"
        for pat, cnt in sorted(pattern_counts.items(), key=lambda x: -x[1]):
            result += f"| {pat:<22} | {cnt:>5} |\n"
        
        return result
    else:
        return f"No candlestick patterns identified for {symbol} in the date range {start_date} to {end_date}"

@tool
def get_candlestick_patterns(
    symbol: Annotated[str, "ticker symbol of the company"],
    start_date: Annotated[str, "Start date (YYYY-mm-dd)"],
    end_date: Annotated[str, "End date (YYYY-mm-dd)"],
    stock_data: Annotated[str, "Optional: pre-fetched stock data in table format"] = "",
) -> str:
    """
    Identify candlestick patterns for a given ticker symbol.
    Returns recognized patterns like:
    - BULLISH_ENGULFING, BEARISH_ENGULFING
    - HAMMER, HANGING_MAN
    - DOJI
    - MORNING_STAR, EVENING_STAR
    - THREE_BLACK_CROWS, THREE_WHITE_SOLDIERS
    
    Args:
        symbol (str): Ticker symbol of the company, e.g. AAPL, TSM
        start_date (str): Start date (YYYY-mm-dd)
        end_date (str): End date (YYYY-mm-dd)
        stock_data (str): Optional: pre-fetched stock data in table format
    
    Returns:
        str: A formatted dataframe containing the candlestick patterns for the specified ticker symbol.
    """
    print(f"\n🔧 Calling get_candlestick_patterns (INTERNAL) for {symbol} ({start_date} to {end_date})...")
    
    stock_data_result = stock_data
    
    # 如果没有提供预获取的股票数据，则尝试获取
    if not stock_data_result:
        try:
            # 获取数据管理器
            manager = get_data_manager()
            # 获取股票数据
            stock_data_result = manager.fetch("get_stock_data", symbol, start_date, end_date)
        except Exception as e:
            return f"Error fetching stock data: {str(e)}"
    
    # 解析数据
    try:
        df = parse_stock_data_to_dataframe(stock_data_result)
        
        if df is not None:
            # 识别蜡烛图形态
            patterns = identify_candlestick_patterns(df)
            # 格式化输出
            return format_patterns_result(patterns, symbol, start_date, end_date)
        else:
            return f"Could not parse stock data format. Raw data preview: {stock_data_result[:500]}..."
    except Exception as e:
        import traceback
        return f"Error in internal candlestick pattern detection: {str(e)}\n{traceback.format_exc()}"
