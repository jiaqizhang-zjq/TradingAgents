"""
日期调整器模块
负责调整日期范围，确保数据充足
"""
from datetime import datetime, timedelta
from typing import Tuple


class DateAdjuster:
    """日期范围调整器"""
    
    MIN_LOOKBACK_DAYS = 200  # 最小回溯天数
    
    @staticmethod
    def adjust_date_range(
        start_date: str,
        end_date: str,
        min_days: int = MIN_LOOKBACK_DAYS
    ) -> Tuple[str, str]:
        """
        调整日期范围，确保至少有min_days天的数据
        
        Args:
            start_date: 开始日期 (yyyy-mm-dd)
            end_date: 结束日期 (yyyy-mm-dd)
            min_days: 最小天数
        
        Returns:
            (调整后的开始日期, 结束日期)
        """
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            days_diff = (end_dt - start_dt).days
            
            if days_diff < min_days:
                new_start_dt = end_dt - timedelta(days=min_days)
                new_start_date = new_start_dt.strftime("%Y-%m-%d")
                return (new_start_date, end_date)
            
            return (start_date, end_date)
        except Exception:
            # 解析失败，返回原始日期
            return (start_date, end_date)
    
    @staticmethod
    def is_weekend(date_str: str) -> bool:
        """
        判断日期是否是周末
        
        Args:
            date_str: 日期字符串 (yyyy-mm-dd)
        
        Returns:
            是否是周末
        """
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            # 0=Monday, 6=Sunday
            return dt.weekday() >= 5
        except Exception:
            return False
    
    @staticmethod
    def should_cache_by_date(end_date: str) -> bool:
        """
        根据日期判断是否应该缓存
        （周末数据不缓存）
        
        Args:
            end_date: 结束日期
        
        Returns:
            是否应该缓存
        """
        return not DateAdjuster.is_weekend(end_date)
