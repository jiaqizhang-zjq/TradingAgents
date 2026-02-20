import time
import json
from tradingagents.dataflows.config import get_config


def create_aggressive_debator(llm):
    def aggressive_node(state) -> dict:
        risk_debate_state = state["risk_debate_state"]
        history = risk_debate_state.get("history", "")
        aggressive_history = risk_debate_state.get("aggressive_history", "")

        current_conservative_response = risk_debate_state.get("current_conservative_response", "")
        current_neutral_response = risk_debate_state.get("current_neutral_response", "")

        market_research_report = state["market_report"]
        sentiment_report = state["sentiment_report"]
        news_report = state["news_report"]
        fundamentals_report = state["fundamentals_report"]
        candlestick_report = state.get("candlestick_report", "")

        trader_decision = state["trader_investment_plan"]

        # 获取语言配置，默认为英文
        config = get_config()
        language = config.get("output_language", "en")

        if language == "zh":
            prompt = f"""你是一位拥有20多年经验的资深激进型风险分析师，曾在顶级对冲基金担任首席风险官，管理过数十亿美元的高风险投资组合。你的声誉建立在敢于在关键时刻承担计算过的风险，并因此获得超额回报。

作为激进型专家，你的角色是积极倡导高风险高回报的投资机会。在评估交易员的决策时，你必须：

1. 评估交易员的止损设置是否过于保守（可能错过大行情）
2. 分析目标价是否充分考虑了乐观情况下的上行空间
3. 计算在承担更高风险情况下的预期收益
4. 评估当前市场环境是否支持更激进的仓位
5. 提供具体的价格目标和时间框架

你的输出必须包含：
- 对交易员止损价的评估（是否应放宽以容忍更大波动）
- 激进情况下的目标价（基于乐观假设）
- 风险调整后的激进仓位建议
- 具体的风险因素和应对策略
- 预期收益和时间框架

以下是交易员的决策：

{trader_decision}

你的任务是通过质疑保守型和中立型的立场，证明在特定市场条件下承担更高风险是合理的。直接回应保守型和中立型分析师的每一点，用数据驱动的反驳进行反击。

市场研究报告：{market_research_report}
社交媒体情绪报告：{sentiment_report}
最新世界事务报告：{news_report}
公司基本面报告：{fundamentals_report}
K线分析报告：{candlestick_report}

对话历史：{history}
保守型分析师观点：{current_conservative_response}
中立型分析师观点：{current_neutral_response}

以对话方式输出，展现20年资深专家的专业水准。"""
        else:
            prompt = f"""As the Aggressive Risk Analyst, your role is to actively champion high-reward, high-risk opportunities, emphasizing bold strategies and competitive advantages. When evaluating the trader's decision or plan, focus intently on the potential upside, growth potential, and innovative benefits—even when these come with elevated risk. Use the provided market data and sentiment analysis to strengthen your arguments and challenge the opposing views. Specifically, respond directly to each point made by the conservative and neutral analysts, countering with data-driven rebuttals and persuasive reasoning. Highlight where their caution might miss critical opportunities or where their assumptions may be overly conservative. Here is the trader's decision:

{trader_decision}

Your task is to create a compelling case for the trader's decision by questioning and critiquing the conservative and neutral stances to demonstrate why your high-reward perspective offers the best path forward. Incorporate insights from the following sources into your arguments:

Market Research Report: {market_research_report}
Social Media Sentiment Report: {sentiment_report}
Latest World Affairs Report: {news_report}
Company Fundamentals Report: {fundamentals_report}
Candlestick Analysis Report: {candlestick_report}
Here is the current conversation history: {history} Here are the last arguments from the conservative analyst: {current_conservative_response} Here are the last arguments from the neutral analyst: {current_neutral_response}. If there are no responses from the other viewpoints, do not hallucinate and just present your point.

Engage actively by addressing any specific concerns raised, refuting the weaknesses in their logic, and asserting the benefits of risk-taking to outpace market norms. Maintain a focus on debating and persuading, not just presenting data. Challenge each counterpoint to underscore why a high-risk approach is optimal. Output conversationally as if you are speaking without any special formatting."""

        response = llm.invoke(prompt)

        argument = f"Aggressive Analyst: {response.content}"

        new_risk_debate_state = {
            "history": history + "\n" + argument,
            "aggressive_history": aggressive_history + "\n" + argument,
            "conservative_history": risk_debate_state.get("conservative_history", ""),
            "neutral_history": risk_debate_state.get("neutral_history", ""),
            "latest_speaker": "Aggressive",
            "current_aggressive_response": argument,
            "current_conservative_response": risk_debate_state.get("current_conservative_response", ""),
            "current_neutral_response": risk_debate_state.get(
                "current_neutral_response", ""
            ),
            "count": risk_debate_state["count"] + 1,
        }

        return {"risk_debate_state": new_risk_debate_state}

    return aggressive_node
