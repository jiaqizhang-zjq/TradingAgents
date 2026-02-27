#!/usr/bin/env python3
"""
预测提取器 - 使用策略模式重构复杂条件逻辑
"""

import re
from abc import ABC, abstractmethod
from typing import Optional, Tuple, Dict
from tradingagents.constants import (
    STRONG_CONFIDENCE,
    WEAK_CONFIDENCE,
    NEUTRAL_CONFIDENCE
)


class ExtractionStrategy(ABC):
    """预测提取策略基类"""
    
    @abstractmethod
    def extract(self, text: str) -> Optional[Tuple[str, float]]:
        """
        提取预测和置信度
        
        Args:
            text: LLM响应文本
            
        Returns:
            (预测, 置信度) 或 None
        """
        pass


class RegexStrategy(ExtractionStrategy):
    """正则表达式提取策略"""
    
    # 预测正则模式
    PREDICTION_PATTERNS = [
        r'预测[:：]\s*(BUY|SELL|HOLD)',
        r'Prediction[:：]\s*(BUY|SELL|HOLD)',
        r'建议[:：]\s*(BUY|SELL|HOLD)',
        r'Recommendation[:：]\s*(BUY|SELL|HOLD)',
        r'\*\*预测\*\*[:：]?\s*(BUY|SELL|HOLD)',
        r'\*\*Prediction\*\*[:：]?\s*(BUY|SELL|HOLD)',
    ]
    
    # 置信度正则模式
    CONFIDENCE_PATTERNS = [
        r'置信度[:：]\s*([0-9.]+)',
        r'Confidence[:：]\s*([0-9.]+)',
        r'信心[:：]\s*([0-9.]+)',
        r'\*\*置信度\*\*[:：]?\s*([0-9.]+)',
        r'\*\*Confidence\*\*[:：]?\s*([0-9.]+)',
    ]
    
    def extract(self, text: str) -> Optional[Tuple[str, float]]:
        """使用正则表达式提取"""
        prediction = None
        confidence = None
        
        # 提取预测
        for pattern in self.PREDICTION_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                prediction = match.group(1).upper()
                break
        
        # 提取置信度
        for pattern in self.CONFIDENCE_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    conf_value = float(match.group(1))
                    # 如果是百分比形式（>1），转换为0-1
                    if conf_value > 1:
                        conf_value = conf_value / 100
                    confidence = conf_value
                    break
                except ValueError:
                    continue
        
        if prediction and confidence:
            return (prediction, confidence)
        
        return None


class KeywordStrategy(ExtractionStrategy):
    """关键词推断策略"""
    
    # 关键词映射
    KEYWORD_MAPPING = {
        'BUY': ['买入', '建议买入', '推荐买入', '强烈推荐买入', 'recommend buy', 'strong buy'],
        'SELL': ['卖出', '建议卖出', '推荐卖出', '强烈推荐卖出', 'recommend sell', 'strong sell'],
        'HOLD': ['持有', '建议持有', '继续持有', 'recommend hold', 'keep holding']
    }
    
    # 置信度关键词
    CONFIDENCE_KEYWORDS = {
        '强烈': 0.85,
        '非常': 0.80,
        '高度': 0.80,
        '较强': 0.75,
        '谨慎': 0.60,
        '弱': 0.55,
        'strong': 0.85,
        'highly': 0.80,
        'moderate': 0.70,
        'weak': 0.55,
    }
    
    def extract(self, text: str) -> Optional[Tuple[str, float]]:
        """使用关键词推断"""
        text_lower = text.lower()
        
        # 查找预测关键词
        prediction = None
        for pred, keywords in self.KEYWORD_MAPPING.items():
            if any(kw.lower() in text_lower for kw in keywords):
                prediction = pred
                break
        
        if not prediction:
            return None
        
        # 推断置信度
        confidence = NEUTRAL_CONFIDENCE
        for keyword, conf in self.CONFIDENCE_KEYWORDS.items():
            if keyword.lower() in text_lower:
                confidence = conf
                break
        
        return (prediction, confidence)


class LengthBasedStrategy(ExtractionStrategy):
    """基于响应长度的策略"""
    
    def extract(self, text: str) -> Optional[Tuple[str, float]]:
        """
        根据响应长度推断
        
        - 长响应（>500字符）通常表示深入分析，给予较高置信度
        - 短响应（<200字符）可能分析不足，给予较低置信度
        """
        text_length = len(text.strip())
        
        if text_length > 500:
            confidence = STRONG_CONFIDENCE
        elif text_length > 300:
            confidence = NEUTRAL_CONFIDENCE
        else:
            confidence = WEAK_CONFIDENCE
        
        # 仅用于辅助，不独立提取预测
        return None


