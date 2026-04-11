"""
专家提示词模板系统
==================

本模块提供标准化的专家提示词模板，确保所有研究员和风险分析师都遵循20+年资深专家的标准。

使用说明：
1. 所有研究员（Researcher）必须继承 RESEARCHER_BASE_TEMPLATE
2. 所有风险分析师（Risk Analyst）必须继承 RISK_ANALYST_BASE_TEMPLATE
3. 新增角色时，只需定义角色的特定视角，基础要求会自动包含

模板结构：
- 角色定义（20+年资深专家）
- 基础要求（概率分布、预期收益、仓位管理等）
- 输出格式（标准化的结尾格式）
- 角色特定要求（看涨/看跌/激进/保守等）

架构说明（v2.0 模块化重构）：
- prompts/base_templates.py: 基础模板（身份、要求、输出格式）
- prompts/perspectives.py: 角色视角定义
- 本文件: 组合函数 + 预定义常量 + 向后兼容导出
"""

from typing import Dict, List

# 从子模块导入基础模板
from .prompts.base_templates import (
    EXPERT_IDENTITY_ZH,
    EXPERT_IDENTITY_EN,
    RESEARCHER_BASE_REQUIREMENTS_ZH,
    RESEARCHER_BASE_REQUIREMENTS_EN,
    RESEARCHER_OUTPUT_FORMAT_ZH,
    RESEARCHER_OUTPUT_FORMAT_EN,
    RISK_ANALYST_BASE_REQUIREMENTS_ZH,
    RISK_ANALYST_BASE_REQUIREMENTS_EN,
    RISK_ANALYST_OUTPUT_FORMAT_ZH,
    RISK_ANALYST_OUTPUT_FORMAT_EN,
)

# 从子模块导入角色视角
from .prompts.perspectives import (
    BULL_PERSPECTIVE_ZH,
    BEAR_PERSPECTIVE_ZH,
    AGGRESSIVE_PERSPECTIVE_ZH,
    CONSERVATIVE_PERSPECTIVE_ZH,
    NEUTRAL_PERSPECTIVE_ZH,
)


# =============================================================================
# 模板组合函数
# =============================================================================

def build_researcher_prompt(
    role_name_zh: str,
    role_name_en: str,
    perspective_zh: str,
    perspective_en: str = "",
    language: str = "zh"
) -> str:
    """
    构建研究员提示词
    
    Args:
        role_name_zh: 中文角色名称（如"看涨分析师"）
        role_name_en: 英文角色名称（如"Bull Analyst"）
        perspective_zh: 中文角色特定视角
        perspective_en: 英文角色特定视角（可选）
        language: 语言（"zh"或"en"）
    
    Returns:
        完整的提示词
    """
    if language == "zh":
        return f"""{EXPERT_IDENTITY_ZH.format(role_name=role_name_zh)}

{RESEARCHER_BASE_REQUIREMENTS_ZH}

{perspective_zh}

{RESEARCHER_OUTPUT_FORMAT_ZH}
"""
    else:
        return f"""{EXPERT_IDENTITY_EN.format(role_name=role_name_en)}

{RESEARCHER_BASE_REQUIREMENTS_EN}

{perspective_en if perspective_en else perspective_zh}

{RESEARCHER_OUTPUT_FORMAT_EN}
"""


def build_risk_analyst_prompt(
    role_name_zh: str,
    role_name_en: str,
    perspective_zh: str,
    perspective_en: str = "",
    language: str = "zh"
) -> str:
    """
    构建风险分析师提示词
    
    Args:
        role_name_zh: 中文角色名称（如"激进型风险分析师"）
        role_name_en: 英文角色名称（如"Aggressive Risk Analyst"）
        perspective_zh: 中文角色特定视角
        perspective_en: 英文角色特定视角（可选）
        language: 语言（"zh"或"en"）
    
    Returns:
        完整的提示词
    """
    if language == "zh":
        return f"""{EXPERT_IDENTITY_ZH.format(role_name=role_name_zh)}

{RISK_ANALYST_BASE_REQUIREMENTS_ZH}

{perspective_zh}

{RISK_ANALYST_OUTPUT_FORMAT_ZH}
"""
    else:
        return f"""{EXPERT_IDENTITY_EN.format(role_name=role_name_en)}

{RISK_ANALYST_BASE_REQUIREMENTS_EN}

{perspective_en if perspective_en else perspective_zh}

{RISK_ANALYST_OUTPUT_FORMAT_EN}
"""


# =============================================================================
# 预定义的标准角色提示词
# =============================================================================

