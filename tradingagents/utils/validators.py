#!/usr/bin/env python3
"""全局输入验证与清理工具。"""

import re
from datetime import datetime
from typing import Any, Optional, Tuple

from tradingagents.exceptions import ValidationError


class InputValidator:
    """集中管理常用输入校验逻辑。"""

    DATE_FORMAT = "%Y-%m-%d"
    MAX_SYMBOL_LENGTH = 20
    ALLOWED_PREDICTIONS = {"BUY", "SELL", "HOLD"}
    _DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
    _SYMBOL_CHAR_PATTERN = re.compile(r"^[A-Za-z0-9.]+$")
    _SYMBOL_PATTERNS = (
        re.compile(r"^[A-Z]{1,5}$"),
        re.compile(r"^[A-Z]{1,5}\.US$"),
        re.compile(r"^[0-9]{4}\.HK$"),
        re.compile(r"^[0-9]{6}$"),
    )
    _SQL_KEYWORDS = re.compile(
        r"\b(drop|delete|truncate|update|insert|alter|create|replace|union|select)\b",
        re.IGNORECASE,
    )
    _DANGEROUS_TOKENS = re.compile(r"(--|/\*|\*/|;|'|\")")

    @classmethod
    def validate_symbol(cls, symbol: str) -> str:
        """验证并规范化股票代码。"""
        if symbol is None or not str(symbol).strip():
            raise ValidationError("symbol", "股票代码不能为空")

        normalized = str(symbol).strip().upper()
        if len(normalized) > cls.MAX_SYMBOL_LENGTH:
            raise ValidationError("symbol", "股票代码过长")
        if not cls._SYMBOL_CHAR_PATTERN.fullmatch(normalized):
            raise ValidationError("symbol", "股票代码只能包含字母、数字和点号")
        if not any(pattern.fullmatch(normalized) for pattern in cls._SYMBOL_PATTERNS):
            raise ValidationError("symbol", f"无效的股票代码格式: {normalized}")
        return normalized

    @classmethod
    def validate_date(cls, date_str: str) -> str:
        """验证日期格式与合法性。"""
        if date_str is None or not str(date_str).strip():
            raise ValidationError("date", "日期不能为空")

        normalized = str(date_str).strip()
        if not cls._DATE_PATTERN.fullmatch(normalized):
            raise ValidationError("date", "日期格式必须为 YYYY-MM-DD")

        try:
            datetime.strptime(normalized, cls.DATE_FORMAT)
        except ValueError as exc:
            raise ValidationError("date", f"无效的日期: {normalized}") from exc
        return normalized

    @classmethod
    def validate_date_range(cls, start_date: str, end_date: str) -> Tuple[str, str]:
        """验证日期范围。"""
        start = cls.validate_date(start_date)
        end = cls.validate_date(end_date)

        if datetime.strptime(start, cls.DATE_FORMAT) > datetime.strptime(end, cls.DATE_FORMAT):
            raise ValidationError("date_range", "开始日期必须早于或等于结束日期")
        return start, end

    @classmethod
    def validate_confidence(cls, confidence: float) -> float:
        """验证置信度范围。"""
        if not isinstance(confidence, (int, float)):
            raise ValidationError("confidence", "置信度必须是数字")

        value = float(confidence)
        if not 0 <= value <= 1:
            raise ValidationError("confidence", "置信度必须在 0-1 之间")
        return value

    @classmethod
    def validate_prediction(cls, prediction: str) -> str:
        """验证交易预测方向。"""
        if prediction is None or not str(prediction).strip():
            raise ValidationError("prediction", "预测类型不能为空")

        normalized = str(prediction).strip().upper()
        if normalized not in cls.ALLOWED_PREDICTIONS:
            allowed = ", ".join(sorted(cls.ALLOWED_PREDICTIONS))
            raise ValidationError("prediction", f"预测类型必须是: {allowed}")
        return normalized

    @classmethod
    def validate_vendor(cls, vendor: str, allowed_vendors: Optional[list[str]] = None) -> str:
        """验证数据供应商。"""
        if vendor is None or not str(vendor).strip():
            raise ValidationError("vendor", "Vendor cannot be empty")

        normalized = str(vendor).strip().upper()
        normalized_allowed = [item.upper() for item in allowed_vendors] if allowed_vendors else None
        if normalized_allowed and normalized not in normalized_allowed:
            raise ValidationError(
                "vendor",
                f"Invalid vendor: {normalized}. Allowed: {', '.join(normalized_allowed)}",
            )
        return normalized

    @classmethod
    def sanitize_string(cls, value: Any, max_length: int = 1000) -> str:
        """清理潜在危险字符串，避免注入和超长输入。"""
        if value is None:
            return ""

        cleaned = str(value).strip()
        cleaned = cls._SQL_KEYWORDS.sub("", cleaned)
        cleaned = cls._DANGEROUS_TOKENS.sub("", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned[:max_length]

    @classmethod
    def validate_trading_params(
        cls,
        symbol: str,
        start_date: str,
        end_date: str,
        confidence: Optional[float] = None,
        prediction: Optional[str] = None,
    ) -> dict[str, Any]:
        """一站式校验常见交易参数。"""
        validated_symbol = cls.validate_symbol(symbol)
        validated_start, validated_end = cls.validate_date_range(start_date, end_date)

        result: dict[str, Any] = {
            "symbol": validated_symbol,
            "start_date": validated_start,
            "end_date": validated_end,
        }
        if confidence is not None:
            result["confidence"] = cls.validate_confidence(confidence)
        if prediction is not None:
            result["prediction"] = cls.validate_prediction(prediction)
        return result


# 便捷函数

def validate_symbol(symbol: str) -> str:
    """验证股票代码。"""
    return InputValidator.validate_symbol(symbol)



def validate_date(date_str: str) -> str:
    """验证日期。"""
    return InputValidator.validate_date(date_str)



def validate_date_range(start_date: str, end_date: str) -> Tuple[str, str]:
    """验证日期范围。"""
    return InputValidator.validate_date_range(start_date, end_date)



def validate_confidence(confidence: float) -> float:
    """验证置信度。"""
    return InputValidator.validate_confidence(confidence)



def validate_prediction(prediction: str) -> str:
    """验证预测类型。"""
    return InputValidator.validate_prediction(prediction)



def validate_vendor(vendor: str, allowed_vendors: Optional[list[str]] = None) -> str:
    """验证数据供应商。"""
    return InputValidator.validate_vendor(vendor, allowed_vendors)



def sanitize_string(value: Any, max_length: int = 1000) -> str:
    """清理字符串。"""
    return InputValidator.sanitize_string(value, max_length=max_length)



def validate_trading_params(
    symbol: str,
    start_date: str,
    end_date: str,
    confidence: Optional[float] = None,
    prediction: Optional[str] = None,
) -> dict[str, Any]:
    """验证交易参数组合。"""
    return InputValidator.validate_trading_params(
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
        confidence=confidence,
        prediction=prediction,
    )


__all__ = [
    "InputValidator",
    "sanitize_string",
    "validate_confidence",
    "validate_date",
    "validate_date_range",
    "validate_prediction",
    "validate_symbol",
    "validate_trading_params",
    "validate_vendor",
]