class ConfidenceAnalyzer:
    """置信度分析器"""
    
    @staticmethod
    def analyze_sentiment_strength(text: str) -> float:
        """
        分析情感强度
        
        Args:
            text: 文本
            
        Returns:
            置信度调整因子 (0.9-1.1)
        """
        strong_positive = ['强烈', '非常', '极其', '高度', 'strong', 'highly', 'extremely']
        weak_signals = ['可能', '也许', '或许', '谨慎', 'maybe', 'perhaps', 'cautious']
        
        text_lower = text.lower()
        
        if any(word in text_lower for word in strong_positive):
            return 1.1  # 提升10%
        elif any(word in text_lower for word in weak_signals):
            return 0.9  # 降低10%
        
        return 1.0  # 无调整
    
    @staticmethod
    def clamp_confidence(confidence: float) -> float:
        """
        限制置信度范围
        
        Args:
            confidence: 原始置信度
            
        Returns:
            限制在0.5-0.95之间的置信度
        """
        return max(0.50, min(0.95, confidence))


class PredictionExtractor:
    """
    预测提取器 - 策略模式链式调用
    
    使用多个策略按优先级提取预测和置信度
    """
    
    def __init__(self):
        """初始化策略链"""
        self.strategies = [
            RegexStrategy(),
            KeywordStrategy(),
            LengthBasedStrategy(),
        ]
        self.confidence_analyzer = ConfidenceAnalyzer()
    
    def extract(self, text: str) -> Tuple[Optional[str], Optional[float]]:
        """
        提取预测和置信度
        
        Args:
            text: LLM响应文本
            
        Returns:
            (预测, 置信度)，如果无法提取则返回(None, None)
        """
        if not text or len(text.strip()) < 10:
            return (None, None)
        
        prediction = None
        confidence = None
        
        # 按策略链尝试提取
        for strategy in self.strategies:
            result = strategy.extract(text)
            if result:
                pred, conf = result
                if prediction is None:
                    prediction = pred
                if confidence is None:
                    confidence = conf
                
                # 如果都提取到了，提前退出
                if prediction and confidence:
                    break
        
        # 如果没有提取到置信度，使用默认值
        if confidence is None and prediction:
            confidence = NEUTRAL_CONFIDENCE
        
        # 分析情感强度并调整置信度
        if confidence:
            adjustment_factor = self.confidence_analyzer.analyze_sentiment_strength(text)
            confidence = confidence * adjustment_factor
            confidence = self.confidence_analyzer.clamp_confidence(confidence)
        
        return (prediction, confidence)
    
    def extract_with_fallback(
        self,
        text: str,
        default_prediction: Optional[str] = None,
        default_confidence: Optional[float] = None
    ) -> Tuple[str, float]:
        """
        提取预测和置信度，带fallback
        
        Args:
            text: LLM响应文本
            default_prediction: 默认预测（如果无法提取）
            default_confidence: 默认置信度（如果无法提取）
            
        Returns:
            (预测, 置信度)
        """
        prediction, confidence = self.extract(text)
        
        if prediction is None:
            prediction = default_prediction or "HOLD"
        
        if confidence is None:
            confidence = default_confidence or WEAK_CONFIDENCE
        
        return (prediction, confidence)


# 便捷函数
_extractor = PredictionExtractor()


def extract_prediction(text: str) -> Tuple[Optional[str], Optional[float]]:
    """
    提取预测和置信度（便捷函数）
    
    Args:
        text: LLM响应文本
        
    Returns:
        (预测, 置信度)
    """
    return _extractor.extract(text)


def extract_prediction_with_fallback(
    text: str,
    default_prediction: str = "HOLD",
    default_confidence: float = WEAK_CONFIDENCE
) -> Tuple[str, float]:
    """
    提取预测和置信度，带fallback（便捷函数）
    
    Args:
        text: LLM响应文本
        default_prediction: 默认预测
        default_confidence: 默认置信度
        
    Returns:
        (预测, 置信度)
    """
    return _extractor.extract_with_fallback(text, default_prediction, default_confidence)