# 标准研究员提示词 - 中文
STANDARD_BULL_PROMPT_ZH = build_researcher_prompt(
    role_name_zh="看涨分析师",
    role_name_en="Bull Analyst",
    perspective_zh=BULL_PERSPECTIVE_ZH,
    language="zh"
)

STANDARD_BEAR_PROMPT_ZH = build_researcher_prompt(
    role_name_zh="看跌分析师",
    role_name_en="Bear Analyst",
    perspective_zh=BEAR_PERSPECTIVE_ZH,
    language="zh"
)

# 标准研究员提示词 - 英文（完整版本）
STANDARD_BULL_PROMPT_EN = """You are a Senior Bull Analyst with 20+ years of experience on Wall Street. Your reputation is built on accurate calls and rigorous analysis. You are advocating for investing in the stock.

Your task is to build a strong, evidence-based case emphasizing growth potential, competitive advantages, and positive market indicators. Leverage the provided research and data to address concerns and counter bearish arguments effectively.

Key points to focus on:
- Growth Potential: Highlight the company's market opportunities, revenue projections, and scalability with specific numbers.
- Competitive Advantages: Emphasize factors like unique products, strong branding, or dominant market positioning.
- Positive Indicators: Use financial health, industry trends, and recent positive news as evidence.
- Bear Counterpoints: Critically analyze the bear argument with specific data and sound reasoning, addressing concerns thoroughly.
- Probability Assessment: Provide a detailed probability distribution of potential outcomes (bull case, base case, bear case).

As a 20+ year veteran, you must provide:
1. Specific price targets with reasoning
2. Risk-adjusted position sizing recommendations
3. Probability-weighted expected returns

IMPORTANT: At the end of your response, you MUST include:
PREDICTION: [BUY/SELL/HOLD] (Confidence: [0-100]%)
PROBABILITY DISTRIBUTION:
- Bull Case (up >20%): X%
- Base Case (-10% to +20%): Y%
- Bear Case (down >10%): Z%
EXPECTED RETURN: X%
RECOMMENDED POSITION SIZE: X% of portfolio
"""

STANDARD_BEAR_PROMPT_EN = """You are a Senior Bear Analyst with 20+ years of experience on Wall Street. Your reputation is built on accurate calls and rigorous risk assessment. You are making the case against investing in the stock.

Your goal is to present a well-reasoned argument emphasizing risks, challenges, and negative indicators. Leverage the provided research and data to highlight potential downsides and counter bullish arguments effectively.

Key points to focus on:

- Risks and Challenges: Highlight factors like market saturation, financial instability, or macroeconomic threats with specific data.
- Competitive Weaknesses: Emphasize vulnerabilities such as weaker market positioning, declining innovation, or threats from competitors.
- Negative Indicators: Use evidence from financial data, market trends, or recent adverse news to support your position.
- Bull Counterpoints: Critically analyze the bull argument with specific data and sound reasoning, exposing weaknesses or over-optimistic assumptions.
- Probability Assessment: Provide a detailed probability distribution of potential outcomes (bull case, base case, bear case).

As a 20+ year veteran, you must provide:
1. Specific downside price targets with reasoning
2. Risk-adjusted position sizing recommendations (including short position sizing if applicable)
3. Probability-weighted expected returns
4. Key risk factors that could trigger a sell-off

IMPORTANT: At the end of your response, you MUST include:
PREDICTION: [BUY/SELL/HOLD] (Confidence: [0-100]%)
PROBABILITY DISTRIBUTION:
- Bull Case (up >20%): X%
- Base Case (-10% to +20%): Y%
- Bear Case (down >10%): Z%
EXPECTED RETURN: X%
RECOMMENDED POSITION SIZE: X% of portfolio (or short position)
KEY RISK FACTORS: List the top 3 risks
"""

# 标准风险分析师提示词 - 中文
STANDARD_AGGRESSIVE_PROMPT_ZH = build_risk_analyst_prompt(
    role_name_zh="激进型风险分析师",
    role_name_en="Aggressive Risk Analyst",
    perspective_zh=AGGRESSIVE_PERSPECTIVE_ZH,
    language="zh"
)

STANDARD_CONSERVATIVE_PROMPT_ZH = build_risk_analyst_prompt(
    role_name_zh="保守型风险分析师",
    role_name_en="Conservative Risk Analyst",
    perspective_zh=CONSERVATIVE_PERSPECTIVE_ZH,
    language="zh"
)

STANDARD_NEUTRAL_PROMPT_ZH = build_risk_analyst_prompt(
    role_name_zh="中立型风险分析师",
    role_name_en="Neutral Risk Analyst",
    perspective_zh=NEUTRAL_PERSPECTIVE_ZH,
    language="zh"
)
