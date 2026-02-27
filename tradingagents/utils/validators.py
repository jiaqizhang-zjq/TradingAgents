#!/usr/bin/env python3
"""
全局输入验证器
提供股票代码、日期、日期范围等的验证功能
"""

import re
from datetime import datetime
from typing import Optional, Tuple
from tradingagents.exceptions import ValidationError


class InputValidator:
    """输入验证器"""
    
    # 股票代码正则（支持美股、A股）
    SYMBOL_PATTERN = re.compile(r'^[A-Z]{1,5}$|^[0-9]{6}$')
    
    # 日期格式
    DATE_FORMAT = "%Y-%m-%d"
    
    @classmethod
    def validate_symbol(cls, symbol: str) -> str:
        """
        验证股票代码格式
        
        Args:
            symbol: 股票代码
            
        Returns:
            验证后的股票代码（大写）
            
        Raises:
            ValidationError: 格式不合法
        """
        if not symbol:
            raise ValidationError("symbol", "Symbol cannot be empty")
        
        symbol = symbol.strip().upper()
        
        if not cls.SYMBOL_PATTERN.match(symbol):
            raise ValidationError(
                "symbol",
                f"Invalid symbol format: {symbol}. "
                "Expected US stock (1-5 uppercase letters) or CN stock (6 digits)"
            )
        
        return symbol
    
    @classmethod
    def validate_date(cls, date_str: str) -> str:
        """
        验证日期格式（YYYY-MM-DD）
        
        Args:
            date_str: 日期字符串
            
        Returns:
            验证后的日期字符串
            
        Raises:
            ValidationError: 格式不合法
        """
        if not date_str:
            raise ValidationError("date", "Date cannot be empty")
        
        date_str = date_str.strip()
        
        try:
            datetime.strptime(date_str, cls.DATE_FORMAT)
        except ValueError as e:
            raise ValidationError(
                "date",
                f"Invalid date format: {date_str}. Expected YYYY-MM-DD. Error: {e}"
            )
        
        return date_str
    
    @classmethod
    def validate_date_range(cls, start_date: str, end_date: str) -> Tuple[str, str]:
        """
        验证日期范围
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            (验证后的开始日期, 验证后的结束日期)
            
        Raises:
            ValidationError: 格式不合法或范围无效
        """
        start_date = cls.validate_date(start_date)
        end_date = cls.validate_date(end_date)
        
        start_dt = datetime.strptime(start_date, cls.DATE_FORMAT)
        end_dt = datetime.strptime(end_date, cls.DATE_FORMAT)
        
        if start_dt > end_dt:
            raise ValidationError(
                "date_range",
                f"Start date {start_date} is after end date {end_date}"
            )
        
        return start_date, end_date
    
    @classmethod
    def validate_confidence(cls, confidence: float) -> float:
        """
        验证置信度值
        
        Args:
            confidence: 置信度 (0-1)
            
        Returns:
            验证后的置信度
            
        Raises:
            ValidationError: 范围不合法
        """
        if not isinstance(confidence, (int, float)):
            raise ValidationError(
                "confidence",
                f"Confidence must be numeric, got {type(confidence)}"
            )
        
        if not 0 <= confidence <= 1:
            raise ValidationError(
                "confidence",
                f"Confidence must be between 0 and 1, got {confidence}"
            )
        
        return float(confidence)
    
    @classmethod
    def validate_vendor(cls, vendor: str, allowed_vendors: Optional[list] = None) -> str:
        """
        验证数据供应商
        
        Args:
            vendor: 供应商名称
            allowed_vendors: 允许的供应商列表（可选）
            
        Returns:
            验证后的供应商名称（大写）
            
        Raises:
            ValidationError: 供应商不在允许列表中
        """
        if not vendor:
            raise ValidationError("vendor", "Vendor cannot be empty")
        
        vendor = vendor.strip().upper()
        
        if allowed_vendors and vendor not in allowed_vendors:
            raise ValidationError(
                "vendor",
                f"Invalid vendor: {vendor}. Allowed: {', '.join(allowed_vendors)}"
            )
        
        return vendor


# 便捷函数
def validate_symbol(symbol: str) -> str:
    """验证股票代码"""
    return InputValidator.validate_symbol(symbol)


def validate_date(date_str: str) -> str:
    """验证日期"""
    return InputValidator.validate_date(date_str)


def validate_date_range(start_date: str, end_date: str) -> Tuple[str, str]:
    """验证日期范围"""
    return InputValidator.validate_date_range(start_date, end_date)


def validate_confidence(confidence: float) -> float:
    """验证置信度"""
    return InputValidator.validate_confidence(confidence)


def validate_vendor(vendor: str, allowed_vendors: Optional[list] = None) -> str:
    """验证数据供应商"""
    return InputValidator.validate_vendor(vendor, allowed_vendors)
